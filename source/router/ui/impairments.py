
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from pycopia.WWW import framework
from router.ui import auth

ENCODING = b"utf-8"

class ImpairmentsHandler(framework.RequestHandler):

    def get(self, request):
        resp = self.get_response(request)
        doc = resp.doc
        doc.stylesheet = "/media/css/ui.css"
        doc.scripts = ["/media/js/modernizr-1.7.min.js"]
        doc.title = "Router Impairments"
        nav = doc.body.add_section("nav")
        nav.append(resp.anchor2("/", "Home"))
        doc.body.add_header(1, "Router Impairments")
        return resp.finalize()

index = ImpairmentsHandler(verifier=auth.need_login)



