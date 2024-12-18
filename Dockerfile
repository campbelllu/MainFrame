FROM python:3.10.12-alpine AS builder
EXPOSE 8000
WORKDIR /app
COPY /mainframe /app
COPY reqs_prod.txt /app
RUN python -m pip install --upgrade pip && \
   pip install -r reqs_prod.txt --no-cache-dir
CMD ["gunicorn", "mainframe.wsgi:application", "-b", "0.0.0.0:8000"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]