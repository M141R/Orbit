import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional
from flask_login import UserMixin
from datetime import datetime
from dicebear import Avatar, Style
from importlib.resources import files
from . import db

class User(UserMixin,db.Model):
    user_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email : so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    def __repr__(self):
        return '<User {}>'.format(self.username)
    def get_id(self):
        return str(self.user_id)
    @property
    def avatar(self):
        return f"https://api.dicebear.com/9.x/lorelei/svg?seed={self.username}"

class Groups(db.Model):
    group_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True)
    desc: so.Mapped[str] = so.mapped_column(sa.String(120))
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now)
    created_by: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.user_id))
    creator: so.Mapped['User'] = so.relationship()
    slug: so.Mapped[str] = so.mapped_column(sa.String(45))

class Group_members(db.Model):
    user_id : so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.user_id), primary_key=True)
    group_id : so.Mapped[int] = so.mapped_column(sa.ForeignKey(Groups.group_id), primary_key=True)
    joined_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now)
    role: so.Mapped[str] = so.mapped_column(sa.String(25),default="member")

class Channel(db.Model):
    channel_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_by: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.user_id))
    name: so.Mapped[str] = so.mapped_column(sa.String(35), unique=True)
    group_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Groups.group_id))
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now)
    group: so.Mapped['Groups'] = so.relationship()
    creator: so.Mapped['User'] = so.relationship()
    slug: so.Mapped[str] = so.mapped_column(sa.String(45))
    
class Message(db.Model):
    message_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.String(500))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.user_id))
    channel_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Channel.channel_id))
    timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now)
    sender: so.Mapped['User'] = so.relationship()
    room: so.Mapped['Channel'] = so.relationship()

class Access_Request(db.Model):
    access_id : so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id : so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.user_id))
    group_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Groups.group_id))
    timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now)
    status: so.Mapped[str] = so.mapped_column(sa.String(25), default="pending")
    user: so.Mapped['User'] = so.relationship()
    group: so.Mapped['Groups'] = so.relationship()