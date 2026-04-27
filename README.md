![Banner](./marketing.png)

# 🚀 Multi-Agent Marketing Crew

A small AI application that generates complete marketing campaigns from a single topic. Four AI agents work together to produce strategy, content, social posts, and a timeline.

Built with **CrewAI** for agent orchestration and **OpenAI** as the LLM.

---

## What it does

Given a topic like _"Launch a new eco-friendly product line"_, the app runs it through a pipeline of four agents:

1. **Marketing Strategist** — figures out the audience, positioning, and channels
2. **Content Creator** — drafts blog outlines and key messaging
3. **Social Media Specialist** — writes posts for Instagram, Twitter, and LinkedIn
4. **Campaign Manager** — puts together a timeline and KPIs

Each agent's output flows into the next, so the final result holds together as one coherent campaign.

---

## Tech stack

- **Python 3.10+**
- **CrewAI** — multi-agent orchestration
- **OpenAI** — LLM
- **FastAPI** — backend API
- **Streamlit** — frontend dashboard
- **SQLite + SQLAlchemy** — persistent task storage
- **Pydantic** — type-safe models
- **uv** — package management

---

## Project structure

```
multi-agent-marketing-crew/
├── src/
│   ├── shared/
│   │   ├── config.py              # env vars + settings
│   │   ├── models.py              # pydantic models
│   │   └── database.py            # db setup
│   │
│   ├── backend/
│   │   ├── main.py                # fastapi endpoints
│   │   ├── db_models.py           # sqlalchemy models
│   │   └── services/
│   │       ├── marketing_crew.py  # crewai agents
│   │       └── task_service.py    # task management
│   │
│   └── frontend/
│       └── streamlit_app.py       # streamlit ui
│
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Getting started

Requires Python 3.10+ and an OpenAI API key.

**1. Install uv** (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Clone and install:**

```bash
git clone <repository-url>
cd multi-agent-marketing-crew
uv sync
```

**3. Add a `.env` file** in the project root:

```bash
OPENAI_API_KEY=sk-your-key-here

# optional
APP_LANGUAGE=en
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
DATABASE_URL=sqlite+aiosqlite:///./marketing_team.db
```

**4. Start the backend** (keep this terminal running):

```bash
uv run uvicorn src.backend.main:app --reload --host 127.0.0.1 --port 8000
```

**5. Start the frontend** (in a new terminal):

```bash
uv run streamlit run src/frontend/streamlit_app.py
```

Open `http://localhost:8501` to use the app.

---

## API

The API is fully usable on its own. Swagger docs available at `http://127.0.0.1:8000/docs`.

| Method | Endpoint           | Description         |
| ------ | ------------------ | ------------------- |
| `POST` | `/tasks`           | Create a new task   |
| `GET`  | `/tasks`           | List all tasks      |
| `GET`  | `/tasks/{task_id}` | Get a specific task |
| `GET`  | `/health`          | Health check        |

**Example:**

```bash
curl -X POST "http://127.0.0.1:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Launch a new eco-friendly product line", "language": "en"}'
```

---

## Example prompts

- _"Launch a new eco-friendly product line"_
- _"Rebrand our company with a modern, tech-forward image"_
- _"Promote our annual tech conference"_
- _"Holiday marketing campaign for an e-commerce store"_
- _"Strategy for entering the European market"_

Each campaign takes around 2–5 minutes since the agents run sequentially.

---

## Output

Each completed task includes:

- A full marketing strategy (audience, positioning, channels)
- A content plan with blog outlines and themes
- Social media posts for Instagram, Twitter, and LinkedIn
- Campaign ideas
- A timeline with milestones and KPIs

All results are persisted to SQLite and accessible through the dashboard or API.

---
