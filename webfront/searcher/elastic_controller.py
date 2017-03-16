
from django.conf import settings
import http.client
import json
import urllib.parse

from webfront.searcher.search_controller import SearchController


class ElasticsearchController(SearchController):

    def __init__(self, queryset_manager=None):
        url = urllib.parse.urlparse(settings.SEARCHER_URL)
        self.server = url.hostname
        self.port = url.port
        parts = url.path.split("/")
        self.index = parts[1]
        self.type = parts[2]
        self.queryset_manager = queryset_manager

    def add(self, docs):
        body = ""
        for doc in docs:
            body += '{ "index": { "_type": "'+self.type+'", "_id":"'+doc["id"]+'"}}\n'+json.dumps(doc)+'\n'
        conn = http.client.HTTPConnection(self.server, self.port)
        conn.request("POST", "/"+self.index+"/_bulk/", body)
        return conn.getresponse()

    def clear_all_docs(self):
        body = '{ "query": { "match_all": {} } }'
        conn = http.client.HTTPConnection(self.server, self.port)
        conn.request("POST", "/"+self.index+"/"+self.type+"/_delete_by_query?conflicts=proceed", body)
        return conn.getresponse()

    def get_counter_object(self, endpoint, solr_query=None, extra_counters=[]):
        qs = self.queryset_manager.get_solr_query()
        if qs == '':
            qs = '*:*'
        if solr_query is not None:
            qs += ' && ' + solr_query.lower()
        facet = {
            "aggs": {
                "databases": {
                    "terms": {
                        "field": "{}_db".format(endpoint),
                        "execution_hint": "map",
                    },
                    "aggs": {
                        "unique": {
                            "cardinality": {"field": "{}_acc".format(endpoint)}
                        },
                    }
                }
            },
            "size": 0
        }
        for ec in extra_counters:
            facet["aggs"]["databases"]["aggs"][ec] = {"cardinality": {"field": "{}_acc".format(ec)}}
        if endpoint == "entry":
            facet["aggs"]["unintegrated"] = {
              "filter": {
                  "bool": {
                      "must_not": [
                          {"term": {"entry_db": "interpro"}},
                          {"exists": {"field": "integrated"}}
                      ]
                  }
              },
              "aggs": {"unique": {"cardinality": {"field": "entry_acc"}}}
            }
            for ec in extra_counters:
                facet["aggs"]["unintegrated"]["aggs"][ec] = {"cardinality": {"field": "{}_acc".format(ec)}}
        elif endpoint == "protein":
            facet["aggs"]["uniprot"] = {
              "filter": {"exists": {"field": "protein_acc"}},
              "aggs": {"unique": {"cardinality": {"field": "protein_acc"}}}
            }
            for ec in extra_counters:
                facet["aggs"]["uniprot"]["aggs"][ec] = {"cardinality": {"field": "{}_acc".format(ec)}}
        elif endpoint == "structure":
            facet["aggs"]["databases"]["filter"] = {"exists": {"field": "structure_acc"}}
            del facet["aggs"]["databases"]["terms"]
            for ec in extra_counters:
                facet["aggs"]["databases"]["aggs"][ec] = {"cardinality": {"field": "{}_acc".format(ec)}}

        response = self._elastic_json_query(qs, facet)
        return response["aggregations"]

    def get_group_obj_of_field_by_query(self, query, field, fq=None, rows=1, start=0):
        query = self.queryset_manager.get_solr_query() if query is None else query.lower()
        facet = {
            "aggs": {
                "ngroups": {
                    "cardinality": {
                        "field": field
                    }
                },
                "groups": {
                    "terms": {
                        "field": field,
                        "size": rows,
                        "execution_hint": "map",
                    },
                    "aggs": {
                        "tops": {"top_hits": {"size": 1}}
                    }
                },
            },
            "size": 1
        }
        if fq is not None:
            query += " && "+fq
        response = self._elastic_json_query(query, facet)
        response["aggregations"]["groups"] = [
            bucket["tops"]["hits"]["hits"][0]["_source"]
            for bucket in response["aggregations"]["groups"]["buckets"]
        ]
        return response["aggregations"]

    def get_list_of_endpoint(self, endpoint, solr_query=None, rows=10, start=0):
        qs = self.queryset_manager.get_solr_query() if solr_query is None else solr_query
        if qs == '':
            qs = '*:*'
        facet = {
            "aggs": {
                "ngroups": {
                    "cardinality": {
                        "field": endpoint+"_acc"
                    }
                },
                "rscount": {
                    "terms": {
                        "field": '{}_acc'.format(endpoint),
                        "size": start+rows,
                        "order": {"_term": "asc"},
                        "execution_hint": "map",
                    }
                }
            },
            "size": 0
        }
        response = self._elastic_json_query(qs, facet)
        return [x['key'].upper() for x in response["aggregations"]["rscount"]["buckets"]], response["aggregations"]["ngroups"]["value"]

    def get_chain(self):
        qs = self.queryset_manager.get_solr_query()
        response = self._elastic_json_query(qs)
        return [ch["_source"] for ch in response["hits"]["hits"]]

    def execute_query(self, query, fq=None, rows=0, start=0):
        query = self.queryset_manager.get_solr_query() if query is None else query.lower()
        conn = http.client.HTTPConnection(self.server, self.port)
        if fq is not None:
            q = query+" && "+fq.lower()
        q = self.to_dbcodes(q.replace(" && ", "%20AND%20"))
        conn.request(
            "GET",
            "/"+self.index+"/"+self.type+"/_search?pretty&q="+q,
        )
        response = conn.getresponse()
        data = response.read().decode()
        obj = json.loads(data)
        return [o["_source"] for o in obj["hits"]["hits"]]

    def _elastic_json_query(self, q, query_obj=None):
        if query_obj is None:
            query_obj = {"from": 0}
        conn = http.client.HTTPConnection(self.server, self.port)
        q = self.to_dbcodes(q.replace(" && ", "%20AND%20"))
        conn.request(
            "GET",
            "/"+self.index+"/"+self.type+"/_search?pretty&q="+q,
            json.dumps(query_obj)
        )
        response = conn.getresponse()
        data = response.read().decode()
        obj = json.loads(data)
        return obj