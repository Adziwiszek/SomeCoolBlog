import pytest
from myblog.db import get_db
import json

def test_index(client, auth):
    response = client.get('/')
    assert b"Log In" in response.data
    assert b"Register" in response.data

    auth.login()
    response = client.get('/')
    assert b'Log Out' in response.data
    assert b'test title' in response.data
    assert b'by test on 2018-01-01' in response.data
    assert b'test\nbody' in response.data
    assert b'href="/update/1"' in response.data

'''
@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
    '/1/delete',
))'''
def test_login_required(client):
    response = client.post('/create')
    assert response.headers["location"] == "/auth/login"

    response = client.patch('/post/1')
    assert response.headers["location"] == "/auth/login"

    response = client.delete('/post/1')
    assert response.headers["location"] == "/auth/login"


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.patch('/post/1').status_code == 403
    assert client.delete('/post/1').status_code == 403
    # current user doesn't see edit link
    assert b'href="/1/update"' not in client.get('/').data

'''
@pytest.mark.parametrize('path', (
    '/2/update',
    '/2/delete',
))'''
def test_exists_required(client, auth):
    auth.login()
    assert client.patch('/post/2').status_code == 404
    assert client.delete('/post/2').status_code == 404

def test_create(client, auth, app):
    auth.login()
    assert client.get('/create').status_code == 200
    client.post('/create', data={'title': 'created', 'body': '', 'tags': 'tag1 tag2'})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2

def test_update(client, auth, app):
    auth.login()
    assert client.get('/update/1').status_code == 200
    client.patch('/post/1', data={'title': 'updated', 'body': '', 'tags': 'tag4 tag3'})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'

'''
@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
))'''
def test_create_update_validate(client, auth):
    auth.login()
    response = client.post('/create', data={'title': '', 'body': '', 'tags': ''})
    assert b'Title is required.' in response.data

    response = client.patch('/post/1', data={'title': '', 'body': '', 'tags': ''})
    assert b'Title is required.' in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.delete('/post/1')
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post is None

def test_receive_message(client, auth, app):
    # TODO: maybe in future add tests for getting comments from post that
    # doesn't exist (although right now it also works)

    # Try to read comments, when there are none
    response = client.get('/1/receive', content_type='application/json')
    data_response = json.loads(response.data)
    assert data_response['status'] == 'success'
    assert data_response['message'] == 'no comments found'

    # Send a comment and check if we can get it
    auth.login()
    client.post('/send', 
                data=json.dumps({'message': 'dupa', 'postID': 1}),
                content_type='application/json')
    response = client.get('/1/receive', content_type='application/json')
    data_response = json.loads(response.data)
    assert data_response['status'] == 'success'
    assert data_response['message'] == 'comments found'

def test_send_message(client, auth, app):
    auth.login()

    response = client.post('/send', 
                           data=json.dumps({'message': 'dupa', 'postID': 1}),
                           content_type='application/json')
    data_response = json.loads(response.data)
    assert 'comment' in data_response
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM comment'
                           ' WHERE post_id = 1').fetchone()[0]
        assert count == 1
