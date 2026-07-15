# AI Support Ticket Resolution API

An AI-powered customer support ticket resolution system. Tickets are classified, routed to a
category-specific handler, matched against a local FAQ knowledge base, answered by an LLM, evaluated
by an LLM-as-judge, and escalated to a human when necessary — all orchestrated as a LangGraph
state machine.

## Stack

- FastAPI — HTTP layer
- LangGraph — workflow orchestration with conditional branching
- LiteLLM — LLM provider abstraction (configured for [Groq](https://console.groq.com)'s free API tier)
- Streamlit — manual testing UI
- JSON files — FAQ knowledge base and session storage (no external database)

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in a free Groq API key from https://console.groq.com/keys:

   ```bash
   copy .env.example .env
   ```

## Run

Start the FastAPI backend:

```bash
python -m app.main
```

The API is available at `http://localhost:8000` (interactive docs at `/docs`).

In a second terminal, start the Streamlit UI:

```bash
streamlit run app/ui/streamlit_app.py
```

## API Endpoints

- `GET /health`
- `POST /api/v1/support/tickets/process`
- `GET /api/v1/support/sessions/{session_id}`