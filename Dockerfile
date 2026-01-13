# Dockerfile
# Unk Agent - Production Container
# Who Visions LLC

# ═══════════════════════════════════════════════════════════════════════════
# BUILD STAGE
# ═══════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ═══════════════════════════════════════════════════════════════════════════
# PRODUCTION STAGE
# ═══════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim as production

# Security: Run as non-root user
RUN groupadd -r unk && useradd -r -g unk unk

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

# Copy application code
COPY gemini_agent/ ./gemini_agent/
COPY routers/ ./routers/
COPY services/ ./services/
COPY tools/ ./tools/
COPY skills/ ./skills/
COPY deploy.py .
# Optional: Copy scripts if needed for debugging, but usually omit from prod
# COPY scripts/ ./scripts/

# Set ownership
RUN chown -R unk:unk /app

# Switch to non-root user
USER unk

# Environment variables
ENV ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Cloud Run uses PORT env variable
ENV PORT=8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run with python -m to ensure imports work from root
CMD ["python", "deploy.py"]
