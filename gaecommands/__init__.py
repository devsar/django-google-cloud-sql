#!/usr/bin/python
#

import logging
import os
import sys
import wsgiref

from StringIO import StringIO

from google.appengine.ext import webapp


# Add parent folder to sys.path, so we can import boot.
# App Engine causes main.py to be reloaded if an exception gets raised
# on the first request of a main.py instance, so don't add project_dir multiple
# times.
project_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_dir not in sys.path or sys.path.index(project_dir) > 0:
    while project_dir in sys.path:
        sys.path.remove(project_dir)
    sys.path.insert(0, project_dir)

for path in sys.path[:]:
    if path != project_dir and os.path.isdir(os.path.join(path, 'django')):
        sys.path.remove(path)
        break

# Remove the standard version of Django.
if 'django' in sys.modules and sys.modules['django'].VERSION < (1, 2):
    for k in [k for k in sys.modules
              if k.startswith('django.') or k == 'django']:
        del sys.modules[k]

os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

from djangoappengine_rdbms.boot import setup_env
setup_env()



class SyncDBHandler(webapp.RequestHandler):
    """
        Creates a new session and renders the shell.html template.
    """

    def get(self):
        from StringIO import StringIO
        from django.core.management.commands import syncdb
        
        orginal_stdout = sys.stdout
        f = StringIO()
        sys.stdout = f
        
        #run syncdb
        syncdb.Command().handle()
        f.seek(0)
        html = """<html>
<body>
<pre>
%(result)s
</pre>
</body>
</html> 
"""  % {'result': f.read()}
        f.close()
        sys.stdout = orginal_stdout
        self.response.out.write(html)


class CommandsHandler(webapp.RequestHandler):
    """
        Execute custom commands
    """
    def get(self):        
        self.response.out.write("""<html><body><form action="." method="POST"><input name="command"><input type="submit"></form></body></html>""")
        
    def post(self):
        orginal_stdout = sys.stdout
        orginal_stderr = sys.stderr
        f = StringIO()
        sys.stdout = f
        sys.stderr = f
        
        #run syncdb
        try:
            from django.core.management import ManagementUtility
            argv = ("manage.py " + self.request.get("command", "help")).split(" ")
            ManagementUtility(argv=argv).execute()
        except:
            import logging
            logging.exception("error")

        f.seek(0)
        html = """<html>
<body>
<form action="." method="POST">
<input name="command">
<input type="submit">
</form>
<pre>
%(result)s
</pre>
</body>
</html> 
"""  % {'result': f.read()}
        f.close()
        sys.stdout = orginal_stdout
        sys.stderr = orginal_stderr
        self.response.out.write(html)


def main():
    application = webapp.WSGIApplication([('/commands/syncdb/', SyncDBHandler),
                                          ('/commands/', CommandsHandler),], debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
