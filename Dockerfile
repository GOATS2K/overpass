FROM python:3.10.7

RUN apt update
RUN apt install git nginx libnginx-mod-rtmp ffmpeg -y
RUN mkdir /archive && mkdir /hls
RUN chown -R www-data:root /archive /hls

COPY ./docker/nginx.conf /etc/nginx/nginx.conf
COPY ./docker/startup.sh /startup.sh
RUN chmod +x /startup.sh

# RUN git clone https://github.com/GOATS2K/overpass.git .
WORKDIR /app
COPY . .
RUN pip3 install .

EXPOSE 8000
EXPOSE 1935

CMD ["/startup.sh"]
