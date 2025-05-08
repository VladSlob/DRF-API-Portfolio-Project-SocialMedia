FROM python:alpine3.21

LABEL maintainer="gnonasis@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

RUN adduser --disabled-password --no-create-home django-user
RUN mkdir -p /vol/web/media
RUN chown -R django-user:django-user /vol/
RUN chmod -R 755 /vol/web/
USER django-user
