import logging
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Story, Character, LoreEntry, Scene
from .serializers import (
    StorySerializer,
    CharacterSerializer,
    LoreEntrySerializer,
    SceneSerializer,
    SceneGenerateRequestSerializer,
)
from .services import memory, ai

logger = logging.getLogger(__name__)


class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer

    @action(detail=True, methods=['get'], url_path='tree')
    def tree(self, request, pk=None):
        story = self.get_object()
        scenes = story.scenes.all()
        nodes = [
            {
                "id": scene.id,
                "label": scene.choice_label or "Start",
                "choice_label": scene.choice_label or "Start",
                "text": scene.text,
            }
            for scene in scenes
        ]
        edges = [
            {
                "from": scene.parent_id,
                "to": scene.id,
            }
            for scene in scenes
            if scene.parent_id is not None
        ]
        return Response({"nodes": nodes, "edges": edges, "is_completed": story.is_completed})


class CharacterViewSet(viewsets.ModelViewSet):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer

    def get_queryset(self):
        queryset = Character.objects.all()
        story_id = self.request.query_params.get('story_id')
        if story_id is not None:
            queryset = queryset.filter(story_id=story_id)
        return queryset

    def perform_create(self, serializer):
        character = serializer.save()
        memory.add_character(
            story_id=character.story_id,
            name=character.name,
            psychology=character.psychology,
            speech_style=character.speech_style,
            character_id=character.id,
        )


class LoreEntryViewSet(viewsets.ModelViewSet):
    queryset = LoreEntry.objects.all()
    serializer_class = LoreEntrySerializer

    def get_queryset(self):
        queryset = LoreEntry.objects.all()
        story_id = self.request.query_params.get('story_id')
        if story_id is not None:
            queryset = queryset.filter(story_id=story_id)
        return queryset

    def perform_create(self, serializer):
        lore = serializer.save()
        memory.add_lore(
            story_id=lore.story_id,
            text=lore.fact,
            lore_id=lore.id,
        )


class SceneGenerateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SceneGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        story_id = serializer.validated_data['story_id']
        parent_id = serializer.validated_data.get('parent_id')
        choice_label = serializer.validated_data.get('choice_label', '')

        story = get_object_or_404(Story, pk=story_id)
        if story.is_completed:
            return Response(
                {"error": "This story is completed. Reopen the story to generate new scenes."},
                status=status.HTTP_400_BAD_REQUEST
            )
        parent_scene = None
        if parent_id:
            parent_scene = get_object_or_404(Scene, pk=parent_id, story=story)

        result = ai.generate_scene(story, parent_scene, choice_label)
        if isinstance(result, dict) and "error" in result:
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        scene_text = result.get('text', '')
        choices = result.get('choices', [])

        consistency_result = ai.check_consistency(story, scene_text)

        scene = Scene.objects.create(
            story=story,
            parent=parent_scene,
            choice_label=choice_label,
            text=scene_text,
        )

        return Response({
            'scene': SceneSerializer(scene).data,
            'choices': choices,
            'consistency': consistency_result,
            'consistency_issues': consistency_result.get('issues', []) if isinstance(consistency_result, dict) else consistency_result,
        }, status=status.HTTP_201_CREATED)


# Template views
def story_setup_view(request):
    return render(request, 'story_setup.html')


def writer_view(request, story_id):
    story = get_object_or_404(Story, pk=story_id)
    return render(request, 'writer.html', {'story': story})


def tree_view(request, story_id):
    story = get_object_or_404(Story, pk=story_id)
    return render(request, 'tree_view.html', {'story': story})


@api_view(['POST'])
def complete_story_view(request, story_id):
    """
    Marks a story as completed and optionally generates a short 2-3 sentence
    epilogue scene closing the narrative based on the story bible.
    """
    story = get_object_or_404(Story, pk=story_id)
    story.is_completed = True
    story.save(update_fields=['is_completed'])

    # Check parent scene and epilogue generation preference
    parent_id = request.data.get('parent_id') if isinstance(request.data, dict) else None
    parent_scene = None
    if parent_id:
        parent_scene = Scene.objects.filter(pk=parent_id, story=story).first()
    if not parent_scene:
        parent_scene = story.scenes.order_by('-created_at').first()

    generate_epilogue_flag = True
    if isinstance(request.data, dict) and 'generate_epilogue' in request.data:
        generate_epilogue_flag = bool(request.data.get('generate_epilogue'))

    epilogue_scene = None
    if generate_epilogue_flag and parent_scene:
        try:
            epilogue_result = ai.generate_epilogue(story, parent_scene)
            if isinstance(epilogue_result, dict) and epilogue_result.get('text') and 'error' not in epilogue_result:
                epilogue_scene = Scene.objects.create(
                    story=story,
                    parent=parent_scene,
                    choice_label="The End (Epilogue)",
                    text=epilogue_result['text'].strip(),
                )
        except Exception as e:
            logger.warning("Could not generate closing epilogue scene: %s", e)

    return Response({
        "status": "completed",
        "is_completed": True,
        "story_id": story.id,
        "epilogue_scene": SceneSerializer(epilogue_scene).data if epilogue_scene else None,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def reopen_story_view(request, story_id):
    """
    Reopens a completed story so new scenes and branches can be added.
    """
    story = get_object_or_404(Story, pk=story_id)
    story.is_completed = False
    story.save(update_fields=['is_completed'])
    return Response({
        "status": "reopened",
        "is_completed": False,
        "story_id": story.id,
    }, status=status.HTTP_200_OK)


def download_story_view(request, story_id):
    """
    Downloads all scenes in the story in sequential order as a formatted .txt manuscript.
    """
    story = get_object_or_404(Story, pk=story_id)
    scenes = story.scenes.all().order_by('created_at')

    lines = [
        "=" * 60,
        f"STORY TITLE: {story.title}",
        f"GENRE: {story.genre}",
    ]
    if story.dialect_rules:
        lines.append(f"DIALECT & RULES: {story.dialect_rules}")
    lines.append("=" * 60)
    lines.append("")

    # Cast list
    characters = story.characters.all()
    if characters.exists():
        lines.append("--- DRAMATIS PERSONAE ---")
        for c in characters:
            lines.append(f"* {c.name}")
            if c.psychology:
                lines.append(f"  Psychology: {c.psychology}")
            if c.speech_style:
                lines.append(f"  Speech Style: {c.speech_style}")
        lines.append("")

    # Lore
    lore_entries = story.lore_entries.all()
    if lore_entries.exists():
        lines.append("--- WORLD CANON & LORE ---")
        for lore in lore_entries:
            lines.append(f"* [{lore.category}] {lore.fact}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("CHRONICLE SCENES")
    lines.append("=" * 60)
    lines.append("")

    if not scenes.exists():
        lines.append("(No scenes recorded yet.)")
    else:
        for idx, scene in enumerate(scenes, start=1):
            label = scene.choice_label or ("Beginning of Story" if idx == 1 else f"Scene {idx}")
            lines.append(f"=== SCENE {idx}: {label} ===")
            lines.append("")
            lines.append(scene.text.strip())
            lines.append("")
            lines.append("-" * 40)
            lines.append("")

    if story.is_completed:
        lines.append("=" * 60)
        lines.append("                 THE END                  ")
        lines.append("=" * 60)

    content = "\n".join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    safe_title = "".join(c for c in story.title if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    filename = f"{safe_title or 'StoryForge'}_Full_Story.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
