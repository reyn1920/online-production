web: python main.py
api: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
worker: python -m celery worker -A app.celery --loglevel=info
release: python -m alembic upgrade head
