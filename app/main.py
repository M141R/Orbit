from flask import Flask,render_template,url_for,request,redirect, Blueprint, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required,current_user
from flask_migrate import Migrate
from datetime import datetime
from .models import User,Groups, Group_members,Channel, Message, Access_Request
from flask_socketio import SocketIO,emit,join_room,leave_room,disconnect
from importlib.resources import files
from sqlalchemy.orm import joinedload
from dicebear import Avatar, Style
from . import db
from app import socketio

app = Blueprint('main',__name__)

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", name=current_user.username)

@app.route("/groups")
@login_required
def groups():
    groups = db.session.scalars(db.select(Groups).order_by(Groups.group_id.desc())).all()
    return render_template("group/groups.html",groups=groups)

@app.route("/new-group", methods=['POST'])
@login_required
def new_group():
    name = request.form.get('Name')
    desc = request.form.get('Desc')
    created_at = datetime.now()
    created_by = current_user.user_id
    slug = name.lower().replace(" ", "-")

    new_group=Groups(name=name,desc=desc,created_at=created_at,created_by=created_by,slug=slug)
    db.session.add(new_group)
    db.session.flush()
    user_admin= Group_members(role="admin",user_id=current_user.user_id, group_id=new_group.group_id)
    db.session.add(user_admin)
    db.session.commit()
    return redirect(url_for('main.group',group_slug=slug))

@app.route("/new-station-modal")
@login_required
def new_group_modal():
    return render_template("components/new_group_modal.html")

@app.route("/group/<string:group_slug>")
@login_required
def group(group_slug):
    group = db.session.scalar(db.select(Groups).filter(Groups.slug == group_slug))
    if not group:
        return "Group not found", 404
    channels = db.session.scalars(db.select(Channel).where(Channel.group_id == group.group_id))

    membership = db.session.scalar(db.select(Group_members).where(Group_members.user_id == current_user.user_id, Group_members.group_id == group.group_id))

    if membership:
        return render_template("group/group.html", group=group,channels=channels)
    else:
        current_status = db.session.scalar(db.select(Access_Request.status).where(Access_Request.user_id == current_user.user_id, Access_Request.group_id == group.group_id))
        if current_status:
            if current_status == 'pending':
                flash('Your access request is pending')
                return redirect(url_for('main.groups'))
            elif current_status.status == 'rejected':
                flash('Your request was rejected')
                return redirect(url_for('main.groups'))
        else:
            return redirect(url_for('main.groups')) 
        
        

@app.route("/group/<int:group_id>/new-channel", methods=['POST'])
@login_required
def new_channel(group_id):
    input_channel_name = request.form.get('channelname')
    created_by = current_user.user_id
    created_at = datetime.now()
    slug = input_channel_name.lower().replace(" ", "-")
    new_room = Channel(name=input_channel_name, group_id=group_id, created_by=created_by, created_at=created_at,slug=slug)
    db.session.add(new_room)
    db.session.commit()
    current_group = db.session.scalar(db.select(Groups).where(Groups.group_id == group_id))
    return redirect(url_for('main.group',group_slug=current_group.slug))

@app.route("/group/<int:group_id>/new-channel-modal")
@login_required
def new_channel_modal(group_id):
    return render_template("components/new_channel_modal.html", group_id=group_id)

@app.route("/<string:group_slug>/<string:channel_slug>")
@login_required
def channel(group_slug,channel_slug):
    current_group = db.session.scalar(db.select(Groups).filter(Groups.slug == group_slug))
    
    if not current_group:
        return "Room not found", 404
        
    current_channel = db.session.scalar(db.select(Channel).where(Channel.group_id == current_group.group_id, Channel.slug == channel_slug ))
    
    if not current_channel:
        return "Room not found", 404

    messages = db.session.scalars(db.select(Message).filter(Message.channel_id == current_channel.channel_id).options(joinedload(Message.sender)).order_by(Message.timestamp.asc())).all()

    if 'HX-REQUEST' in request.headers:
        return render_template("components/chatbox.html",group=current_group, channel=current_channel, messages=messages)

    return render_template("group/group.html", group=current_group, channel=current_channel, messages=messages)

@app.route("/group/<string:group_slug>/admin")
@login_required
def group_admin(group_slug):
    current_group = db.session.scalar(db.select(Groups).filter(Groups.slug == group_slug))

    if not current_group:
        return "Room not found", 404
    
    check_admin = db.session.scalar(db.select(Group_members).where(Group_members.group_id == current_group.group_id, Group_members.user_id == current_user.user_id))

    if not check_admin:
        flash('You are not the admin of this group')
        return redirect(url_for('main.groups'))
    if check_admin.role == 'admin':
        pending_requests = db.session.scalars(db.select(Access_Request).where(Access_Request.group_id == current_group.group_id, Access_Request.status == 'pending')).all()
        return render_template('group/groupadmin.html',requests=pending_requests,group=current_group)
    
@app.route("/group/<int:group_id>/request-access",methods=["POST"])
@login_required
def group_request(group_id):
    group = db.session.scalar(db.select(Groups).where(Groups.group_id == group_id))
    membership = db.session.scalar(db.select(Group_members).where(Group_members.user_id == current_user.user_id, Group_members.group_id == group_id))
    if membership:
        return redirect(url_for('main.group',group_slug=group.slug))
    else:
        new_request = Access_Request(user_id=current_user.user_id, group_id=group_id)
        db.session.add(new_request)
        db.session.commit()
        flash("Your request to join the group has been sent!")
        return redirect(url_for('main.groups'))
    
@app.route("/group/<string:group_slug>/access", methods=["POST"])
@login_required
def access(group_slug):
    current_group = db.session.scalar(db.select(Groups).filter(Groups.slug == group_slug))
    access_id = request.form.get('access_id')
    action = request.form.get('action')
    get_details = db.session.scalar(db.select(Access_Request).where(Access_Request.access_id == access_id))

    if action == 'approve':
        new_member = Group_members(user_id=get_details.user_id,group_id=current_group.group_id)
        db.session.add(new_member)
    remove_request = db.session.get(Access_Request, access_id)
    db.session.delete(remove_request)
    db.session.commit()
    return redirect(url_for("main.group_admin",group_slug=current_group.slug))

@app.context_processor
def inject_user_groups():
    if current_user.is_authenticated:
        my_groups = db.session.scalars(
            db.select(Groups)
            .join(Group_members)
            .where(Group_members.user_id == current_user.user_id)
        ).all()
        
        return dict(my_groups=my_groups)
    
    return dict(my_groups=[])

@socketio.event
def connect():
    if not current_user.is_authenticated:
        disconnect()

@socketio.on('join_channel')
def handle_join_channel(data):
    channel_id = data["channel_id"]
    join_room(str(channel_id))

@socketio.on('send_message')
def handle_send_message(data):
    message = data["message"]
    channel = data["channel_id"]
    

    new_message = Message(content = message,channel_id=int(channel),user_id=current_user.user_id )
    db.session.add(new_message)
    db.session.commit()

    emit(
        "receive_message" ,
        {
            'content' : message,
            'user' : current_user.username,
            'timestamp': datetime.now().strftime("%I:%M %p"),
            'avatar' : current_user.avatar
        },
        to=str(channel)
    )

@socketio.on('leave_channel')
def handle_leave_channel(data):
    channel_id = data["channel_id"]
    leave_room(str(channel_id))