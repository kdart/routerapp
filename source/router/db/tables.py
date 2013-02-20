#!/usr/bin/python2.7
# -*- coding: utf8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

"""
Tables for router management.

typical database:
  create DATABASE router ENCODING 'utf-8' OWNER admin;

"""
from datetime import datetime

from sqlalchemy import *
from router.db.types import *

# default value constructors


def time_now():
    return datetime.now()

def default_obj(x): # call this one in default attribute
    return lambda: x

def default_active():
    return True

def default_inactive():
    return False


metadata = MetaData()


auth_message =  Table('auth_message', metadata,
    Column('id', INTEGER(), primary_key=True, nullable=False),
            Column('user_id', INTEGER(), nullable=False),
            Column('message', TEXT(length=None, convert_unicode=False), nullable=False),
    ForeignKeyConstraint(['user_id'], ['passwd.uid'], name='auth_message_user_id_fkey',
                    onupdate="CASCADE", ondelete="CASCADE"),
    )
Index('index_auth_message_user_id', auth_message.c.user_id, unique=False)


client_session =  Table('client_session', metadata,
    Column('session_key', VARCHAR(length=40, convert_unicode=False), primary_key=True, nullable=False),
            Column('data', JsonText(), nullable=False, default=default_obj({})),
            Column('expire_date', TIMESTAMP(timezone=True), nullable=False),
    )
Index('index_client_session_pkey', client_session.c.session_key, unique=True)


config =  Table('config', metadata,
    Column('id', INTEGER(), primary_key=True, nullable=False),
            Column('name', VARCHAR(length=80, convert_unicode=False), nullable=False),
            Column('value', PickleText(), nullable=True, default=default_obj(None)),
            Column('comment', TEXT(length=None, convert_unicode=False), ),
            Column('parent_id', INTEGER(), ),
            Column('user_id', INTEGER(), ),
        ForeignKeyConstraint(['parent_id'], ['config.id'], name='parent_id_refs_config_id'),
            ForeignKeyConstraint(['user_id'], ['passwd.uid'], name='config_user_id_fkey',
                    onupdate="CASCADE", ondelete="CASCADE"),
    UniqueConstraint("name", "parent_id"),
    )
Index('index_config_name_key', config.c.name, config.c.parent_id, unique=True)
Index('index_config_parent_id', config.c.parent_id, unique=False)
Index('index_config_user_id', config.c.user_id, unique=False)


# compatible columns with libnss-sqlite
#CREATE TABLE passwd(uid INTEGER PRIMARY KEY,
#                    gid INTEGER,
#                    username TEXT NOT NULL,
#                    gecos TEXT NOT NULL default '',
#                    shell TEXT NOT NULL,
#                    homedir TEXT NOT NULL);
#CREATE INDEX idx_passwd_username ON passwd(username);
passwd =  Table('passwd', metadata,
        Column('uid', INTEGER(), primary_key=True, nullable=False), # NSS
        Column('gid', INTEGER(), ForeignKey("groups.gid"), nullable=False), # NSS
        Column('username', TEXT(convert_unicode=True), nullable=False), # NSS
        Column('gecos', TEXT(convert_unicode=True), nullable=False, default=""), # NSS
        Column('shell', TEXT(convert_unicode=True), nullable=False, default="/bin/sh"), # NSS
        Column('homedir', TEXT(convert_unicode=True), nullable=False), # NSS
        Column('password', VARCHAR(length=256, convert_unicode=False), ), # encrypted
        Column('first_name', VARCHAR(length=30, convert_unicode=False), nullable=False),
        Column('middle_name', VARCHAR(length=30, convert_unicode=False), ),
        Column('last_name', VARCHAR(length=30, convert_unicode=False), nullable=False),
        Column('email', VARCHAR(length=80, convert_unicode=False), ),
        Column('is_active', BOOLEAN(), nullable=False, default=default_active),
        Column('is_superuser', BOOLEAN(), nullable=False, default=default_inactive),
        Column('last_login', TIMESTAMP(timezone=True), nullable=False,
                    onupdate=time_now, default=time_now),
    )
Index('index_passwd_username_key', passwd.c.username, unique=True)


#CREATE TABLE groups(gid INTEGER PRIMARY KEY, groupname TEXT NOT NULL, passwd TEXT NOT NULL DEFAULT '');
#CREATE INDEX idx_groupname ON groups(groupname);
groups =  Table('groups', metadata,
        Column('gid', INTEGER(), primary_key=True, nullable=False),
        Column('groupname', TEXT(convert_unicode=True), nullable=False),
        Column('passwd', TEXT(convert_unicode=True), nullable=False, default=""),
    )
Index('idx_groupname', groups.c.groupname, unique=True)


# association table
#CREATE TABLE user_group(uid INTEGER, gid INTEGER, CONSTRAINT pk_user_groups PRIMARY KEY(uid, gid));
#CREATE INDEX idx_ug_uid ON user_group(uid);
#CREATE INDEX idx_ug_gid ON user_group(gid);
user_group =  Table('user_group', metadata,
        Column('uid', INTEGER(), ForeignKey("passwd.uid")),
        Column('gid', INTEGER(), ForeignKey("groups.gid")),
    PrimaryKeyConstraint('uid', 'gid', name="pk_user_groups"),
    )
Index('idx_ug_uid', user_group.c.uid, unique=False)
Index('idx_ug_gid', user_group.c.gid, unique=False)


#interfaces =  Table('interfaces', metadata,
#    Column('id', INTEGER(), primary_key=True, nullable=False),
#            Column('name', VARCHAR(length=64, convert_unicode=False), nullable=False),
#            Column('alias', VARCHAR(length=64, convert_unicode=False)),
#            Column('ifindex', INTEGER(), ),
#            Column('description', TEXT(convert_unicode=False), ),
#            Column('macaddr', MACADDR(), ),
#            Column('vlan', INTEGER(), ),
#            Column('ipaddr', Inet(), ),
#            Column('mtu', INTEGER(), ),
#            Column('speed', INTEGER(), ),
#            Column('status', INTEGER(), ),
#            Column('parent_id', INTEGER(), ),
#        ForeignKeyConstraint(['parent_id'], ['interfaces.id'], name='parent_id_refs_interfaces_id'),
#    )
#Index('index_interfaces_parent_id', interfaces.c.parent_id, unique=False)



# Run this module to create the tables. The user/role/database should
# already be created.
if __name__ == '__main__':
    import sys
    from sqlalchemy import create_engine

    tname = None
    try:
        url = sys.argv[1]
    except IndexError:
        print ("Please supply a database URL.")
        print ("e.g: postgresql://pycopia@localhost/pycopia")
    else:
        db = create_engine(url)
        metadata.bind = db
        if len(sys.argv) > 2:
            for tname in sys.argv[2:]:
                tbl = getattr(sys.modules[__name__], tname)
                print (tbl)
                tbl.drop(checkfirst=True)
                tbl.create()
        else:
            print ("creating tables for", url)
            metadata.create_all()


