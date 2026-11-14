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

## License---
 
## Problem Statement

Creative writers often face difficulties when developing long-form stories and interactive narratives. Managing characters, locations, timelines, relationships, and multiple story branches manually can become complicated.

Key Challenges

- Maintaining consistency across long stories.
- Managing characters, locations, and story timelines.
- Creating and organizing multiple story branches.
- Maintaining context when using AI writing tools.
- Spending too much time managing story details.

StoryForge aims to address these challenges through AI-powered story development and centralized narrative management.

---

## Proposed Solution

StoryForge provides an AI-powered environment that helps writers create, organize, and manage complex narratives.

The platform aims to:

- Assist with AI-powered story generation.
- Organize story information through a centralized Story Bible.
- Support branching narratives and alternative story paths.
- Help identify potential inconsistencies in story details.
- Simplify the overall creative writing workflow.

---

## System Architecture

StoryForge follows a backend-driven architecture connecting the frontend, Django backend, AI services, and data storage components.

Architecture Diagram

flowchart TD
    A[User / Writer] --> B[Frontend Interface]
    B --> C[Django Backend]
    C --> D[Application Logic]

    D --> E[Gemini AI API]
    D --> F[ChromaDB]
    D --> G[Application Database]

    E --> H[AI Generated Content]
    F --> I[Retrieved Story Context]
    G --> J[Stored Story Data]

    H --> K[Story Processing]
    I --> K
    J --> K

    K --> L[Final Output to User]

---

## Project Workflow

1. User accesses the StoryForge platform.
2. User creates or selects a story.
3. User provides story ideas or prompts.
4. Django backend processes the request.
5. AI services assist with content generation.
6. Story information is managed through the Story Bible.
7. Branching scenes help develop alternative narratives.
8. The consistency checker helps identify potential inconsistencies.
9. The final output is presented to the user.

---

## Installation and Setup

Prerequisites

- Python 3.x
- pip
- Git
- Required API credentials

Clone Repository

git clone https://github.com/adidas53605-netizen/storyforge-.git
cd storyforge-

Create Virtual Environment

python -m venv venv

Activate on Windows:

venv\Scripts\activate

Install Dependencies

pip install -r requirements.txt

Environment Configuration

Configure the required environment variables in a ".env" file.

Example:

GEMINI_API_KEY=your_api_key_here

Database Migration

python manage.py migrate

Run Development Server

python manage.py runserver

Open:

http://127.0.0.1:8000/

---

## Project Screenshots

Homepage

[Add Homepage Screenshot]



Story Editor

[Add Story Editor Screenshot]

AI Story Generation

[Add AI Generation Screenshot]

Consistency Checker

[Add Consistency Checker Screenshot]

---

## Live Demo

Live Project

[https://storyforge-yd1r.onrender.com]

Demo Video

"Watch StoryForge Demo" (https://youtu.be/N_LeGO6zd0E?si=Sh6UAwpuhMbEbGVt)

---

## Future Scope

- Advanced AI-powered narrative assistance.
- Improved story consistency analysis.
- Enhanced branching story structures.
- Advanced character and world-building tools.
- Collaborative story development.
- Improved performance and user experience.

---

## Team Members

Team Name: Clash Coders

Team Leader: Aditya Das

| Team Member | Role |
| --- | --- |
| Aditya Das | Team Leader & Backend / AI API Integration |
| Aditya Naskar | Frontend / UI Design |
| Sheikh Meheraj Uddin | Story Bible & Prompt Design |
| Deeptadeep Dey | Testing, Deployment & Demo |

---

## Conclusion

StoryForge aims to simplify creative writing by combining artificial intelligence with structured narrative management.

By bringing story generation, story organization, branching narratives, and consistency support together, StoryForge provides a unified environment for developing complex stories.

StoryForge — Where Ideas Become Stories.

MIT
