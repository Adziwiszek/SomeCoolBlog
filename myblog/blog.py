from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,
    jsonify
)
from werkzeug.exceptions import abort
# from flask_wtf.csrf import generate_csrf
from myblog.auth import login_required
from myblog.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, upvotes, downvotes'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
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
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
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

    return post

def get_posts_comments(post_id):
    comments = get_db().execute(
        'SELECT c.id, c.body, c.created, u.username'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' WHERE c.post_id = ?'
        ' ORDER BY created DESC',
        (post_id,)
    ).fetchall()

    if comments is None:
        print(f"Post {post_id} has no comments")
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

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
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
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/read', methods=('GET', 'POST'))
def read(id):
    post = get_post(id, False)
    db = get_db()
    comments = db.execute(
        'SELECT c.id, c.body, c.created, u.username FROM comment c JOIN user u ON c.author_id = u.id WHERE c.post_id = ? ORDER BY c.created DESC',
        (id,)
    ).fetchall()
    return render_template('blog/read.html', post=post  , comments=comments)

@bp.route('/<int:id>/receive', methods=('POST', 'GET'))
def receive_message(id):
    comments = get_posts_comments(id)
    return comments

@bp.route('/send', methods=['POST'])
@login_required
def send_message():
    if request.method == 'POST':
        data = request.json

        message = data['message']
        postID = data['postID']
        error = None

        if not message:
            error = 'Message is required.'

        if error is not None:
            flash(error)
        else:
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
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'SELECT downvotes FROM post'
        ' WHERE id = ?',
        (id,)
    )
    result = cur.fetchone()

    if result is None:
        return jsonify({'status': 'failure',
                    'votes': -1})
    
    cur.execute(
        'UPDATE post SET downvotes = ?'
        ' WHERE id = ?',
        (result['downvotes'] + 1, id)
    )
    db.commit()

    return jsonify({'status': 'success',
                    'votes': result['downvotes'] + 1}) 
    

@bp.route('/<int:id>/upvote', methods=('POST',))
def upvote(id):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'SELECT upvotes FROM post'
        ' WHERE id = ?',
        (id,)
    )
    result = cur.fetchone()

    if result is None:
        return jsonify({'status': 'failure',
                    'votes': -1})
    
    cur.execute(
        'UPDATE post SET upvotes = ?'
        ' WHERE id = ?',
        (result['upvotes'] + 1, id)
    )
    db.commit()

    return jsonify({'status': 'success',
                    'votes': result['upvotes'] + 1})    

    
# Make sure to set a secret key for your app
# app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure random key