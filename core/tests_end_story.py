import json
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from core.models import Story, Character, LoreEntry, Scene


class EndStoryFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.story = Story.objects.create(
            title="Chronicles of the Obsidian Veil",
            genre="Dark Fantasy",
            dialect_rules="Archaic Victorian prose, no contractions.",
            is_completed=False,
        )
        self.character = Character.objects.create(
            story=self.story,
            name="Lady Seraphina",
            psychology="Guarded, deeply cynical of high court politics.",
            speech_style="Whispered, poetic, uses avian metaphors.",
        )
        self.lore = LoreEntry.objects.create(
            story=self.story,
            category="Artifacts",
            fact="The Obsidian Veil absorbs memory crystals and glows crimson near betrayed royalty.",
        )
        self.scene1 = Scene.objects.create(
            story=self.story,
            parent=None,
            choice_label="Beginning of Story",
            text="The carriage rattled upon cobblestone slick with autumn rain as Lady Seraphina entered the castle gates.",
        )
        self.scene2 = Scene.objects.create(
            story=self.story,
            parent=self.scene1,
            choice_label="Confront the Regent in the Throne Room",
            text="She pushed open the heavy oak doors, her gloved fingers resting upon the veiled pendant.",
        )

    def test_writer_template_contains_all_end_story_ui_elements(self):
        """Verify the writer template has the Finish Story button, confirmation, The End card, and action buttons."""
        response = self.client.get(reverse('writer', kwargs={'story_id': self.story.id}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # 1. Finish Story / The End button
        self.assertIn('btn-finish-story', content)
        self.assertIn('Finish Story / The End', content)

        # 2. Confirmation dialog prompt
        self.assertIn("Are you sure you want to end this story? You won't be able to add more scenes.", content)

        # 3. The End card & elements
        self.assertIn('completed-card', content)
        self.assertIn('The End', content)
        self.assertIn('btn-read-full-story', content)
        self.assertIn('btn-download-story', content)
        self.assertIn('btn-reopen-story', content)
        self.assertIn('full-story-modal', content)

    @patch('core.services.ai.generate_epilogue')
    def test_complete_story_endpoint_marks_completed_and_adds_epilogue(self, mock_epilogue):
        """Verify POST /writer/<id>/complete/ sets is_completed=True and saves epilogue scene."""
        mock_epilogue.return_value = {
            "text": "The obsidian veil dissolved into morning mist. The realm was forever changed.",
            "choices": []
        }

        url = reverse('complete-story', kwargs={'story_id': self.story.id})
        response = self.client.post(url, data=json.dumps({
            'parent_id': self.scene2.id,
            'generate_epilogue': True
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['is_completed'])
        self.assertEqual(data['status'], 'completed')
        self.assertIsNotNone(data['epilogue_scene'])
        self.assertEqual(data['epilogue_scene']['choice_label'], 'The End (Epilogue)')

        self.story.refresh_from_db()
        self.assertTrue(self.story.is_completed)

        # Verify Scene count increased by 1 (the epilogue scene)
        self.assertEqual(self.story.scenes.count(), 3)
        last_scene = self.story.scenes.last()
        self.assertEqual(last_scene.choice_label, 'The End (Epilogue)')
        self.assertEqual(last_scene.text, "The obsidian veil dissolved into morning mist. The realm was forever changed.")

    def test_cannot_generate_scene_when_story_is_completed(self):
        """Verify POST /api/scenes/generate/ is blocked when story is completed."""
        self.story.is_completed = True
        self.story.save()

        response = self.client.post('/api/scenes/generate/', data=json.dumps({
            'story_id': self.story.id,
            'parent_id': self.scene2.id,
            'choice_label': 'Strike a bargain'
        }), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('This story is completed. Reopen the story to generate new scenes.', data['error'])

    def test_download_full_story_as_txt(self):
        """Verify GET /writer/<id>/download/ returns full text manuscript with headers, scenes, and The End."""
        self.story.is_completed = True
        self.story.save()

        url = reverse('download-story', kwargs={'story_id': self.story.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn('attachment;', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        self.assertIn(self.story.title, content)
        self.assertIn(self.story.genre, content)
        self.assertIn("Lady Seraphina", content)
        self.assertIn("The Obsidian Veil", content)
        self.assertIn(self.scene1.text, content)
        self.assertIn(self.scene2.text, content)
        self.assertIn("THE END", content)

    def test_reopen_story_allows_adding_scenes_again(self):
        """Verify POST /writer/<id>/reopen/ unmarks completed and permits scene generation again."""
        self.story.is_completed = True
        self.story.save()

        url = reverse('reopen-story', kwargs={'story_id': self.story.id})
        response = self.client.post(url, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['is_completed'])
        self.assertEqual(data['status'], 'reopened')

        self.story.refresh_from_db()
        self.assertFalse(self.story.is_completed)

        # Now test that scene generation is allowed (mocking AI calls)
        with patch('core.services.ai.generate_scene') as mock_gen, \
             patch('core.services.ai.check_consistency') as mock_check:
            mock_gen.return_value = {
                'text': 'A secret passageway opened behind the throne.',
                'choices': ['Enter the dark tunnel', 'Seal the passageway']
            }
            mock_check.return_value = {'consistent': True, 'issues': []}

            gen_response = self.client.post('/api/scenes/generate/', data=json.dumps({
                'story_id': self.story.id,
                'parent_id': self.scene2.id,
                'choice_label': 'Search for hidden doors'
            }), content_type='application/json')

            self.assertEqual(gen_response.status_code, 201)
            self.assertEqual(self.story.scenes.count(), 3)
