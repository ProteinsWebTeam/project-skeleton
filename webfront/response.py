from rest_framework.response import Response as R
from django.conf import settings

from webfront.models import Database


class Response(R):
    def __init__(
        self,
        data=None,
        status=None,
        template_name=None,
        headers={},
        exception=False,
        content_type=None,
    ):

        if settings.DEBUG:
            from django.db import connection
            from webfront.searcher.elastic_controller import es_results

            timings = [
                # 'cpu;dur=1;desc="CPU"',
                'mysql;dur={:0.2f};desc="MySQL"'.format(
                    sum((float(query["time"]) for query in connection.queries)) * 1000
                ),
                # 'filesystem;dur=0;desc="Filesystem"',
                'es;dur={:0.2f};desc="Elasticsearch"'.format(
                    sum(query["took"] for query in es_results if "took" in query)
                ),
                # 'django;dur={:0.2f};desc=Django'.format(
                #     (datetime.now().timestamp() - django_time['time']) * 1000
                # )
            ]

            headers["Server-Timing"] = ",".join(timings)

        headers["InterPro-Version"] = Database.objects.get(pk="interpro").version
        headers["InterPro-Version-Minor"] = settings.MINOR_VERSION

        super(Response, self).__init__(
            data, status, template_name, headers, exception, content_type
        )
