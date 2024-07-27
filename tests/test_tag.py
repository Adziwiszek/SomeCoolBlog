import pytest
from myblog.db import get_db
import json

# TODO:
# 1) get all tags
# 2) get posts with given tags
# 3) set, update, delete tags
# 4) when adding tags, select from existing 

def test_add_tags(client, auth, app):
    auth.login()

    client.post('/create', data={'title': 'created', 'body': '', 'tags': ['tag1', 'tag2']})

    with app.app_context():
        db = get_db()
        # check that two tags were added to tag table
        tags = db.execute('SELECT COUNT(name) FROM tag').fetchone()[0]
        assert tags == 2

        # test adding tag that already exists in database
        client.post('/create', data={'title': 'created', 'body': '', 'tags': ['tag2', 'tag3']})
        tags = db.execute('SELECT COUNT(name) FROM tag').fetchone()[0]
        assert tags == 3


