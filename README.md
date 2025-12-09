# Personalized Learning Advisor Chatbot

**Overview**

The Personalized Learning Advisor Chatbot is a Rasa-based assistant that provides personalized learning paths, course recommendations, project ideas, and career guidance, while maintaining simple user profiles to tailor advice.

**Architecture**

- **Rasa Core & NLU**: Handles intent classification, entity extraction, and dialogue management.
- **Actions server**: Custom action endpoints for recommendations and external integrations (see `actions/`).
- **Frontend**: Lightweight frontend for interacting with the bot (see `streamlit_app/` or `frontend/`).
- **Deployment**: Docker image orchestrated for deployment (Render configuration present in repository).

**Requirements**

- **Python**: 3.10
- **Rasa**: Tested with `rasa==3.6.21` (runtime image `rasa/rasa:3.6.21-full` recommended)
- **Optional**: Docker and Docker Compose for containerized deployments

**Local development**

1. Create and activate a virtual environment:

```bash
python -m venv .env
# macOS / Linux
source .env/bin/activate
# Windows (PowerShell)
.\.env\Scripts\Activate.ps1
```

2. Install Python dependencies (project uses Rasa):

```bash
pip install -r requirements.txt
# or at minimum:
pip install rasa==3.6.21
```

3. Train the model:

```bash
rasa train
```

4. Run the actions server in a separate terminal:

```bash
rasa run actions
```

5. Run Rasa locally:

```bash
rasa run --enable-api --cors "*" --port 5005
```

6. Open the frontend for manual testing (if using Streamlit):

```bash
cd streamlit_app
streamlit run app.py
```

**Project layout**

- `actions/` — Custom action server code
- `models/` — Trained model archives (`*.tar.gz`)
- `data/` — NLU, stories, rules, and domain data
- `streamlit_app/` — Optional frontend for manual testing
- `render_start.sh`, `render_start_simple.sh` — startup scripts used for deployment
- `config.yml`, `config_lightweight.yml` — Rasa model configurations

**Contributing**

- Fork the repository, create a branch for your change, and submit a pull request with a clear description. Keep changes focused; run `rasa train` and `rasa test` before opening a PR.

**License & Contact**

This repository does not include a license file. If you wish to add one, include a `LICENSE` file at the repository root.

For questions or support, open an issue describing the problem and supply logs from the deployment or instructions to reproduce locally.
