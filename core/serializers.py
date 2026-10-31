from rest_framework import serializers
from .models import Story, Character, LoreEntry, Scene


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = '__all__'


class LoreEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoreEntry
        fields = '__all__'


class SceneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scene
        fields = '__all__'


class StorySerializer(serializers.ModelSerializer):
    characters = CharacterSerializer(many=True, read_only=True)
    lore_entries = LoreEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = '__all__'


class SceneGenerateRequestSerializer(serializers.Serializer):
    story_id = serializers.IntegerField()
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    choice_label = serializers.CharField(max_length=255, required=False, default='')
