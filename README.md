# overpass
A self-hosted Twitch alternative, powered by nginx-rtmp.

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
DISCORD_GUILD_ID = (if you want to restrict access to the tool from a certain guild ID - set one here)


OVERPASS_SECRET_KEY = (whatever os.urandom spits out after the byte symbol)

HLS_PATH = ""
REC_PATH = ""
RTMP_SERVER = "127.0.0.1:1935/live"
```
- Run `flask init-db`
- Run `flask run` (only in dev environments)

# Streaming server setup

- Create the directories you defined in `HLS_PATH` and `REC_PATH` and make sure to give `www-data` write permissions to said folder.

*Make sure the user the Overpass is running as also has read and write access to the same folders.*

```
rtmp {
    server {
        listen 1935;
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
            exec_record_done bash -c "/usr/bin/ffmpeg -i $path -acodec copy -vcodec copy -movflags +faststart /your/recording/path/$basename.mp4 && rm $path";
         }
    }
}


```

# Deploying to production

`gunicorn -w 4 app:app --log-level=debug`

## NGINX setup
```
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;
    }
```