#!/usr/bin/python2.7
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from pycopia import passwd
from pycopia.WWW import framework

from router.ui import auth
from router import controller

ENCODING = b"utf-8"

class StatusHandler(framework.RequestHandler):

    def get(self, request):
        resp = self.get_response(request)
        doc = resp.doc
        doc.stylesheet = "/media/css/ui.css"
        doc.scripts = ["/media/js/modernizr-1.7.min.js"]
        doc.title = "Router Status"
        nav = doc.body.add_section("nav")
        nav.append(resp.anchor2("/", "Home"))
        doc.body.add_header(1, "Interface Status")

        cont = controller.RouterManager()
        iflist = cont.get_interfaces()
        doc.new_preformat(str(iflist)) # XXX
        return resp.finalize()


class DashboardHandler(framework.RequestHandler):

    def get(self, request):
        resp = self.get_response(request)
        doc = resp.doc
        doc.stylesheet = "/media/css/ui.css"
        doc.new_para("Current Status")
        return resp.finalize()


index = StatusHandler(verifier=auth.need_login)
dashboard = DashboardHandler(verifier=auth.need_login)

