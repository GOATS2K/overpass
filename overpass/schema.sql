DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS stream;

CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    snowflake INTEGER NOT NULL,
    username TEXT NOT NULL,
    avatar TEXT,
    last_login_date DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE stream (
    id INTEGER PRIMARY KEY,
    user_snowflake INTEGER NOT NULL,
    stream_key TEXT NOT NULL,
    unique_id TEXT NOT NULL,
    generate_date DEFAULT CURRENT_TIMESTAMP NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT,
    archived_file TEXT,
    archivable INTEGER,
    unlisted INTEGER,

    FOREIGN KEY (user_snowflake) REFERENCES user (snowflake)
);