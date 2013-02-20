#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab
#
#    Copyright (C) 2012  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

"""
Defines database ORM objects.

"""
import sys

from datetime import timedelta
from hashlib import sha1

from Crypto.Cipher import AES

from sqlalchemy import create_engine, and_, or_, not_, func, exists
from sqlalchemy.orm import sessionmaker, mapper, relationship, backref, synonym
from sqlalchemy.orm.exc import NoResultFound

from pycopia import basicconfig
from pycopia.aid import hexdigest, unhexdigest, NULL

from router.db import tables


class ModelError(Exception):
    """Raised when something doesn't make sense for this model"""
    pass


class ModelAttributeError(ModelError):
    """Raised for errors related to models with attributes."""
    pass


def create_session(url=None):
    if url is None:
        cf = basicconfig.get_config("database.conf")
        url = cf["DATABASE_URL"]
    db = create_engine(url)
    tables.metadata.bind = db
    return sessionmaker(bind=db, autoflush=False)

SessionMaker = create_session()

class _Session_builder(object):

    def __getattr__(self, name):
        global dbsession
        if isinstance(dbsession, _Session_builder):
            dbsession = SessionMaker()
        return getattr(dbsession, name)

dbsession = _Session_builder()

def commit():
    dbsession.commit()

def rollback():
    dbsession.rollback()

def close():
    global dbsession
    if not isinstance(dbsession, _Session_builder):
        dbsession.close()
        dbsession = _Session_builder()


# Due to the way sqlalchemy instruments attributes you cannot instantiate
# new model objects in the usual way. Use this general factory function instead.
def create(klass, **kwargs):
    inst = klass()
    for k, v in kwargs.items():
        setattr(inst, k, v)
    return inst

def update(inst, **kwargs):
    for k, v in kwargs.items():
        setattr(inst, k, v)

def delete(inst):
    dbsession.delete(inst)
    dbsession.commit()

def query(klass, **kwargs):
     q = dbsession.query(klass)
     if kwargs:
         for name, value in kwargs.items():
            q = q.filter(getattr(klass, name)==value)
     return q


# Set password encryption key for the site.
SECRET_KEY = None
def _get_secret():
    global SECRET_KEY
    try:
        cf = basicconfig.get_config("auth.conf")
    except basicconfig.ConfigReadError:
        raise ModelError("No auth.conf config file found.")
    else:
        SECRET_KEY = cf.SECRET_KEY

def get_key():
    global SECRET_KEY, _get_secret
    if SECRET_KEY is None:
        _get_secret()
        del _get_secret
        h = sha1()
        h.update(SECRET_KEY)
        h.update("IfucnrdthsUrtooCls")
        SECRET_KEY = h.digest()[:16]
    return SECRET_KEY


class Group(object):
    ROW_DISPLAY = ("groupname", "gid")

    def __str__(self):
        return "%s(%s)" % (self.groupname, self.gid)

mapper(Group, tables.groups)


class User(object):
    ROW_DISPLAY = ("username", "uid", "first_name", "last_name", "email")

    def __str__(self):
        return "%s %s (%s)" % (self.first_name, self.last_name, self.username)

    def __repr__(self):
        return "User(%r, %r, %r)" % (self.username, self.first_name, self.last_name)

    # Passwords are stored in the database encrypted.
    def _set_password(self, passwd):
        eng = AES.new(get_key(), AES.MODE_ECB)
        self._password = hexdigest(eng.encrypt((passwd + b"\0"*(16 - len(passwd)))[:16]))

    def _get_password(self):
        eng = AES.new(get_key(), AES.MODE_ECB)
        return eng.decrypt(unhexdigest(self._password.encode("ascii"))).strip(b"\0")

    password = property(_get_password, _set_password)

    def set_last_login(self):
            self.last_login = tables.time_now()

    def get_session_key(self):
        h = sha1()
        h.update(str(self.uid))
        h.update(self.username)
        h.update(str(self.last_login))
        return h.hexdigest()

    @classmethod
    def get_by_username(cls, username):
        return dbsession.query(cls).filter(cls.username==username).first()

    @property
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)


mapper(User, tables.passwd,
    properties={
        "password": synonym('_password', map_column=True),
        "groups": relationship(Group,
            secondary=tables.user_group,
            primaryjoin=tables.passwd.c.uid==tables.user_group.c.uid,
            secondaryjoin=tables.user_group.c.gid==tables.groups.c.gid,
            single_parent=True,
            cascade="all, delete, delete-orphan",
            ),
    })


class UserMessage(object):
    ROW_DISPLAY = ("user", "message")

    def __unicode__(self):
        return unicode(self.message)

    def __str__(self):
        return "%s: %s" % (self.user, self.message)

mapper(UserMessage, tables.auth_message,
    properties={
        "user": relationship(User, backref=backref("messages",
                    cascade="all, delete, delete-orphan")),
    }
)

class Session(object):
    ROW_DISPLAY = ("username",)
    def __init__(self, user, lifetime=48):
        self.session_key = user.get_session_key()
        self.expire_date = user.last_login + timedelta(hours=lifetime)
        self.data = { "username": user.username }

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        d = self.data
        d[key] = value
        self.data = d

    def __delitem__(self, key):
        d = self.data
        del d[key]
        self.data = d

    def __str__(self):
        return "key: %s: Expires: %s" % (self.session_key, self.expire_date)

    def is_expired(self):
        return tables.time_now() >= self.expire_date

    @classmethod
    def get_expired(cls, session):
        return session.query(cls).filter(cls.expire_date < "now").order_by(cls.expire_date)

    @classmethod
    def clean(cls, session):
        for sess in session.query(cls).filter(cls.expire_date < "now"):
            session.delete(sess)
        session.commit()

mapper(Session, tables.client_session)


#class Interface(object):
#    ROW_DISPLAY = ("ifindex", "name", "macaddr", "ipaddr")

#    def __str__(self):
#        return "%s (%s)" % (self.name, self.ipaddr)

#    def __str__(self):
#        extra = []
#        if self.ipaddr is not None:
#            extra.append(unicode(self.ipaddr.CIDR))
#        if self.macaddr is not None:
#            extra.append(unicode(self.macaddr))
#        if extra:
#            return "%s (%s)" % (self.name, ", ".join(extra))
#        else:
#            return self.name

#    def __repr__(self):
#        return "Interface(%r, ipaddr=%r)" % (self.name, self.ipaddr)

#    def create_subinterface(self, session, subname):
#        intf = create(Interface, name=self.name+subname, ifindex=0,
#                interface_type=self.interface_type, parent=self)
#        session.add(intf)
#        session.commit()

#    @classmethod
#    def select_unattached(cls, session):
#        return session.query(cls).filter(cls.equipment == None).order_by(cls.ipaddr)


#mapper(Interface, tables.interfaces,
#    properties = {
#        "subinterfaces": relationship(Interface,
#                backref=backref('parent', remote_side=[tables.interfaces.c.id])),
#    }
#)


#######################################
# configuration data. This models a hierarchical storage structures. It
# should be updated with the pycopia.db.config wrapper objects.

class Config(object):
    ROW_DISPLAY = ("name", "value", "user")

    def __str__(self):
        if self.value is NULL:
            return "[%s]" % self.name
        else:
            return "%s=%r" % (self.name, self.value)

    def __repr__(self):
        return "Config(%r, %r)" % (self.name, self.value)

    def set_owner(self, session, user):
        if self.container is not None:
            if isinstance(user, basestring):
                user = User.get_by_username(session, user)
            self.user = user
            session.commit()

    def get_child(self, session, name):
        session.query(Config).filter

        q = session.query(Config).filter(and_( Config.container==self, Config.name==name))
        try:
            return q.one()
        except NoResultFound:
            raise ModelError("No sub-node %r set." % (name,))


mapper(Config, tables.config,
    properties={
        'children': relationship(Config, cascade="all",
            backref=backref("container",
                    remote_side=[tables.config.c.id, tables.config.c.user_id])),
        'user': relationship(User),
    }
)


def get_rowdisplay(class_):
    return getattr(class_, "ROW_DISPLAY", ["id"])


if __name__ == "__main__":
    import os
    from pycopia import autodebug
    if sys.flags.interactive:
        from pycopia import interactive

    for user in dbsession.query(User).all():
        print(user, user.groups)
    close()
