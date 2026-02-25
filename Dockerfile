FROM rasa/rasa-sdk:3.6.0

USER root
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
        mysql-connector-python \
        sqlalchemy \
        alembic \
        python-dotenv \
        requests

WORKDIR /app

# Copy all project files
COPY actions/ /app/actions/
COPY database/ /app/database/
COPY alembic.ini /app/alembic.ini

# Default command starts the action server
CMD ["start", "--debug", "--port", "5055", "--actions", "actions"]
