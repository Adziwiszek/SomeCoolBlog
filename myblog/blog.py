from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,
    jsonify, current_app
)
from werkzeug.exceptions import abort
# from flask_wtf.csrf import generate_csrf
from myblog.auth import login_required
from myblog.db import get_db
import sqlite3

bp = Blueprint('blog', __name__)

def get_post_tags(post_id):
    tags = get_db().execute(
        'SELECT t.name'
        ' FROM tag t JOIN post_tags pt ON t.id = pt.tag_id'
        ' WHERE pt.post_id = ?',
        (post_id,)
    ).fetchall()


    return [tag['name'] for tag in tags]

def get_post(id, check_author=True):
    '''Returns dictionary of posts.'''
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, upvotes, downvotes'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    get_post_tags(id)
    post_dict = dict(post)
    tags = get_post_tags(post['id'])
    post_dict['tags'] = tags

    return post_dict

def get_posts_comments(post_id):
    comments = get_db().execute(
        'SELECT c.id, c.body, c.created, u.username'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' WHERE c.post_id = ?'
        ' ORDER BY created DESC',
        (post_id,)
    ).fetchall()
    if comments is None or comments == []:
        return jsonify({'status': 'success',
                        'message': 'no comments found',
                        'comments': []})

    return jsonify({
        'status': 'success',
        'message': 'comments found',
        'comments': [
            {
                'id': comment['id'],
                'body': comment['body'],
                'created': comment['created'].isoformat(),
                'username': comment['username']
            } for comment in comments
        ]
    })

@bp.route('/')
def index():
    '''Redirects user to index page with all posts posted'''
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, upvotes, downvotes'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    tagged_posts = []
    for post in posts:
        post_dict = dict(post)
        tags = get_post_tags(post['id'])
        post_dict['tags'] = tags
        tagged_posts.append(post_dict)

    return render_template('blog/index.html', posts=tagged_posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    '''Handles creating a post.'''
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = request.form['tags'].split()
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            new_post_id = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
            for tag in tags:
                if tag:
                    db.execute(
                        'INSERT OR IGNORE INTO tag (name) VALUES (?)',
                        (tag,)
                    )
                    tag_id = db.execute(
                        'SELECT id FROM tag WHERE name = ?',
                        (tag,)
                    ).fetchone()[0]

                    db.execute(
                        'INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?)',
                        (new_post_id, tag_id)
                    )

            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


@bp.route('/post/<int:id>', methods=('PATCH', 'POST'))
@login_required
def update(id):
    post = get_post(id)
    print('updating...')
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = request.form['tags'].split()
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.execute(
                'DELETE FROM post_tags WHERE post_id = ?',
                (id,)
            )
            for tag in tags:
                db.execute(
                    'INSERT OR IGNORE INTO tag (name) VALUES (?)',
                    (tag,)
                )
                tag_id = db.execute(
                    'SELECT id FROM tag WHERE name = ?',
                    (tag,)
                ).fetchone()[0]
                db.execute(
                    'INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)',
                    (id, tag_id)
                )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/update/<int:id>', methods=('GET',))
@login_required
def update_page(id):
    post = get_post(id)
    if request.method == 'GET':
        print('getting update page...')
        return render_template('blog/update.html', post=post)
    return  redirect(url_for('blog.index'))

@bp.route('/post/<int:id>', methods=('DELETE',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/post/<int:id>/', methods=('GET',))
def read(id):
    post = get_post(id, False)
    db = get_db()
    comments = db.execute(
        'SELECT c.id, c.body, c.created, u.username FROM comment c JOIN user u ON c.author_id = u.id WHERE c.post_id = ? ORDER BY c.created DESC',
        (id,)
    ).fetchall()
    post_dict = dict(post)
    tags = get_post_tags(post['id'])
    post_dict['tags'] = tags
    return render_template('blog/read.html', post=post_dict, comments=comments)


@bp.route('/<int:id>/receive', methods=('POST', 'GET'))
def receive_message(id):
    comments = get_posts_comments(id)
    return comments


@bp.route('/send', methods=('POST',))
@login_required
def send_message():
    if request.method == 'POST':
        data = request.json

        message = data['message']
        postID = data['postID']

        if not message: 
            return jsonify({'status': 'error',
                            'message': 'message is required.'})
        if not postID: 
            return jsonify({'status': 'error',
                            'message': 'postID is required.'})

        db = get_db()
        cur = db.cursor()
        cur.execute(
            'INSERT INTO comment (post_id, author_id, body)'
            ' VALUES (?, ?, ?)',
            (postID, g.user['id'], message)
        )
        db.commit()

        # fetch the newly inserted comment
        cur.execute(
            'SELECT c.id, c.body, c.created, u.username FROM comment c JOIN user u ON c.author_id = u.id WHERE c.id = ?',
            (cur.lastrowid,)
        )
        new_comment = cur.fetchone()
        response = jsonify({
            'status': 'success',
            'comment': {
                'id': new_comment['id'],
                'body': new_comment['body'],
                'created': new_comment['created'].strftime('%Y-%m-%d %H:%M:%S'),
                'username': new_comment['username']
            }
        })
        return response
        
    return jsonify({'status': 'failure'})    


@bp.route('/<int:id>/downvote', methods=('POST',))
def downvote(id):
    '''Downvote a post. If post was already downvoted by this user, remove the downvote.
    If this user upvoted this post already, remove the upvote and downvote.'''
    try:
        db = get_db() 
        cur = db.cursor()
        votes = cur.execute(
            'SELECT upvotes, downvotes FROM post'
            ' WHERE id = ?',
            (id,)
        ).fetchone()
        if votes is None:
            return jsonify({'status': 'failure',
                            'message': 'post doesn\'t exist!'})
        
        voted = cur.execute(
            'SELECT vote FROM user_votes'
            ' WHERE user_id = ? AND post_id = ?',
            (g.user['id'], id)
        ).fetchone()   

        if voted is not None: # user has voted on this post before
            voted = voted[0]
            if not voted: # user downvoted this post before
                cur.execute(
                    'DELETE FROM user_votes WHERE post_id = ? AND user_id = ?',
                    (id, g.user['id'])
                )
                cur.execute(
                    'UPDATE post SET downvotes = ?'
                    ' WHERE id = ?',
                    (votes[1] - 1, id)
                )
                db.commit()
                return jsonify({'status': 'success',
                            'votes': {
                                'upvotes': votes[0],
                                'downvotes': votes[1] - 1
                            }})      
            else: # user upvoted before
                cur.execute(
                    'UPDATE user_votes SET vote = FALSE'
                    ' WHERE user_id = ? AND post_id = ?',
                    (g.user['id'], id)
                )      
                cur.execute(
                    'UPDATE post SET upvotes = ?, downvotes = ?'
                    ' WHERE id = ?',
                    (votes[0] - 1, votes[1] + 1, id)
                )
                db.commit()
                return jsonify({'status': 'success',
                            'votes': {
                                'upvotes': votes[0] - 1,
                                'downvotes': votes[1] + 1
                            }})
        else: # user hasn't voted on this before\
            cur.execute(
                'INSERT INTO user_votes (user_id, post_id, vote)'
                ' VALUES (?, ?, ?)',
                (g.user['id'], id, False)
            )
            cur.execute(
                'UPDATE post SET downvotes = ?'
                ' WHERE id = ?',
                (votes[1] + 1, id)
            )
            db.commit()

            return jsonify({'status': 'success',
                            'votes': {
                                'upvotes': votes[0],
                                'downvotes': votes[1] + 1
                            }})        
    except Exception as e:
        # current_app.logger.error(f'Error in upvote route: {str(e)}')
        db.rollback()
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred'}), 500


@bp.route('/<int:id>/upvote', methods=('POST',))
def upvote(id):
    '''Upvote a post. If post was already upvoted by this user, remove the upvote.
    If this user downvoted this post already, remove the downvote and upvote.'''
    try:
        db = get_db() 
        cur = db.cursor()
        votes = cur.execute(
            'SELECT upvotes, downvotes FROM post'
            ' WHERE id = ?',
            (id,)
        ).fetchone()
        if votes is None:
            return jsonify({'status': 'failure',
                            'message': 'post doesn\'t exist!'})
        
        voted = cur.execute(
            'SELECT vote FROM user_votes'
            ' WHERE user_id = ? AND post_id = ?',
            (g.user['id'], id)
        ).fetchone()   

        if voted is not None: # user has voted on this post before
            voted = voted[0]
            if voted: # user upvoted this post before
                cur.execute(
                    'DELETE FROM user_votes WHERE post_id = ? AND user_id = ?',
                    (id, g.user['id'])
                )
                cur.execute(
                    'UPDATE post SET upvotes = ?'
                    ' WHERE id = ?',
                    (votes[0] - 1, id)
                )
                db.commit()
                return jsonify({'status': 'success',
                            'votes': {
                                'upvotes': votes[0] - 1,
                                'downvotes': votes[1]
                            }})      
            else:
                cur.execute(
                    'UPDATE user_votes SET vote = TRUE'
                    ' WHERE user_id = ? AND post_id = ?',
                    (g.user['id'], id)
                )      
                cur.execute(
                    'UPDATE post SET upvotes = ?, downvotes = ?'
                    ' WHERE id = ?',
                    (votes[0] + 1, votes[1] - 1, id)
                )
                db.commit()
                return jsonify({'status': 'success',
                            'votes': {
                                'upvotes': votes[0] + 1,
                                'downvotes': votes[1] - 1
                            }})
        else: # user hasn't voted on this before
            cur.execute(
                'INSERT INTO user_votes (user_id, post_id)'
                ' VALUES (?, ?)',
                (g.user['id'], id)
            )
            cur.execute(
                'UPDATE post SET upvotes = ?'
                ' WHERE id = ?',
                (votes[0] + 1, id)
            )
            db.commit()

            return jsonify({'status': 'success',
                            'votes': {
                                'upvotes': votes[0] + 1,
                                'downvotes': votes[1]
                            }})        
    except Exception as e:
        # current_app.logger.error(f'Error in upvote route: {str(e)}')
        db.rollback()
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred'}), 500
    
@bp.route('/gettags', methods=('GET',))
def get_tags():
    db = get_db()
    tags = db.execute('SELECT name FROM tag').fetchall()
    tags = [tag['name'] for tag in tags]
    return tags

@bp.route('/post', methods=('GET',))
def get_posts():
    parsed_args = request.args.to_dict()
    # bar = {k: v.split(',') for k, v in parsed_args.items()}
    tags_raw = request.args.get('tag', '').split(' ')
    titles_raw = request.args.get('title', '').split(' ')
    if not tags_raw or not titles_raw:
        return jsonify({'status': 'failure',
                        'message': 'user didn\'t provide any info'})

    # preprocess input
    tags = [tag.strip() for tag in tags_raw]
    titles = [title.strip() for title in titles_raw if title != '']
    print(tags)
    print(titles)

    query = '''
    SELECT DISTINCT p.id, p.title, p.body, p.created, p.upvotes, p.downvotes, u.username as username, p.author_id
     FROM post p
     JOIN user u ON p.author_id = u.id
     LEFT JOIN post_tags pt ON pt.post_id = p.id
     LEFT JOIN tag t ON pt.tag_id = t.id
     WHERE ({0} OR {1})
     ORDER BY p.created DESC
    '''

    tag_conditions = 't.name IN ({})'.format(','.join(['?'] * len(tags))) if tags else 'FALSE'
    title_conditions = ' OR '.join(['p.title LIKE ?'] * len(titles)) if titles else 'FALSE'

    query = query.format(tag_conditions, title_conditions) 
    params = tags + (['%' + title + '%' for title in titles] if len(titles) > 0 else [])
    print(f'final query: {query}')
    print(f'final params: {params}')
    
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(query, params)
        posts = cur.fetchall()

        tagged_posts = []
        for post in posts:
            post_dict = dict(post)
            tags = get_post_tags(post['id'])
            post_dict['tags'] = tags
            tagged_posts.append(post_dict)
        print(f'posts: {tagged_posts}')
        # result = []/
        # for post in posts:
        #     post_dict = dict(post)
        #     result.append(post_dict)
        return render_template('blog/index.html', posts=tagged_posts)
        # return jsonify({'status': 'success', 
        #                 'posts': result}), 200
    
    except sqlite3.Error as e:
        return jsonify({'status': 'failure',
                        'message': 'failed to get posts'})


