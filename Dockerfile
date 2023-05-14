FROM python:3.10.6-alpine AS builder
EXPOSE 8000
WORKDIR /app
COPY /mainframe /app
COPY reqs.txt /app
RUN pip install -r reqs.txt --no-cache-dir
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]