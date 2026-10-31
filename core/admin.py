from django.contrib import admin
from .models import Story, Character, LoreEntry, Scene


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'created_at')
    search_fields = ('title', 'genre')


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'story', 'speech_style')
    list_filter = ('story',)
    search_fields = ('name',)


@admin.register(LoreEntry)
class LoreEntryAdmin(admin.ModelAdmin):
    list_display = ('category', 'story', 'fact')
    list_filter = ('story', 'category')
    search_fields = ('fact',)


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('choice_label', 'story', 'parent', 'created_at')
    list_filter = ('story',)
    search_fields = ('text', 'choice_label')
