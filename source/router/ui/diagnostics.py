
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import os

from pycopia.WWW import framework
#from pycopia import proctools

from router.ui import auth

ENCODING = b"utf-8"

class DiagnosticsHandler(framework.RequestHandler):

    def get(self, request):
        resp = self.get_response(request)
        doc = resp.doc
        doc.stylesheet = "/media/css/ui.css"
        doc.scripts = ["/media/js/modernizr-1.7.min.js"]
        doc.title = "Router Diagnostics (this is a test)"
        nav = doc.body.add_section("nav")
        nav.append(resp.anchor2("/", "Home"))
        doc.body.add_header(1, "Router Diagnostics (TEST)")
        doc.body.add_unordered_list(get_files())
        frm = doc.add_form()
        frm.add_textinput("rcpt", "Text")
        frm.add_input(type="submit", value="Submit")
        return resp.finalize()

    def post(self, request):
        resp = self.get_response(request)
        doc = resp.doc
        text = request.POST["rcpt"]
        doc.new_para("You entered:")
        doc.new_preformat(text)
        doc.new_para("Report desc:")
        doc.new_preformat(get_report())
        return resp.finalize()

def get_files():
    rv = []
    for name in os.listdir("/proc/self/fd"):
        try:
            rv.append("{} - > {}".format(name, os.readlink("/proc/self/fd/" + name)))
        except OSError:
            rv.append("{} did not read".format(name))
    return rv

def get_report():
    return """
        User id: {uid}
    Current dir: {cwd}
    """.format(
            uid=os.getuid(),
            cwd=os.getcwd(),
            )


index = DiagnosticsHandler(verifier=auth.need_login)


