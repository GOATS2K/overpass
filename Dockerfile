FROM python:3.10.0

RUN apt update
RUN apt install git nginx libnginx-mod-rtmp ffmpeg -y

COPY ./docker/nginx.conf /etc/nginx/nginx.conf

WORKDIR /app
RUN git clone https://github.com/GOATS2K/overpass.git .
COPY .env /app/
RUN pip3 install .
RUN flask init-db

EXPOSE 8000
EXPOSE 1935

CMD ["gunicorn", "app:app", "--workers=2", "--threads=4", "--worker-class=gthread", "--timeout=600", "--bind=0.0.0.0"]