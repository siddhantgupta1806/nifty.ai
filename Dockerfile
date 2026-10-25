FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --upgrade pip && python -m pip install -e .
COPY docs ./docs
COPY examples ./examples
EXPOSE 8766
CMD ["uvicorn", "nifty_ai.web.app:app", "--host", "0.0.0.0", "--port", "8766"]
