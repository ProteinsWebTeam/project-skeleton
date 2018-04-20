import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from collections import OrderedDict

from django.core.cache import cache

from rest_framework import status
from webfront.response import Response
from django.conf import settings

multiple_slashes = re.compile('/+')

def canonical(url):
    parsed = urlparse(url)
    # process query
    query = parse_qs(parsed.query, keep_blank_values=True)
    # order querystring, lowercase keys
    query = OrderedDict(
        sorted(
            ((key.lower(), sorted(value)) for key, value in query.items())
        )
    )
    # handle page_size
    if query.get('page_size') == [str(settings.INTERPRO_CONFIG.get('default_page_size', 20))]:
        query.pop('page_size', None)
    # handle page
    if query.get('page') == ['1']:
        query.pop('page', None)
    # generate new canonical ParseResult
    canonical_parsed = parsed._replace(
      path=multiple_slashes.sub('/', parsed.path + '/'),
      query=urlencode(query, doseq=True)
    )
    # stringify and return
    return urlunparse(canonical_parsed)

class InterProCache:
    def set(self, key, response):
        try:
            if settings.INTERPRO_CONFIG.get('enable_caching', False)\
                and settings.INTERPRO_CONFIG.get('enable_cache_write', False):
                if response.status_code == status.HTTP_200_OK:
                    if response.data:
                        key = canonical(key)
                        value = {
                            'data': {x: response.data[x] for x in response.data},
                            'status': response.status_code,
                            'template_name': response.template_name,
                            'exception': response.exception,
                            'content_type': response.content_type,
                            'headers': {
                                'Content-Type': response.get('Content-Type', ""),
                                'InterPro-Version': response.get('InterPro-Version', ""),
                                'Server-Timing': response.get('Server-Timing', ""),
                                'Cached': 'true'
                            }
                        }
                        cache.set(key, value, timeout=None)
        except:
            pass

    def get(self, key):
        if settings.INTERPRO_CONFIG.get('enable_caching', False):
            key = canonical(key)
            value = cache.get(key)
            if value:
                value = Response(
                    value.get('data'),
                    value.get('status', 200),
                    value.get('template_name'),
                    value.get('headers', {}),
                    value.get('exception', False),
                    value.get('content_type')
                )
            return value
