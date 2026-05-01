# HR Interview Practice Chatbot

Interactive HR interview simulator built with **Streamlit** and **OpenAI**.  
It conducts a short interview for a selected role and then generates feedback with an overall score, highlighting strengths and gaps.

---

## Overview

This project is a self‑contained web app where candidates can practice **machine learning, data science or analyst** interviews in a safe environment.

The app:

- Asks HR‑style questions tailored to the user’s **background**, **level**, **role**, and **company**
- Limits the number of messages
- Runs a dedicated **feedback pass** that scores the candidate and explains the reasoning

The goal is to demonstrate:

- Clean, readable **Python**
- Stateful **Streamlit** UI
- Structured **LLM integration**

---

## Features

- **Role‑aware interview**
  - Collects name, experience, skills, seniority level, target position, and company
  - Builds a custom system prompt for the interviewer model based on this data

- **Limited‑turn conversation**
  - Caps the number of user messages
  - Adds a “final answer” system message so the last assistant reply clearly ends the interview

- **Structured feedback generator**
  - Second LLM call reviews the full conversation
  - Returns:
    - `Overall Score: 1–10`
    - `Feedback:` strengths, weaknesses, and missing skills

- **Clean state management**
  - Uses `st.session_state` for:
    - Setup progress
    - Chat history
    - Message counts

  - Keeps the app stateless across sessions on the server side

- **Centralised prompts and LLM helpers**
  - Prompt text is built via small helper functions
  - All OpenAI calls go through helper functions with `try/except` and user‑friendly error messages

---

## Tech Stack

- **Language:** Python 3.10+
- **Web UI:** Streamlit
- **LLM:** OpenAI API 
- **Utility:** `streamlit_js_eval` for a simple “Restart interview” page reload

---

## How It Works

### 1. Setup phase

1. User fills in:
   - Name
   - Experience summary
   - Skills
2. User selects:
   - Level (Junior / Mid / Senior)
   - Role (Data Scientist, ML Engineer, etc.)
   - Company (Amazon, Meta, Spotify, …)
3. The app builds a system prompt via `build_interview_system_prompt()` and stores it as the first message in `st.session_state.messages`.

### 2. Interview phase

1. Streamlit chat UI renders all messages except internal system messages.
2. On each user reply:
   - The message is appended to `st.session_state.messages`.
   - `user_message_count` is incremented.
   - When approaching the limit, a `build_last_turn_system_prompt()` message is added so the model knows this is the final answer.
3. The app calls `stream_interview_completion()`:
   - Wraps a shared `_create_chat_completion()` that:
     - Creates an OpenAI client
     - Calls `chat.completions.create`
     - Handles errors with `st.error` and `st.stop()`
4. The streamed response is displayed via `st.write_stream` and stored in history.

### 3. Feedback phase

1. After the last turn, the user clicks **Get Feedback**.
2. The app builds:
   - A feedback system prompt via `build_feedback_model_system_prompt()`
   - A user message summarizing the conversation via `build_feedback_model_messages_prompt(conversation_history)`
3. It calls `get_feedback_completion()` (non‑streaming) and renders the resulting feedback text.

The entire flow lives in a single `app.py` file, but is organised into clear sections:

- Constants and variables
- Prompt builders
- LLM helpers
- Session state helpers
- Setup UI
- Interview UI
- Feedback UI

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/evsvl/hr-interview-chatbot.git
cd hr-interview-chatbot
```

### 2. Install dependencies

```bash
pip install streamlit openai streamlit-js-eval
```

### 3. Configure secrets

In a `.streamlit` directory rename `secrets.example.toml` to `secrets.toml`

And put your key to

```toml
OPENAI_API_KEY = "..."
```

Make sure your `.gitignore` contains:

```gitignore
.streamlit/secrets.toml
```

so your API key is never pushed to GitHub

### 5. Run the app

```bash
streamlit run app.py
```

Open the URL shown in the terminal (typically http://localhost:8501) and follow the steps in the UI.

---

## Possible Extensions

Ideas for future enhancements:

- **Model selector**  
  Let users choose between different LLMs 

- **Custom company and role input**  
  Allow users to type any company name and role title

- **Persistence and analytics**  
  Store interviews and feedback in a database to:
  - Track progress over time
  - Visualise common weaknesses

- **Rate limiting**  
  Add per‑IP or per‑user limits

- **Multi‑language support**  
  Add language selection in UI and allow the interview and feedback to run in other languages