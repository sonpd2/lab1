# -*- coding: utf-8 -*-
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify, abort, send_file
from flask_login import current_user, login_required
from flask_babel import _
import sys, os
from app import db
from app.main.forms import EditProfileForm, PostForm, MessageForm, ChangePassForm, CreateUserForm, \
    CommentForm, MessageEditForm, AnswerForm
from app.models import User, Post, Message, Notification, Comment
from app.main import bp
from sqlalchemy import or_, and_
from werkzeug.utils import secure_filename
import os
import random
import string
import hashlib
from app import current_app
import traceback
import unicodedata
import re

def convert_file_name_to_standard(file_name):
    file_name = file_name.replace(".txt", "")
    file_name = ' '.join(file_name.split("_"))
    file_name = file_name.encode('utf-8').decode()
    file_name = re.sub(u'Đ', 'D', file_name)
    file_name = re.sub(u'đ', 'd', file_name)
    file_name = unicodedata.normalize('NFKD', file_name).encode('ASCII', 'ignore')

    return hashlib.md5(file_name).hexdigest()


def get_random_string_and_hash(length, filename):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    output = hashlib.md5((result_str + "_" + filename).encode('utf-8')).hexdigest()
    return output

def save_file(attach_file, is_challenge):
    try:
        if is_challenge == 0:
            attach_file_name = secure_filename(attach_file.filename)
        elif is_challenge == 1:
            attach_file_name = convert_file_name_to_standard(secure_filename(attach_file.filename))

        cwd = os.path.join(current_app.root_path, current_app.config.get('UPLOAD_FOLDER'), current_user.username)
        if not os.path.exists(cwd):
            os.mkdir(cwd)

        attach_file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER'), current_user.username, get_random_string_and_hash(10, attach_file_name))
        attach_file_full_path = os.path.join(current_app.root_path, attach_file_path)
        attach_file.save(attach_file_full_path)
        return attach_file_name, attach_file_path
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log = ''.join('!! ' + line for line in lines)  # Log it or whatever here
        print(log)
        return None, None

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()

    if form.validate_on_submit():

        post = Post(body=form.post.data, author=current_user, privacy=form.privacy.data, is_challenge=form.is_challenge.data)

        if form.attach_file.data is not None:
            attach_file = form.attach_file.data
            attach_file_name, attach_file_path = save_file(attach_file, form.is_challenge.data)
            if attach_file_name is not None and attach_file_path is not None:
                post.file_name = attach_file_name
                post.file_path = attach_file_path

        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))

    return render_template('index.html', title=_('Home'), form=form)

@bp.route('/challenge', methods=['GET', 'POST'])
@login_required
def challenge():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter(and_(Post.privacy == 0, Post.is_challenge == 1)).order_by(
        Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None

    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        post = Post.query.filter(Post.id == comment_form.post_id.data,
                                 or_(Post.privacy == 0, Post.user_id == current_user.id)).first_or_404()
        if post is not None:
            comment = Comment(user_id=current_user.id, post_id=post.id,
                              body=comment_form.body.data)

            if comment_form.attach_file.data is not None:
                attach_file = comment_form.attach_file.data
                attach_file_name, attach_file_path = save_file(attach_file)
                if attach_file_name is not None and attach_file_path is not None:
                    comment.file_name = attach_file_name
                    comment.file_path = attach_file_path

            db.session.add(comment)
            db.session.commit()
            flash(_('Your comment is now live!'))
            return redirect(url_for('main.explore'))
        else:
            return abort(403)

    return render_template('challenge/index.html', title=_('Challenge'),posts=posts.items, next_url=next_url, comment_form=comment_form, prev_url=prev_url)

# @bp.route('/challenge/<id>', methods = ['POST'])
# @login_required
# def check_result_of_challenage(id):
#     if "answer" in request.json:
#         answer = request.json.get("answer")
#         challenge = Post.query.filter(and_(Post.id == id, Post.is_challenge == 1, Post.privacy == 0)).first_or_404()
#
#         if hashlib.md5(answer).hexdigest() == challenge.file_name:
#             attach_file_full_path = os.path.join(current_app.root_path, challenge.file_path)
#             with open(attach_file_full_path) as file:
#                 file_content = file.read()
#             return jsonify({'status':'ok','data':file_content})
#         else:
#             return jsonify({'status':'nok','info':'Wrong answer.'})
#     else:
#         return jsonify({'status':'nok','info':'Wrong request.'})

@bp.route('/challenge/<id>', methods = ['GET','POST'])
@login_required
def check_result_of_challenage(id):
    post = Post.query.filter(and_(Post.id == id, Post.is_challenge == 1, Post.privacy == 0)).first_or_404()
    answer_form = AnswerForm()
    if answer_form.validate_on_submit():
        comment = Comment(user_id=current_user.id, post_id=post.id, body=answer_form.answer.data)
        db.session.add(comment)
        db.session.commit()
        if hashlib.md5(answer_form.answer.data.encode('utf-8')).hexdigest() == post.file_name:
            attach_file_full_path = os.path.join(current_app.root_path, post.file_path)
            with open(attach_file_full_path) as file:
                file_content = file.read()
                info = {'status':'ok','data':file_content, 'answer':answer_form.answer.data}
                flash("Congratulations, you have correct answer!")
                return render_template('challenge/view_detail_challenge.html', title=_('Challenge'), post=post, info=info)
        else:
            flash('Wrong answer.')
            return redirect(url_for('main.check_result_of_challenage', id =id))
    elif request.method == 'GET':
        return render_template('challenge/view_detail_challenge.html', title=_('Challenge'), post=post, answer_form=answer_form)


@bp.route('/download_file/post/<file_name>', methods = ['GET','POST'])
@login_required
def download_file_from_post(file_name):
    post = Post.query.filter(and_(Post.is_challenge == 0, Post.file_name == file_name, or_(Post.privacy == 0, Post.user_id == current_user.id))).first_or_404()

    try:
        attach_file_full_path = os.path.join(current_app.root_path, post.file_path)
        return send_file(attach_file_full_path, attachment_filename=file_name, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@bp.route('/download_file/comment/<file_name>', methods=['GET', 'POST'])
@login_required
def download_file_from_comment(file_name):
    comment = Comment.query.filter(and_(Comment.file_name == file_name, or_(Post.user_id == current_user.id, Comment.user_id == current_user.id))).first_or_404()

    try:
        attach_file_full_path = os.path.join(current_app.root_path, comment.file_path)
        return send_file(attach_file_full_path, attachment_filename=file_name, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@bp.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter( and_(Post.privacy == 0, Post.is_challenge ==0)).order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None

    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        post = Post.query.filter(Post.id == comment_form.post_id.data, or_(Post.privacy == 0, Post.user_id == current_user.id)).first_or_404()
        if post is not None:
            comment = Comment(user_id = current_user.id, post_id = post.id, body = comment_form.body.data)

            if comment_form.attach_file.data is not None:
                attach_file = comment_form.attach_file.data
                attach_file_name, attach_file_path = save_file(attach_file)
                if attach_file_name is not None and attach_file_path is not None:
                    comment.file_name = attach_file_name
                    comment.file_path = attach_file_path

            db.session.add(comment)
            db.session.commit()
            flash(_('Your comment is now live!'))
            return redirect(url_for('main.explore'))
        else:
            return abort(403)

    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url, comment_form=comment_form,
                           prev_url=prev_url)


@bp.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)

    posts = user.posts.filter(
        or_(Post.user_id == current_user.id, and_(Post.privacy == 0, Post.user_id == user.id, Post.is_challenge == 0))).order_by(
        Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None

    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        post = Post.query.filter(Post.id == comment_form.post_id.data,or_(Post.privacy == 0, Post.user_id == current_user.id)).first()
        if post is not None:
            comment = Comment(user_id=current_user.id, post_id=comment_form.post_id.data, body=comment_form.body.data)
            if comment_form.attach_file.data is not None:
                attach_file = comment_form.attach_file.data
                attach_file_name, attach_file_path = save_file(attach_file)
                if attach_file_name is not None and attach_file_path is not None:
                    comment.file_name = attach_file_name
                    comment.file_path = attach_file_path

            db.session.add(comment)
            db.session.commit()
            flash(_('Your comment is now live!'))
            return redirect(url_for('main.user',username=username))
        else:
            abort(403)

    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, comment_form=comment_form, prev_url=prev_url)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)


@bp.route('/change_pass', methods=['GET', 'POST'])
@login_required
def change_pass():
    form = ChangePassForm(current_user.username)
    if form.validate_on_submit():
        current_user.set_password(form.password1.data)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.change_pass'))

    return render_template('change_pass.html', title=_('Change Password'), form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))

    elif request.method == 'GET':
        form.email.data = current_user.email
        form.name.data = current_user.name
        form.phone_number.data = current_user.phone_number
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('main.user', username=username))

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/edit_message/<id>', methods = ['GET','POST'])
@login_required
def edit_message(id):
    form_edit_message = MessageEditForm(id)
    messages = Message.query.filter(and_(Message.id == id, Message.sender_id == current_user.id)).first_or_404()
    recipient_user = User.query.filter_by(id = messages.recipient_id).first()
    if form_edit_message.validate_on_submit():
        if form_edit_message.submit_delete_message.data:
            db.session.delete(messages)
            db.session.commit()
            flash('Delete success')
            return redirect(url_for('main.view_messages_detail', username=recipient_user.username))
        elif form_edit_message.submit_change_message.data:
            messages.body = form_edit_message.body.data
            db.session.commit()
            flash('Change success')
            return redirect(url_for('main.edit_message', id=id))
    elif request.method == 'GET':
        form_edit_message.recipient.data = recipient_user.username
        form_edit_message.send_date.data = messages.timestamp
        form_edit_message.body.data = messages.body

    return render_template('edit_message.html', form_edit_message=form_edit_message)

@bp.route('/conversation')
@login_required
def conversation():
    conversations = Message.query.with_entities(Message.sender_id, Message.recipient_id).filter(or_(Message.recipient_id == current_user.id, Message.sender_id == current_user.id)).distinct().all()
    user_ids = []
    for conversation in conversations:
        if conversation.sender_id != current_user.id:
            user_ids.append(conversation.sender_id)
        if conversation.recipient_id != current_user.id:
            user_ids.append(conversation.recipient_id)

    user_ids = list(dict.fromkeys(user_ids))

    users = User.query.filter(User.id.in_(user_ids)).all()
    return render_template('conversation.html', users=users)

@bp.route('/view_messages_detail/<username>', methods = ['GET','POST'])
@login_required
def view_messages_detail(username):
    user = User.query.filter_by(username = username).first_or_404()
    messages = Message.query.filter(and_( or_(Message.recipient_id == current_user.id, Message.sender_id == current_user.id), or_(Message.sender_id == user.id, Message.recipient_id == user.id))).order_by(Message.timestamp.asc()).all()

    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.view_messages_detail', username=username))

    return render_template('view_messages_detail.html', messages=messages, form=form, recipient=username)

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])

@login_required
@bp.route('/create_user', methods=['GET', 'POST'])
def create_account():
    if not current_user.is_admin:
        return abort(403)

    form = CreateUserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, is_admin=form.is_admin.data, name= form.name.data, phone_number = form.phone_number.data, is_active = form.is_active.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))

    return render_template('auth/create_user.html', title=_('Create User'), form=form)
