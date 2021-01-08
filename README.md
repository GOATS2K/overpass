# overpass
A self-hosted Twtich alternative, powered by nginx-rtmp.

Features include authentication via Discord and a web player.
# Setup

- Clone the repository
- Create a virtual environment for the package
- Install its dependencies
- Run `flask init-db`
- Run `flask run`

## Streaming server setup

```
rtmp {
    server {
        listen 1940;
        on_publish http://127.0.0.1:5000/api/rtmp/connect;
        on_done http://127.0.0.1:5000/api/rtmp/done;

        application live {
            live on;
            record off;
            # exec_record_done /usr/bin/ffmpeg -i $path  -f mp4 /tmp/recordings/$basename.mp4;
        }
    }
}

```