-- Insert test data
INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO post (title, body, author_id, created, upvotes, downvotes)
VALUES
  ('test title', 'test' || x'0a' || 'body', 1, '2018-01-01 00:00:00', 0, 0);

INSERT INTO tag (name) VALUES ('my-tag');
INSERT INTO post_tags (post_id, tag_id) VALUES (1, 1);
-- INSERT INTO comment (post_id, author_id, body)
-- VALUES
--   (1, 1, 'body')