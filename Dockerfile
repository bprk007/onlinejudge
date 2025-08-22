FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    clang \
    g++ \
    libpq-dev \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME dynamically (Debian trixie provides java 17 by default)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

WORKDIR /app
COPY . /app

# Install dependencies in one layer
RUN pip install --no-cache-dir \
    django \
    google-genai \
    python-dotenv \
    psycopg2-binary

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=toj.settings 
ENV PYTHONUNBUFFERED=1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
