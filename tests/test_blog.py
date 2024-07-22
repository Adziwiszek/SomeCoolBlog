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
    assert b'href="/1/update"' in response.data

@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
    '/1/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.post('/1/update').status_code == 403
    assert client.post('/1/delete').status_code == 403
    # current user doesn't see edit link
    assert b'href="/1/update"' not in client.get('/').data


@pytest.mark.parametrize('path', (
    '/2/update',
    '/2/delete',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404

def test_create(client, auth, app):
    auth.login()
    assert client.get('/create').status_code == 200
    client.post('/create', data={'title': 'created', 'body': ''})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get('/1/update').status_code == 200
    client.post('/1/update', data={'title': 'updated', 'body': ''})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'


@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'title': '', 'body': ''})
    assert b'Title is required.' in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post('/1/delete')
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post is None

def test_receive_message(client, auth, app):
    '''Test for reciving (from server) comments on a post'''
    # Try to read comments, when there are none
    response = client.get('/1/receive', content_type='application/json')
    data_response = json.loads(response.data)
    assert data_response['status'] == 'success'
    print(f'{data_response}')
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
    '''Tests commenting on a post'''
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


def test_vote_correctly(client, auth, app):
    '''Tests voting on a post witch exists, with correct action 
    (1 for upvoting and 0 for downvoting).'''
    auth.login()

    with app.app_context():
        db = get_db()
        cur = db.cursor()
        upvotes_before = cur.execute('SELECT upvotes FROM post WHERE id = 1').fetchone()[0]
        downvotes_before = cur.execute('SELECT downvotes FROM post WHERE id = 1').fetchone()[0]

        response_upv = client.post('/1/upvote')
        response_downv = client.post('/1/downvote')
        assert response_upv.status_code == 200

        data_upv = json.loads(response_upv.data)
        data_downv = json.loads(response_downv.data)
        assert ('votes' in data_upv) and ('status' in data_upv)
        assert ('votes' in data_downv) and ('status' in data_downv)
        # check if json returned by request has correct number of votes
        assert data_upv['votes'] == upvotes_before + 1
        assert data_downv['votes'] == downvotes_before + 1

        # check if database was updated
        upvotes_after = cur.execute('SELECT upvotes FROM post WHERE id = 1').fetchone()[0]
        downvotes_after = cur.execute('SELECT downvotes FROM post WHERE id = 1').fetchone()[0]
        assert upvotes_after == upvotes_before + 1
        assert downvotes_after == downvotes_before + 1

