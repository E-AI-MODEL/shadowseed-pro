FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    GRADIO_ANALYTICS_ENABLED=False \
    TOKENIZERS_PARALLELISM=false \
    HF_HOME=/tmp/huggingface-cache \
    PORT=7860

RUN useradd --create-home --uid 1000 user

WORKDIR /home/user/app
COPY --chown=user:user . /home/user/app

RUN python -m pip install --upgrade pip && \
    python -m pip install ".[workbench]"

USER user

EXPOSE 7860

CMD ["python", "space_app.py"]
