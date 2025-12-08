# Personalized Learning Advisor Chatbot

A production-grade Rasa chatbot for personalized learning recommendations.

## Features

- **Learning Paths**: Suggests roadmaps for AI, Web Dev, etc.
- **Course Recommendations**: Recommends courses based on domain.
- **Project Ideas**: Suggests projects for portfolio.
- **Career Guidance**: Advice on career paths.
- **Profile Tracking**: Remembers user details (Degree, GPA, Skills).

## Setup

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)

### Installation

1. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install rasa
   ```

3. Train the model:

   ```bash
   rasa train
   ```

4. Run the Action Server:

   ```bash
   rasa run actions
   ```

5. Run the Rasa Server:
   ```bash
   rasa run --enable-api --cors "*"
   ```

### Testing

Run the tests using:

```bash
rasa test
```

This will run end-to-end testing on the stories defined in `tests/test_stories.yml`.


## Usage

Open `frontend/index.html` in your browser to chat with the bot.
