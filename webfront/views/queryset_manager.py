from webfront.models import Entry, Protein, Structure
from django.db.models import Q
from functools import reduce
from operator import or_


class QuerysetManager:
    main_endpoint = None
    filters = {
        "search": {},
        "solr": {},
        "entry": {},
        "structure": {},
        "protein": {},
    }
    endpoints = []

    def reset_filters(self, endpoint, endpoint_levels=[]):
        self.main_endpoint = endpoint
        self.endpoints = endpoint_levels
        self.filters = {
            "search": {},
            "solr": {},
            "entry": {},
            "structure": {},
            "protein": {},
        }

    def add_filter(self, endpoint,  **kwargs):
        self.filters[endpoint] = {**self.filters[endpoint], **kwargs}

    def remove_filter(self, endpoint, f):
        del self.filters[endpoint][f]

    def get_searcher_query(self, include_search=False):
        q = ""
        for ep in self.filters:
            for k, v in self.filters[ep].items():
                if ep == "solr":
                    q += " && {}:{}".format(k, v)
                elif include_search and ep == "search":
                    q += " && text:*{}*".format(v)
                elif k == "source_database__isnull":
                    q += " && {}{}_db:*".format("!" if v else "", ep)
                elif k == "accession" or k == "accession__iexact":
                    q += " && {}_acc:{}".format(ep, v)
                elif k == "accession__isnull":
                    # elasticsearch perform better if the "give me all" query runs over a
                    # low cardinality field such as the _db ones
                    if ep == 'structure':
                        q += " && {}{}_acc:*".format("!" if v else "", ep)
                    else:
                        q += " && {}{}_db:*".format("!" if v else "", ep)
                elif k == "integrated" or k == "integrated__iexact":
                    q += " && integrated:{}".format(v)
                elif k == "integrated__isnull":
                    q += " && {}integrated:*".format("!entry_db:interpro && !" if v else "")
                elif k == "type" or k == "type__iexact":
                    q += " && {}_type:{}".format(ep, v)
                elif ep != "structure":
                    if k == "source_database" or k == "source_database__iexact":
                        q += " && {}_db:{}".format(ep, v)
        return q[4:].lower()

    def get_base_queryset(self, endpoint):
        queryset = Entry.objects.all()
        if endpoint == "entry":
            queryset = Entry.objects.all()
        elif endpoint == "structure":
            queryset = Structure.objects.all()
        elif endpoint == "protein":
            queryset = Protein.objects.all()
        return queryset

    def get_queryset(self, endpoint=None, only_main_endpoint=False):
        if endpoint is None:
            endpoint = self.main_endpoint
        queryset = self.get_base_queryset(endpoint)
        current_filters = {} #if only_main_endpoint else self.get_join_filters(endpoint)

        # creates an `OR` filter for the search fields
        search_filters = self.filters.get("search")
        if search_filters:
            or_filter = reduce(
                or_,
                (Q(**{f[0]: f[1]}) for f in search_filters.items()),
            )

        for ep in self.filters:
            if ep == "search" or ep == "solr":
                continue
            if ep == endpoint:
                current_filters = {**current_filters, **{k: v
                                                         for k, v in self.filters[ep].items()}
                                   }
            elif not only_main_endpoint:
                current_filters = {**current_filters, **{ep+"__"+k: v
                                                         for k, v in self.filters[ep].items()}
                                   }

        if search_filters:
            return queryset.filter(or_filter, **current_filters)
        return queryset.filter(**current_filters)

    def update_interpro_filter(self):
        for k, f in self.filters["entry"].items():
            if k == "source_database" or k == "source_database__iexact":
                self.filters["entry"]["integrated__isnull"] = False
                del self.filters["entry"][k]
            elif k == "accession" or k == "accession__iexact":
                self.filters["entry"]["integrated__iexact"] = f
                del self.filters["entry"][k]
