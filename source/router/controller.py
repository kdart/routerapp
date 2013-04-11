#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2013- Keith Dart <keith@dartworks.biz>
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
Manage interfaces via the quagga tools.

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from pycopia import aid
from pycopia import ipv4
from pycopia import proctools

from router.db import models

import sys

#Interface dummy0 is down
#  pseudo interface
#Interface eth0 is up, line protocol detection is disabled
#  index 2 metric 1 mtu 1500 
#  flags: <UP,BROADCAST,RUNNING,MULTICAST>
#  HWaddr: 00:0c:29:fc:b2:5d
#  inet 192.168.1.21/24 broadcast 192.168.1.255
#  inet6 fe80::20c:29ff:fefc:b25d/64
#Interface eth1 is up, line protocol detection is disabled
#  index 3 metric 1 mtu 1500 
#  flags: <UP,BROADCAST,RUNNING,MULTICAST>
#  HWaddr: 00:0c:29:fc:b2:67
#  inet 169.254.114.84/16 broadcast 169.254.255.255
#  inet6 fe80::20c:29ff:fefc:b267/64
#Interface eth2 is up, line protocol detection is disabled
#  index 4 metric 1 mtu 1500 
#  flags: <UP,BROADCAST,RUNNING,MULTICAST>
#  HWaddr: 00:0c:29:fc:b2:71
#  inet 169.254.169.248/16 broadcast 169.254.255.255
#  inet6 fe80::20c:29ff:fefc:b271/64
#Interface lo is up, line protocol detection is disabled
#  index 1 metric 1 mtu 16436 
#  flags: <UP,LOOPBACK,RUNNING>
#  inet 127.0.0.1/8
#  inet6 ::1/128



class ControllerError(Exception):
    pass


class InterfaceData(dict):
    STATUS = aid.Enums("down", "up")
    DOWN, UP = STATUS

    def __init__(self):
        super(InterfaceData, self).__init__()
        self["name"] = "<unk>"
        self["status"] = -1
        self["ifindex"] = -1
        self["metric"] = -1
        self["mtu"] = -1
        self["flags"] = "<UNK>"
        self["macaddr"] = None
        self["ipaddr"] = None

    def __str__(self):
        return """Interface {name} is {status}
  index {ifindex} metric {metric} mtu {mtu}
  flags: {flags}
  HWaddr: {macaddr}
  inet {ipaddr}""".format(**self)


class InterfaceList(dict):

    def parse(self, text):
        iface = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("Interface"):
                iface = InterfaceData()
                parts = line.split()
                if len(parts) >=4:
                    sts=self._get_state(parts[3])
                    iface["name"] = parts[1]
                    iface["status"] = sts
                    self[parts[1]] = iface
                else:
                    continue
            else:
                if line.startswith("index"):
                    parts = line.split()
                    iface["ifindex"] = int(parts[1])
                    iface["metric"] = int(parts[3])
                    iface["mtu"] = int(parts[5])
                elif line.startswith("flags"):
                    iface["flags"] = line.split()[1] # TODO parse out?
                elif line.startswith("HWaddr"):
                    iface["macaddr"] = line.split()[1]
                elif line.startswith("inet6"):
                    continue
                elif line.startswith("inet"):
                    iface["ipaddr"] = ipv4.IPv4(line.split()[1])

    def _get_state(self, val):
        if val.startswith("up"):
            return InterfaceData.UP
        elif val.startswith("down"):
            return InterfaceData.DOWN
        else:
            raise ControllerError("unrecognized status value: {!r}".format(val))

    def __str__(self):
        return "\n".join([str(o) for o in self.values()])


class RouterManager(object):

    def get_interfaces(self):
        proc = proctools.spawnpipe("/usr/bin/vtysh -c 'show int'")
        out = proc.read()
        es = proc.wait()
        if es:
            ifl = InterfaceList()
            ifl.parse(out)
            return ifl
        else:
            raise ControllerError("Could not read output of ip command.")


if __name__ == "__main__":
    from pycopia import autodebug
    m = RouterManager()
    ifl = m.get_interfaces()
    print(ifl)


