FROM rasa/rasa:3.6.21-full

WORKDIR /app

# Copy project files (models, config, actions folder, endpoints, etc.)
COPY . /app

# Clear any ENTRYPOINT inherited from the base image (the rasa image sets an ENTRYPOINT 'rasa')
# so that we can run our startup script directly. If we don't clear it, Docker will execute
# `rasa bash render_start.sh` which makes `rasa` treat `bash` as a subcommand (invalid).
ENTRYPOINT []

EXPOSE 5005

# Use the helper script to write endpoints.yml from ACTIONS_URL and start Rasa on $PORT
# Run the script with bash to avoid relying on the executable bit.
CMD ["bash", "render_start.sh"]
