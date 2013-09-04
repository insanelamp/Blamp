#
from jinja2 import Environment
from jinja2 import FileSystemLoader
from .base import MimetypeHandlerBase

class JinjaTemplate(MimetypeHandlerBase):

    def __init__(self, app):
        config = app.config
        self.env = Environment(loader=FileSystemLoader(config['templates']),
                               autoescape=True)

    def __call__(self, request, view, resource):
        t = self.env.get_template(view['template'])
        return t.render({"request" : request, "resource" : resource})

