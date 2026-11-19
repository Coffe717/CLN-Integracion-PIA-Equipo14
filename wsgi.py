"""Punto de entrada WSGI: `gunicorn wsgi:app` (producción) o `python wsgi.py` (local)."""
from src.api.app import create_app
from src.api.config import Config

app = create_app()

if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=Config.desde_entorno().port)
