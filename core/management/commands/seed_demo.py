from django.core.management.base import BaseCommand
from core.models import Story, Character, LoreEntry
from core.services import memory


class Command(BaseCommand):
    help = 'Seeds demo data for StoryForge (story, characters, lore entries) and indexes them in ChromaDB.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo story data...")

        story, created = Story.objects.get_or_create(
            title='The Lost Kingdom',
            defaults={
                'genre': 'Fantasy',
                'dialect_rules': 'Characters speak in a medieval English style. Avoid modern slang.',
            }
        )
        if not created:
            story.genre = 'Fantasy'
            story.dialect_rules = 'Characters speak in a medieval English style. Avoid modern slang.'
            story.save()
            self.stdout.write(f"Updated existing demo story: {story.title} (ID: {story.id})")
        else:
            self.stdout.write(self.style.SUCCESS(f"Created demo story: {story.title} (ID: {story.id})"))

        # Create Characters
        characters_data = [
            {
                'name': 'Alaric the Bold',
                'psychology': 'Brave but impulsive. Driven by a need to prove himself. Fears being seen as weak.',
                'speech_style': 'Speaks in short, decisive sentences. Uses military metaphors.',
            },
            {
                'name': 'Sera the Wise',
                'psychology': 'Cautious and analytical. Values knowledge above all. Secretly lonely.',
                'speech_style': 'Speaks in longer, flowing sentences. Often quotes ancient proverbs.',
            },
        ]

        for char_info in characters_data:
            character, c_created = Character.objects.get_or_create(
                story=story,
                name=char_info['name'],
                defaults={
                    'psychology': char_info['psychology'],
                    'speech_style': char_info['speech_style'],
                }
            )
            if not c_created:
                character.psychology = char_info['psychology']
                character.speech_style = char_info['speech_style']
                character.save()

            memory.add_character(
                story_id=story.id,
                name=character.name,
                psychology=character.psychology,
                speech_style=character.speech_style,
                character_id=character.id,
            )
            action_desc = "Created and indexed" if c_created else "Updated and indexed"
            self.stdout.write(self.style.SUCCESS(f"{action_desc} character: {character.name} (ID: {character.id})"))

        # Create LoreEntries
        lore_entries_data = [
            {
                'category': 'History',
                'fact': 'The Lost Kingdom of Aethermoor fell 500 years ago when its king used forbidden shadow magic.',
            },
            {
                'category': 'Geography',
                'fact': 'The Whispering Forest surrounds the ruins of Aethermoor. Travelers report hearing voices of the dead.',
            },
            {
                'category': 'Magic',
                'fact': 'Shadow magic corrupts the user slowly. Early signs include silver-streaked eyes and cold skin.',
            },
        ]

        for lore_info in lore_entries_data:
            lore, l_created = LoreEntry.objects.get_or_create(
                story=story,
                category=lore_info['category'],
                fact=lore_info['fact'],
            )
            memory.add_lore(
                story_id=story.id,
                text=lore.fact,
                lore_id=lore.id,
            )
            action_desc = "Created and indexed" if l_created else "Indexed existing"
            self.stdout.write(self.style.SUCCESS(f"{action_desc} lore entry: [{lore.category}] {lore.fact[:40]}... (ID: {lore.id})"))

        self.stdout.write(self.style.SUCCESS("Demo seeding completed successfully!"))
