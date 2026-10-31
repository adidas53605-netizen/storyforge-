from django.db import models


class Story(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    dialect_rules = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'stories'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Character(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=255)
    psychology = models.TextField(blank=True, default='')
    speech_style = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.name} ({self.story.title})"


class LoreEntry(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='lore_entries')
    category = models.CharField(max_length=100)
    fact = models.TextField()

    class Meta:
        verbose_name_plural = 'lore entries'

    def __str__(self):
        return f"{self.category}: {self.fact[:50]}"


class Scene(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='scenes')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    choice_label = models.CharField(max_length=255, blank=True, default='')
    text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        label = self.choice_label or 'Root'
        return f"Scene: {label} ({self.story.title})"
