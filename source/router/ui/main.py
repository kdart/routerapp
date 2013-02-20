#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=0:smarttab

"""
Main entry for management UI.
"""

from pycopia.WWW import HTML5
from pycopia.WWW import framework

from router.ui import auth

ENCODING = "utf-8"


class IndexHandler(framework.RequestHandler):

    def get(self, request):
        resp = self.get_response(request)
        doc = resp.doc
        doc.stylesheet = "/media/css/router.css"
        doc.scripts = ["/media/js/modernizr-1.7.min.js"]
        doc.title = "Router Administration"
        doc.body.add_header(1, "Router Administration")
        doc.body.append(resp.anchor2("/", "Home"))
        doc.body.append(resp.anchor2("/router/status/", "Status"))
        doc.body.append(resp.anchor2("/auth/logout", "Logout"))
        return resp.finalize()

index = IndexHandler(verifier=auth.need_login)


