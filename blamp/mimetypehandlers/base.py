#

class MimetypeHandlerBase(object):

    def __init__(self, app):
        pass

    def __call__(self, request, view, resource):
        return str(resource)

