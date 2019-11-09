from gevent.pywsgi import WSGIServer
from tau import app

http_server = WSGIServer(('', 8000), app)
http_server.serve_forever()