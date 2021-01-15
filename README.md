# overpass
A self-hosted Twtich alternative, powered by nginx-rtmp.

Features include authentication via Discord and a web player.


# Setup

- Clone the repository
- Create a virtual environment for the package
- Install its dependencies
- Create a config file

Create an empty `.env` in the projects' root directory which contains the following:

```
DISCORD_CLIENT_ID =
DISCORD_CLIENT_SECRET = ""
DISCORD_REDIRECT_URI = ""
SECRET_KEY = (whatever os.urandom spits out after the byte symbol)

HLS_PATH = ""
REC_PATH = ""
```

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
            record all;
            record_path /your/recording/path;
            record_append on;

            hls on;
            hls_path /your/hls/path;
            hls_fragment 3;
            hls_playlist_length 60;
            exec_record_done bash -c "/usr/bin/ffmpeg -i $path -acodec copy -vcodec copy /your/recording/path/$basename.mp4 && rm $path";
         }
    }
}


```