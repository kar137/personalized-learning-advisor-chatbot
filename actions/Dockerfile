FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
RUN pip install rasa-sdk
EXPOSE 5055
CMD ["rasa", "run", "actions", "--port", "5055"]
