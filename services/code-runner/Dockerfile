FROM eclipse-temurin:21-jdk-jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 sandbox \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /sandbox sandbox

WORKDIR /opt/runner
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt
COPY executor.py app.py ./

USER sandbox
ENV HOME=/sandbox
ENV PYTHONDONTWRITEBYTECODE=1
EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/health')"

CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
