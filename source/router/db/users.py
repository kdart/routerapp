#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012- Keith Dart <keith@dartworks.biz>
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

"""
User management. Create and update users. Expects the nss-sqlite module to be installed.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import sys
import crypt
import sqlite3

from pycopia import getopt
from pycopia import tty
from pycopia import passwd
from pycopia import sysrandom
from pycopia import cliutils

from router.db import models

SHADOWDB = "/var/db/shadow.sqlite"


SALTCHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./"

def get_salt(n):
    return "".join([sysrandom.choice(SALTCHARS) for i in range(n)])

def get_hash(pw, salt=None):
    if salt is None:
        salt = get_salt(16)
    return crypt.crypt(pw, "$6${}$".format(salt)) # SHA512 hash plus random salt


def new_shadow(name, password):
    pwhash = get_hash(password)
    conn = sqlite3.connect(SHADOWDB)
    c = conn.cursor()
    c.execute("INSERT INTO shadow VALUES (?, ?)", (name, pwhash))
    conn.commit()
    conn.close()

def update_shadow(name, password):
    pwhash = get_hash(password)
    conn = sqlite3.connect(SHADOWDB)
    c = conn.cursor()
    c.execute("UPDATE shadow SET passwd=? WHERE username=?", (pwhash, name))
    conn.commit()
    conn.close()

def delete_shadow(name):
    conn = sqlite3.connect(SHADOWDB)
    c = conn.cursor()
    c.execute("DELETE FROM shadow WHERE username=?", (name,))
    conn.commit()
    conn.close()


def ask_password():
    password = tty.getpass("Password? ")
    password2 = tty.getpass("Again: ")
    if password != password2:
        return None
    return password


def newuser(argv):
    """Create a new user
    newuser [<longopts>] <username>

    Where options are:
        --first_name=<firstname>
        --last_name=<lastname>
        --password=<newpass>
        --shell=<shell>
        --home=<home>
    You will be prompted for missing information.

    """
    try:
        opts, longopts, args = getopt.getopt(argv[1:], "h?")
    except getopt.GetoptError:
        print (newuser.__doc__)
        return
    for opt, optarg in opts:
        if opt in ("-?", "-h"):
            print (newuser.__doc__)
            return

    try:
        username = args[0]
    except IndexError:
        username = cliutils.get_input("Account name? ")

    try:
        pwent = passwd.getpwnam(username)
    except KeyError:
        pass
    else:
        print("User already exists, exiting.", file=sys.stderr)
        return

    password = longopts.get("password")
    if not password:
        password = ask_password()
        if not password:
            print("Passwords do not match, exiting.", file=sys.stderr)
            return

    # Get maximum UID value from passwd and database, not including system ones.
    uidl = [pwe.uid for pwe in passwd.getpwall() if pwe.uid < 10000]
    dblist = [u.uid for u in models.dbsession.query(models.User).all()]
    uidl.extend(dblist)
    uid = max(uidl)+1

    first_name = longopts.get("first_name")
    if not first_name:
        first_name = cliutils.get_input("First Name? ")
    last_name = longopts.get("last_name")
    if not last_name:
        last_name = cliutils.get_input("Last Name? ")

    gecos = "{}, {}".format(last_name, first_name)

    shell = longopts.get("shell")
    if not shell:
        shell = cliutils.get_input("Shell? ", default="/bin/sh")

    home = longopts.get("home")
    if not home:
        home = cliutils.get_input("Homedir? ", default="/home/{}".format(username))

    email = longopts.get("email")
    if not email:
        email = cliutils.get_input("Email? ")

    primary_grp = models.dbsession.query(models.Group).filter(models.Group.groupname=="users").one()
    glist = models.dbsession.query(models.Group).all()
    glist.remove(primary_grp)
    sup_groups = cliutils.choose_multiple(glist, prompt="Extra groups?")

    superuser = cliutils.yes_no("Is admin?")

    user = models.create(models.User,
            username=username,
            uid=uid,
            gid=primary_grp.gid,
            gecos=gecos,
            first_name=first_name,
            last_name=last_name,
            shell=shell,
            homedir=home,
            email=email,
            is_superuser=superuser,
            is_active=True)
    user.password = password
    models.dbsession.add(user)
    models.dbsession.commit()
    user.groups = sup_groups
    models.dbsession.commit()
    new_shadow(username, password)
    return user


def newpass(argv):
    """Change a users' password.
    newpass [--password=<newpass>] <username>
    """
    try:
        opts, longopts, args = getopt.getopt(argv[1:], "h?")
    except getopt.GetoptError:
        print (newpass.__doc__)
        return
    for opt, optarg in opts:
        if opt in ("-?", "-h"):
            print (newpass.__doc__)
            return
    try:
        username = args[0]
    except IndexError:
        username = cliutils.get_input("Account name? ")

    password = longopts.get("password")
    if not password:
        password = ask_password()
        if not password:
            print("Passwords do not match, exiting.", file=sys.stderr)
            return

    user = models.query(models.User, username=username).one()
    user.password = password
    models.commit()
    update_shadow(username, password)

def deleteuser(argv):
    """Delete a user
    deleteuser <username>
    """
    try:
        opts, longopts, args = getopt.getopt(argv[1:], "h?")
    except getopt.GetoptError:
        print (deleteuser.__doc__)
        return
    for opt, optarg in opts:
        if opt in ("-?", "-h"):
            print (deleteuser.__doc__)
            return
    try:
        username = args[0]
    except IndexError:
        username = cliutils.get_input("Account name? ")

    user = models.query(models.User, username=username).one()
    models.delete(user)
    models.close()
    delete_shadow(username)

