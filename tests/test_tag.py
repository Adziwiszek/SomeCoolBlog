import pytest
from myblog.db import get_db
import json

def test_add_tags(client, auth, app):
    '''Tests adding tags to the database when creating posts'''
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
    '''Tests updating tags on a post'''
    auth.login()
    client.post('/create', data={'title': 'created', 'body': '', 'tags': 'tag1s tag2'})
    client.post('/2/update', data={'title': 'updated', 'body': '', 'tags': 'tag4 tag3'})

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
    '''Tests getting all tags'''
    auth.login()
    client.post('/create', data={'title': 'created', 'body': '', 'tags': 'tag1s tag2'})

    response = client.get('/gettags')
    assert b'tag2' in response.data

def test_get_posts_with_tags(client, auth, app):
    '''Tests getting all posts with given tags'''
    auth.login()
    client.post('/create', data={'title': 'created', 'body': '', 'tags': 'my-tag'})

    response = client.get('/post?tag=my-tag')
    print(response)
    data_response = json.loads(response.data)
    print(data_response)
    assert data_response['status'] == 'success'
    assert len(data_response['posts']) == 2


    
