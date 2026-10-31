# StoryForge 📖✨

**AI Story Bible and Co-Writer with branching narratives and a consistency checker**

StoryForge is an AI-powered storytelling platform that pairs an interactive Co-Writer with a living Story Bible. Create rich, consistent stories with branching narrative trees, character psychology tracking, and automatic lore consistency checking powered by Google Gemini and ChromaDB.

## Features

- **Story Bible**: Define characters with deep psychology profiles and speech styles, plus canon lore entries categorized by domain.
- **AI Co-Writer & Branching Scenes**: Generate next scenes with choice options while honoring character personality, speech dialect, and established lore.
- **Consistency Checker**: Automatically analyzes each newly drafted scene against canon facts and character profiles to flag discrepancies or plot holes before canonization.
- **RAG Memory (ChromaDB)**: Vector retrieval pulls only contextually relevant lore and character profiles for every scene generation.
- **Interactive Tree View**: Full interactive graph visualization of your story's branching scene hierarchy powered by vis-network.
- **Resilient AI Pipeline**: Dynamic model selection (`GEMINI_MODEL`, fallback `GEMINI_FALLBACK_MODEL`), automatic retries with exponential backoff on rate limits, and graceful error handling.

## Tech Stack

- **Backend**: Python 3, Django 5, Django REST Framework (DRF)
- **Database**: SQLite
- **AI & LLM**: Google Gemini API via `google-genai` SDK (`gemini-3.5-flash`, fallback `gemini-3.1-flash-lite`)
- **Vector Store & RAG**: ChromaDB
- **Frontend**: Django Templates, Vanilla JavaScript, CSS variables (dark theme), vis-network

## Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and add your own Gemini key:

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY
```

### 3. Run database migrations

```bash
python manage.py migrate
```

### 4. Seed demo story

```bash
python manage.py seed_demo
```

This seeds a fantasy demo story ("The Lost Kingdom") with characters and lore entries indexed into ChromaDB.

### 5. Start the development server

```bash
python manage.py runserver
```

### 6. Explore StoryForge

- **Story Setup & Bible**: [http://localhost:8000/](http://localhost:8000/)
- **Co-Writer & Scene Generator**: [http://localhost:8000/writer/1/](http://localhost:8000/writer/1/)
- **Branching Scene Tree**: [http://localhost:8000/tree/1/](http://localhost:8000/tree/1/)
- **Django Admin**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` / `POST` | `/api/stories/` | List or create stories |
| `GET` / `PUT` / `DELETE` | `/api/stories/<id>/` | Retrieve, update, or delete story |
| `GET` | `/api/stories/<id>/tree/` | Retrieve scene nodes and edges for tree graph |
| `GET` / `POST` | `/api/characters/` | List or create characters (`?story_id=` filter) |
| `GET` / `POST` | `/api/lore-entries/` | List or create lore entries (`?story_id=` filter) |
| `POST` | `/api/scenes/generate/` | Generate next scene, verify consistency, and branch tree |

## License

MIT
