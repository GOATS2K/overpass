FROM python:3.10.0

RUN apt update
RUN apt install git nginx libnginx-mod-rtmp ffmpeg -y
RUN mkdir /archive && mkdir /hls

COPY ./docker/nginx.conf /etc/nginx/nginx.conf
COPY ./docker/startup.sh /startup.sh
RUN chmod +x /startup.sh

WORKDIR /app
# RUN git clone https://github.com/GOATS2K/overpass.git .
COPY ../ .
RUN pip3 install .

EXPOSE 8000
EXPOSE 1935

CMD ["/startup.sh"]