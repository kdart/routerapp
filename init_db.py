#!/usr/bin/python2.7
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2009 Keith Dart <keith@dartworks.biz>
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
Place initial values in database.

"""

import sys
import grp

from pycopia import aid

from router.db import models
from router.db import config


#def do_XXX(session):
#    for name, desc, in (
#        ("XXX", "XXX"),
#        ):
#        session.add(models.create(models.XXX, name=name, description=desc))
#    session.commit()


SYSTEMGROUPS = [
    "users",
    "audio",
    "cdrom",
    "games",
    "wheel",
    "dialout",
    "tape",
    "usb",
    "video",
    "cdrw",
    "cron",
    "plugdev",
    "tcpdump",
]


def do_config(session):
    rn = models.create(models.Config, name="root", user=None, parent=None, value=aid.NULL)
    session.add(rn)
    session.commit()
    root = config.Container(session, rn)
    root["logfiledir"] = "/var/log"
    root["documentroot"] = "/var/www/localhost"
    session.commit()

def do_groups(session):
    for gid, name in (
        (1010, "quagga"),
        (1011, "admin"),
        ):
        session.add(models.create(models.Group, groupname=name, gid=gid))
    for grname in SYSTEMGROUPS:
        try:
            grent = grp.getgrnam(grname)
        except KeyError:
            continue
        session.add(models.create(models.Group, groupname=grent.gr_name, gid=grent.gr_gid))
    session.commit()

def do_users(session):
    for username, uid, gid, gecos, homedir, shell, admin, first, last, pw in (
            ("admin", 1001, 1011, "Administrator", "/home/admin", "/usr/bin/vtysh", True, "Admin", "User", "gentoo"),
        ):
        session.add(models.create(
                models.User, username=username, uid=uid, gid=gid, gecos=gecos, is_admin=admin,
                first_name=first, last_name=last, shell=shell, homedir=homedir, password=pw))
    session.commit()

def do_assign(session):
    glist = list(session.query(models.Group).all())
    admin = session.query(models.User).filter(models.User.username=="admin").one()
    admin.groups = glist
    session.commit()

def init_database(argv):
    try:
        url = argv[1]
    except IndexError:
        from pycopia import basicconfig
        cf = basicconfig.get_config("database.conf")
        url = cf["DATABASE_URL"]
    Maker = models.create_session(url)
    dbsession = Maker()
    try:
        do_config(dbsession)
        do_groups(dbsession)
        do_users(dbsession)
        do_assign(dbsession)
    finally:
        dbsession.close()

if __name__ == "__main__":
    init_database(sys.argv)

