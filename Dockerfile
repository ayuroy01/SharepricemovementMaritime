FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
# Note: we deliberately do NOT set STREAMLIT_SERVER_ENABLE_CORS.
# Streamlit's XSRF protection (left enabled) implies CORS=true; setting
# ENABLE_CORS=false alongside it triggers a startup compatibility warning.
# .streamlit/config.toml handles the rest.

WORKDIR /app

# System deps for pandas/numpy wheels are in the slim image already.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app last to keep the dependency layer cached.
COPY . .

# Default to auto mode — falls back to demo data if no NEWSAPI_KEY is set.
ENV APP_MODE=auto

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3)" || exit 1

CMD ["python", "-m", "streamlit", "run", "dashboard.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
