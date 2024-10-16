  DROP TABLE IF EXISTS user;
  DROP TABLE IF EXISTS post;
  DROP TABLE IF EXISTS comment;
  DROP TABLE IF EXISTS user_votes;
  DROP TABLE IF EXISTS tag;
  DROP TABLE IF EXISTS post_tags;

  CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
  );

  CREATE TABLE post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    upvotes INTEGER NOT NULL DEFAULT 0,
    downvotes  INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES user (id)
  );

  CREATE TABLE comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    body TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES post (id),
    FOREIGN KEY (author_id) REFERENCES user (id)
    -- in future add update time/status, things for moderation, chain comments
  );

  CREATE TABLE user_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    vote BOOLEAN NOT NULL DEFAULT TRUE -- TRUE -> upvote FALSE -> downvote
  );

  CREATE TABLE tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
  );

  CREATE TABLE post_tags (
    post_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts (id),
    FOREIGN KEY (tag_id) REFERENCES tags (id),
    PRIMARY KEY (post_id, tag_id)
  );
