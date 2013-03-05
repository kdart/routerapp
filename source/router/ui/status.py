#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from pycopia import passwd
from pycopia.WWW import framework
from pycopia.WWW import HTML5

from router.ui import auth
from router import controller

ENCODING = b"utf-8"


def status_constructor(**kwargs):
    doc = HTML5.new_document()
    for name, val in kwargs.items():
        setattr(doc, name, val)
    doc.stylesheet = "/media/css/ui.css"
    doc.scripts = ["/media/js/modernizr-1.7.min.js"]
    navigation = doc.body.add_section("nav", id="navigation")
    header = doc.add_section("header", id="header")
    content = wrapper.add_section("container", id="content")
    footer = doc.add_section("footer", id="footer")
    doc.header = header
    doc.content = content
    doc.nav = navigation
    doc.footer = footer
    return doc



class StatusHandler(framework.RequestHandler):

    def get(self, request):
        resp = self.get_response(request, title="Router Status")
        doc = resp.doc
        doc.nav.append(resp.anchor2("/", "Home"))
        doc.body.add_header(1, "Interface Status")
        cont = controller.RouterManager()
        iflist = cont.get_interfaces()
        doc.new_preformat(str(iflist)) # XXX
        return resp.finalize()


class DashboardHandler(framework.RequestHandler):

    def get(self, request):
        resp = self.get_response(request)
        doc = resp.doc
        doc.new_para("Interface Status")
        ifstat = ["{}: {}".format(ifs[b"name"], ifs[b"status"]) for ifs in get_interface_status()]
        doc.body.add_unordered_list(ifstat)
        return resp.finalize()



def get_interface_status():
        cont = controller.RouterManager()
        return cont.get_interfaces().values()


index = StatusHandler(constructor=status_constructor, verifier=auth.need_login)
dashboard = DashboardHandler(verifier=auth.need_login)

