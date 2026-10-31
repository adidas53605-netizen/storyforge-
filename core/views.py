from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render, get_object_or_404
from .models import Story, Character, LoreEntry, Scene
from .serializers import (
    StorySerializer,
    CharacterSerializer,
    LoreEntrySerializer,
    SceneSerializer,
    SceneGenerateRequestSerializer,
)
from .services import memory, ai


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
        return Response({"nodes": nodes, "edges": edges})


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
