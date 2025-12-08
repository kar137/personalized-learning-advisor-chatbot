# Learning Advisor - Streamlit Frontend

A professional web interface for the Learning Advisor chatbot powered by Rasa.


## Prerequisites

Make sure you have the following running:

1. **Rasa Action Server** (port 5055)
2. **Rasa Server** (port 5005)

## Installation

```bash
# Navigate to the streamlit app directory
cd rasa_chatbot/streamlit_app

# Install dependencies
pip install -r requirements.txt
```

## Running the App

### Option 1: Run directly

```bash
cd rasa_chatbot/streamlit_app
streamlit run app.py
```

### Option 2: Run from project root

```bash
cd rasa_chatbot
streamlit run streamlit_app/app.py
```

The app will open in your browser at `http://localhost:8501`

## Complete Startup Sequence

Open 3 terminals and run:

**Terminal 1 - Action Server:**

```powershell
cd rasa_chatbot
rasa run actions --debug
```

**Terminal 2 - Rasa Server:**

```powershell
cd rasa_chatbot
rasa run --enable-api --cors "*" --debug
```

**Terminal 3 - Streamlit App:**

```powershell
cd rasa_chatbot/streamlit_app
streamlit run app.py
```

## Configuration

Edit `.streamlit/config.toml` to customize:

- Theme colors
- Server port
- Other Streamlit settings

To change the Rasa server URL, edit `RASA_API_URL` in `app.py`:

```python
RASA_API_URL = "http://localhost:5005/webhooks/rest/webhook"
```