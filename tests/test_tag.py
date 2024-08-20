import pytest
from myblog.db import get_db
import json

def test_add_tags(client, auth, app):
    auth.login()

    client.post('/create', data={'title': 'created', 'body': '', 'tags': 'tag1 tag2'})

    with app.app_context():
        db = get_db()
        # check that two tags were added to tag table
        tags = db.execute('SELECT COUNT(name) FROM tag').fetchone()[0]
        assert tags == 3

        # test adding tag that already exists in database
        client.post('/create', data={'title': 'created', 'body': '', 'tags': 'tag2 tag3'})
        tags = db.execute('SELECT COUNT(name) FROM tag').fetchone()[0]
        assert tags == 4


def test_update_tags(client, auth, app):
    auth.login()
    client.post('/create', data={'title': 'created', 'body': '', 'tags': 'tag1s tag2'})
    client.patch('/post/2', data={'title': 'updated', 'body': '', 'tags': 'tag4 tag3'})

    with app.app_context():
        db = get_db()
        post = db.execute(
            'SELECT t.name'
            ' FROM tag t JOIN post_tags pt ON t.id = pt.tag_id'
            ' WHERE pt.post_id = 2'
        ).fetchall()
        data_post = [p['name'] for p in post]
        print(data_post)
        assert 'tag4' in data_post

def test_get_all_tags(client, auth, app):
    auth.login()
    client.post('/create', data={'title': 'created', 'body': '', 'tags': 'tag1s tag2'})

    response = client.get('/gettags')
    assert b'tag2' in response.data

def test_get_posts_with_tags(client, auth, app):
    auth.login()
    client.post('/create', data={'title': 'created', 'body': '', 'tags': 'my-tag'})

    response = client.get('/post?tag=my-tag')
    assert b'failure' not in response.data
    # check if two posts with tag 'my-tag' are loaded to the page
    assert b'created' in response.data 
    assert b'test title' in response.data


    
