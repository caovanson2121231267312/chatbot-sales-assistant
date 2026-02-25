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

COPY actions/ /app/actions/
COPY database/ /app/database/

CMD ["start", "--debug", "--port", "5055", "--actions", "actions"]
