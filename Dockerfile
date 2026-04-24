# ── Stage 1: builder ────────────────────────────────────────────────────────
# Install Python dependencies into a user-local directory so we can copy
# only that directory into the slim runtime image (no pip, no build tools).
FROM python:3.12-slim AS builder

WORKDIR /build

# Layer the dependency install separately from the source copy so that
# Docker's cache is only invalidated when requirements.txt changes.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --user -r requirements.txt


# ── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for security — never run application code as root.
RUN addgroup --system app \
 && adduser  --system --ingroup app --no-create-home app

WORKDIR /app

# Copy only the installed packages from the builder stage.
COPY --from=builder /root/.local /home/app/.local

# Copy application source — deliberately exclude tests, agent, and docker files
# via .dockerignore so they never land in the production image.
COPY --chown=app:app . .

USER app

ENV PATH=/home/app/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Lightweight health check using Python's stdlib — no curl required.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c \
        "import urllib.request, sys; \
         urllib.request.urlopen('http://localhost:8000/health'); \
         sys.exit(0)" \
     || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
