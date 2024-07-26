import pytest
from myblog.db import get_db
import json

def test_upvote(client, auth, app):
    '''Tests upvoting a post'''
    auth.login()

    with app.app_context():
        db = get_db()
        response = client.post('/1/upvote')
        assert response.status_code == 200

        data = json.loads(response.data)
        # check response
        assert data['status'] == 'success'
        assert data['votes']['upvotes'] == 1

        # check that database was updated
        upv_db = db.execute('SELECT upvotes FROM post WHERE id = 1').fetchone()[0]
        assert upv_db == 1

        # check user_votes was updated
        vote = db.execute('SELECT vote FROM user_votes WHERE user_id = 1 AND post_id = 1').fetchone()[0]
        assert vote == True 

def test_downvote(client, auth, app):
    '''Tests downvoting a post'''
    auth.login()

    with app.app_context():
        db = get_db()
        response = client.post('/1/downvote')
        assert response.status_code == 200

        data = json.loads(response.data)
        # check response
        assert data['status'] == 'success'
        assert data['votes']['downvotes'] == 1

        # check that database was updated
        upv_db = db.execute('SELECT downvotes FROM post WHERE id = 1').fetchone()[0]
        assert upv_db == 1

        # check user_votes was updated
        vote = db.execute('SELECT vote FROM user_votes WHERE user_id = 1 AND post_id = 1').fetchone()[0]
        assert vote == False

def test_vote_twice(client, auth, app):
    '''Tests upvoting(downvoting) twice on the same post, which should remove 
    the first upvote(downvote).'''
    auth.login()

    with app.app_context():
        db = get_db()
        # upvotes
        client.post('/1/upvote')
        data_upv = json.loads(client.post('/1/upvote').data)

        vote = db.execute('SELECT vote FROM user_votes WHERE user_id = 1 AND post_id = 1').fetchone()
        assert vote is None 
        assert data_upv['votes']['upvotes'] == 0
        # downvotes
        client.post('/1/downvote')
        data_dwv = json.loads(client.post('/1/downvote').data)

        vote = db.execute('SELECT vote FROM user_votes WHERE user_id = 1 AND post_id = 1').fetchone()
        assert vote is None 
        assert data_dwv['votes']['downvotes'] == 0

        # checking database
        db_up, db_down = db.execute('SELECT upvotes, downvotes FROM post WHERE id = 1').fetchone()
        assert db_up == 0
        assert db_down == 0

def test_upvote_downvote(client, auth, app):
    '''Tests upvoting and then downvoting a post. The second action should 
    remove the upvote.'''
    auth.login()

    with app.app_context():
        db = get_db()

        client.post('/1/upvote')
        data_dwv = json.loads(client.post('/1/downvote').data)
        assert data_dwv['votes']['upvotes'] == 0       
        assert data_dwv['votes']['downvotes'] == 1

        # checking database
        db_up, db_down = db.execute('SELECT upvotes, downvotes FROM post WHERE id = 1').fetchone()
        assert db_up == 0
        assert db_down == 1

def test_downvote_upvote(client, auth, app):
    '''Tests downvoting and then upvoting a post. The second action should 
    remove the downvote.'''
    auth.login()

    with app.app_context():
        db = get_db()

        client.post('/1/downvote')
        data_dwv = json.loads(client.post('/1/upvote').data)
        assert data_dwv['votes']['upvotes'] == 1       
        assert data_dwv['votes']['downvotes'] == 0

        # checking database
        db_up, db_down = db.execute('SELECT upvotes, downvotes FROM post WHERE id = 1').fetchone()
        assert db_up == 1
        assert db_down == 0
