FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
RUN pip install rasa-sdk
EXPOSE 5055
# Use the rasa-sdk module to run the actions server (no full Rasa install required here)
CMD ["python", "-m", "rasa_sdk", "--actions", "actions", "--port", "5055"]
