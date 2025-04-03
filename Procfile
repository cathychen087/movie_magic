release: python manage.py migrate
web: gunicorn movie_magic.wsgi:application --log-file - --workers 2 --timeout 120 --max-requests 1000 --bind 0.0.0.0:$PORT 