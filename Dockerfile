FROM rasa/rasa:3.5.0-full

WORKDIR /app

# Copy project files (models, config, actions folder, endpoints, etc.)
COPY . /app

# Ensure the render_start script is executable
RUN if [ -f ./render_start.sh ]; then chmod +x ./render_start.sh; fi

EXPOSE 5005

# Use the helper script to write endpoints.yml from ACTIONS_URL and start Rasa on $PORT
CMD ["bash", "render_start.sh"]
