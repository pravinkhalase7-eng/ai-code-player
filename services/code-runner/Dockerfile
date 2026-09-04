FROM eclipse-temurin:21-jdk-jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 sandbox \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /sandbox sandbox

WORKDIR /opt/runner
COPY requirements.txt .
# Jammy pip has no --break-system-packages; install into a venv instead.
RUN python3 -m venv /opt/runner/.venv \
    && /opt/runner/.venv/bin/pip install --no-cache-dir -r requirements.txt
COPY executor.py app.py ./

USER sandbox
ENV HOME=/sandbox
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/runner/.venv/bin:${PATH}"
EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/health')"

CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
