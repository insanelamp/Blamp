#
from werkzeug.exceptions import Forbidden
from werkzeug.exceptions import NotFound

class ResourceBase(object):

    def __init__(self, request):
        self._request = request

    def __unicode__(self):
        return unicode(self.__class__.__name__)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def resource_url(self):
        return None

    def check_acl(self, context="default", throw=True):
        if throw:
            raise Forbidden()
        return False

    def check_exists(self, throw=True):
        if throw:
            raise NotFound()
        return False

    def load(self, args, query):
        pass

    def save(self, data):
        pass

    def delete(self):
        pass

