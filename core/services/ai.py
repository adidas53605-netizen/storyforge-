import json
import logging
import os
import time
from django.conf import settings
from dotenv import load_dotenv
from pydantic import BaseModel
from .memory import retrieve_relevant

load_dotenv()

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class SceneOutput(BaseModel):
    text: str
    choices: list[str]


class ConsistencyOutput(BaseModel):
    consistent: bool
    issues: list[str]


def _get_client():
    api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '')
    return genai.Client(api_key=api_key)


def _get_models():
    main_model = os.getenv('GEMINI_MODEL') or getattr(settings, 'GEMINI_MODEL', '') or 'gemini-3.5-flash'
    fallback_model = os.getenv('GEMINI_FALLBACK_MODEL') or getattr(settings, 'GEMINI_FALLBACK_MODEL', '') or 'gemini-3.1-flash-lite'
    return main_model, fallback_model


def _is_retryable_error(e: Exception) -> bool:
    """Checks whether an exception corresponds to HTTP 503 or 429."""
    for attr in ('code', 'status_code', 'http_status'):
        val = getattr(e, attr, None)
        if val in (429, 503, '429', '503'):
            return True

    response = getattr(e, 'response', None)
    if response is not None:
        val = getattr(response, 'status_code', None)
        if val in (429, 503, '429', '503'):
            return True

    err_str = str(e)
    if any(code in err_str for code in ('429', '503', 'RESOURCE_EXHAUSTED', 'UNAVAILABLE', 'Too Many Requests', 'Service Unavailable')):
        return True

    return False


def _try_model_with_retries(client, model: str, contents, config: types.GenerateContentConfig):
    """
    Tries the given model with up to 3 attempts, waiting 2s, 4s, 8s on 503/429.
    Returns response if successful.
    Raises exception if all attempts fail or a non-retryable error occurs.
    """
    delays = [2, 4, 8]
    last_exc = None
    for attempt, delay in enumerate(delays):
        try:
            logger.info("Calling Gemini model '%s' (attempt %d/%d)", model, attempt + 1, len(delays))
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as e:
            last_exc = e
            if _is_retryable_error(e):
                logger.warning(
                    "Model '%s' failed with retryable error (attempt %d/%d): %s. Waiting %ds...",
                    model, attempt + 1, len(delays), e, delay
                )
                time.sleep(delay)
            else:
                logger.warning("Model '%s' failed with non-retryable error: %s", model, e)
                break
    raise last_exc


def _execute_gemini_call(contents, response_schema=None):
    """
    Executes a Gemini call:
    1. Try main model (GEMINI_MODEL) with up to 3 attempts (waiting 2s, 4s, 8s on 503/429).
    2. If it still fails, try fallback model (GEMINI_FALLBACK_MODEL) the same way.
    3. If both fail, return friendly JSON error: {"error": "AI is busy, please try again"}.
    """
    main_model, fallback_model = _get_models()
    try:
        client = _get_client()
    except Exception as e:
        logger.error("Failed to initialize Gemini client: %s", e)
        return {"error": "AI is busy, please try again"}

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
    )

    models_to_try = [main_model]
    if fallback_model and fallback_model != main_model:
        models_to_try.append(fallback_model)

    response = None
    for model in models_to_try:
        try:
            response = _try_model_with_retries(client, model, contents, config)
            if response:
                break
        except Exception as e:
            logger.error("Failed to generate content with model '%s': %s", model, e)
            continue

    if not response or not getattr(response, 'text', None):
        return {"error": "AI is busy, please try again"}

    response_text = response.text.strip()
    try:
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])
        return json.loads(response_text)
    except Exception as e:
        logger.error("JSON decode error from Gemini response: %s", e)
        return {"error": "AI is busy, please try again"}


def generate_scene(story, parent_scene, choice_label):
    """Generate a new scene using Google Gemini, pulling relevant lore and character context."""
    context_query = choice_label or story.title
    relevant_docs = retrieve_relevant(story.id, context_query, k=5)

    # Build character context
    characters = story.characters.all()
    char_descriptions = []
    for c in characters:
        char_descriptions.append(
            f"- {c.name}: Psychology: {c.psychology}. Speech style: {c.speech_style}."
        )

    parent_text = ""
    if parent_scene:
        parent_text = f"\n\nPrevious scene:\n{parent_scene.text}"

    prompt = f"""You are a creative fiction writer. Write the next scene for this story.

Story: {story.title}
Genre: {story.genre}
Dialect rules: {story.dialect_rules or 'None specified'}

Characters:
{chr(10).join(char_descriptions) if char_descriptions else 'No characters defined yet.'}

Relevant lore and context:
{chr(10).join(f'- {doc}' for doc in relevant_docs) if relevant_docs else 'No lore entries yet.'}
{parent_text}

The player chose: "{choice_label or 'Begin the story'}"

Write the next scene (2-4 paragraphs). Then provide 2-3 choices for what happens next.

Respond ONLY with valid JSON in this exact format:
{{
  "text": "The scene narrative text here...",
  "choices": ["Choice 1", "Choice 2", "Choice 3"]
}}"""

    return _execute_gemini_call(contents=prompt, response_schema=SceneOutput)


def check_consistency(story, new_scene_text):
    """Check new scene text for consistency issues against story lore and characters."""
    relevant_docs = retrieve_relevant(story.id, new_scene_text, k=5)

    characters = story.characters.all()
    char_descriptions = []
    for c in characters:
        char_descriptions.append(
            f"- {c.name}: Psychology: {c.psychology}. Speech style: {c.speech_style}."
        )

    prompt = f"""You are a story consistency checker. Analyze the new scene text for any inconsistencies with the established story bible.

Story: {story.title}
Genre: {story.genre}
Dialect rules: {story.dialect_rules or 'None specified'}

Established characters:
{chr(10).join(char_descriptions) if char_descriptions else 'No characters defined.'}

Established lore/context:
{chr(10).join(f'- {doc}' for doc in relevant_docs) if relevant_docs else 'No lore entries.'}

New scene text:
{new_scene_text}

Check for:
1. Character behavior inconsistencies
2. Lore contradictions
3. Dialect/speech style violations
4. Plot holes

Respond ONLY with valid JSON:
{{
  "consistent": true/false,
  "issues": ["issue 1", "issue 2"]
}}

If everything is consistent, return {{"consistent": true, "issues": []}}"""

    return _execute_gemini_call(contents=prompt, response_schema=ConsistencyOutput)
