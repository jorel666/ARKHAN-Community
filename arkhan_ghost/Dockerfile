FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ghost_main.py .
ENV GHOST_DB=/data/ghost_state.db
VOLUME ["/data"]
EXPOSE 8080
CMD ["python3", "ghost_main.py"]
