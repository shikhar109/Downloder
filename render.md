services:
  - type: web
    name: cutcraft-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    plan: free
