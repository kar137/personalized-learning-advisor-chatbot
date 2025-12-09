# Personalized Learning Advisor Chatbot

**Overview**

The Personalized Learning Advisor Chatbot is a Rasa-based assistant that provides personalized learning paths, course recommendations, project ideas, and career guidance, while maintaining simple user profiles to tailor advice.

**Architecture**

- **Rasa Core & NLU**: Handles intent classification, entity extraction, and dialogue management.
- **Actions server**: Custom action endpoints for recommendations and external integrations (see `actions/`).
- **Frontend**: Lightweight frontend for interacting with the bot (see `streamlit_app/` or `frontend/`).
- **Deployment**: Docker image orchestrated for deployment (Render configuration present in repository).

**Requirements**

- **Python**: 3.10+
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

**Deployment (Render)**

- The project includes a Dockerfile and startup scripts (`render_start.sh`, `render_start_simple.sh`). On Render, the service expects the `PORT` environment variable provided by the platform.
- Required environment variables on Render:
  - `ACTIONS_URL`: URL of the actions service (e.g. `https://<your-actions>.onrender.com/webhook`)
  - `MODEL_FILE` (optional): filename of the model archive inside `models/`. If omitted the startup script will use the newest `*.tar.gz` in `models/`.
- Recommended runtime image: `rasa/rasa:3.6.21-full` to match models trained with Rasa 3.6.x.

Notes about Render-specific startup:

- Render performs a port-scan to detect healthy services. Rasa must bind the public `PORT` for Render to mark the service as live. The repository contains `render_start_simple.sh` which starts Rasa directly on the Render `PORT`.
- TensorFlow-based models can have slow startup on low-CPU instances. If you see long load times consider training a lightweight model (`config_lightweight.yml` included) or using a higher-resource plan.

**Troubleshooting**

- **No valid model found**: Ensure your model archive exists in `models/` and that `MODEL_FILE` (if set) points to the correct filename. You can list models with:

```bash
ls -la models/
```

- **Model version mismatch**: The model must be compatible with the Rasa runtime. Check the Rasa version used to train the model (`rasa --version`) and ensure the Docker base image matches (e.g. `rasa/rasa:3.6.21-full`).

- **Render port not detected**: Confirm Rasa binds the provided `PORT`. Review Render service logs and ensure startup script uses the `PORT` environment variable. If you previously used an internal proxy, try starting Rasa directly on `PORT`.

- **Slow TensorFlow startup**: On low-CPU instances TensorFlow model loading can take many minutes. Mitigations:
  - Use the lightweight config `config_lightweight.yml` and retrain (reduces TensorFlow use).
  - Set TF env vars in the startup script: `TF_CPP_MIN_LOG_LEVEL=2`, `CUDA_VISIBLE_DEVICES=""`, `TF_NUM_INTEROP_THREADS=1`, `TF_NUM_INTRAOP_THREADS=1`.
  - Use a higher-tier Render instance with more CPU resources.

- **Actions not invoked**: Ensure `endpoints.yml` contains the correct `action_endpoint` URL (the startup script writes `/tmp/endpoints.yml` from the `ACTIONS_URL` env var). Verify your actions server is reachable and healthy.

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
