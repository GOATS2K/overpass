DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS stream;

CREATE TABLE user (
    id INTEGER PRIMARY KEY NOT NULL,
    snowflake INTEGER NOT NULL,
    username TEXT NOT NULL,
    avatar TEXT NOT NULL,
    last_login_date DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE stream (
    id INTEGER PRIMARY KEY NOT NULL,
    user_snowflake INTEGER NOT NULL,
    stream_key TEXT NOT NULL,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    end_date TIMESTAMP,

    FOREIGN KEY (user_snowflake) REFERENCES user (snowflake)
);