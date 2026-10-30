FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py id3.py db.py config.py ./
COPY templates ./templates
COPY static ./static

RUN useradd -m app && mkdir -p uploads && chown -R app:app /app
USER app

EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "app:app"]