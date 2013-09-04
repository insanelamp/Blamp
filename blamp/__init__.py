# Package

from ConfigParser import SafeConfigParser
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound
from werkzeug.exceptions import MethodNotAllowed
from werkzeug.exceptions import Forbidden
from werkzeug.exceptions import NotAcceptable
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.wrappers import Response
from .resourcebase import ResourceBase
from .request import Request
import os

class MimetypeHandlerBase(object):

    def __init__(self, app):
        pass

    def __call__(self, request, view, resource):
        return str(resource)

class Application(object):

    url_map = None
    view_map = {}
    mimetype_map = {}
    config = {}

    __method_map = {
        'get' : 'load',
        'put' : 'save',
        'post' : 'save',
        'delete' : 'delete'
    }

    def __init__(self):
        self.url_map = Map()
        self.mimetype_map['*/*'] = MimetypeHandlerBase

        config_path = os.path.join(os.getcwd(),
                                   os.environ.get('BLAMP_CONFIG',
                                                  '/usr/local/etc/blamp.ini'))
        if not os.path.exists(config_path):
            raise Exception('Config file not found: ' + config_path)
        cp = SafeConfigParser()
        cp.read(config_path)
        self.config = dict(cp.items('default'))

        # Validate required config options
        if 'templates' not in self.config:
            raise Exception("'template' config option missing")
        self.config['templates'] = os.path.join(os.getcwd(), self.config['templates'])

    def add_mimetype(self, mimetype, handler):
        self.mimetype_map[mimetype] = handler

    def add_view(self, url, name, methods=['GET'],
                 resource=None, resource_get=None, resource_put=None,
                 resource_post=None, resource_delete=None,
                 template=None,
                 acl_get='load', acl_put='update',
                 acl_post='create', acl_delete='delete',
                 accept=None, accept_get=None, accept_put=None,
                 accept_post=None, accept_delete=None):
        """ Add and configure a view. """

        self.url_map.add(Rule(url, endpoint=name))
        self.view_map[name] = {
            "methods" : [m.lower() for m in methods],
            "resource" : resource,
            "resource_get" : resource_get,
            "resource_put" : resource_put,
            "resource_post" : resource_post,
            "resource_delete" : resource_delete,
            "acl_get" : acl_get,
            "acl_put" : acl_put,
            "acl_post" : acl_post,
            "acl_delete" : acl_delete,
            "accept" : accept,
            "accept_get" : accept_get,
            "accept_put" : accept_put,
            "accept_post" : accept_post,
            "accept_delete" : accept_delete,
            "template" : template
        }

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        urls = self.url_map.bind_to_environ(environ)
        try:
            # Define view
            endpoint, args = urls.match()
            if endpoint not in self.view_map:
                raise NotFound("Endpoint not found in view_map.")
            view = self.view_map[endpoint]
            method = request.method.lower()
            if method not in view['methods']:
                raise MethodNotAllowed()

            resource = view['resource_' + method] or view['resource']
            accept= view['accept_' + method] or view['accept'] or ['text/html']
            acl = view['acl_' + method]
            data = None
            query = None

            accepted = request.accept_mimetypes.best_match(accept)
            if not accepted:
                raise NotAcceptable()

            if resource:
                resource = resource(request)
                resource.load(args, query)

                if acl and not resource.check_acl(acl):
                    raise Forbidden()

                if not resource.check_exists():
                    raise NotFound()

                if method == 'put' or method == 'post':
                    resource.save(data)
                elif method == 'delete':
                    resource.delete()
                    resource = None

            accepted_handler = self.mimetype_map[accepted] \
                               if accepted in self.mimetype_map \
                               else self.mimetype_map['*/*']
            mimetype_handler = accepted_handler(self)
            response = Response(mimetype_handler(request, view, resource))
            response.headers['Content-Type'] = accepted

            if method == 'post' and resource:
                response.status_code = 201
                response.headers['Location'] = resource.resource_url()

            return response(environ, start_response)

        except HTTPException as e:
            return e(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)
