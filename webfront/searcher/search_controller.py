import abc
import http.client
import json
import re
import urllib.parse
from django.conf import settings


class SearchController(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_group_obj_of_field_by_query(self, query, field, fq=None, rows=0, start=0):
        raise NotImplementedError('users must define get_group_obj_of_field_by_query to use this base class')

    def get_number_of_field_by_endpoint(self, endpoint, field, accession):
        db = field
        if field.startswith("entry"):
            db = "entry_db"
        elif field.startswith("protein"):
            db = "protein_db"
        ngroups = self.get_group_obj_of_field_by_query(
             "{}:* && {}_acc:{}".format(db, endpoint, accession), field
        )["ngroups"]
        if isinstance(ngroups, dict):
            ngroups = ngroups["value"]
        return ngroups

    @abc.abstractmethod
    def get_chain(self):
        raise NotImplementedError('users must define get_chain to use this base class')

    @abc.abstractmethod
    def get_counter_object(self, endpoint, solr_query=None, extra_counters=[]):
        raise NotImplementedError('users must define get_counter_object to use this base class')

    @abc.abstractmethod
    def get_list_of_endpoint(self, endpoint, solr_query=None, rows=1, start=0):
        raise NotImplementedError('users must define get_list_of_endpoint to use this base class')

    @abc.abstractmethod
    def execute_query(self, query, fq=None, rows=0, start=0):
        raise NotImplementedError('users must define execute_query to use this base class')

    @abc.abstractmethod
    def add(self, docs):
        raise NotImplementedError('users must define execute_query to use this base class')

    @abc.abstractmethod
    def clear_all_docs(self):
        raise NotImplementedError('users must define execute_query to use this base class')

    # TODO: check if we can do that only once when building the data instead, to remove it here
    @staticmethod
    def to_dbcodes(q):
        re.sub(r'pfam', "p", "some pFam ", flags=re.IGNORECASE)

        q = re.sub(r'Pfam', "h", q, flags=re.IGNORECASE)
        q = re.sub(r'Prosite?profiles', "m", q, flags=re.IGNORECASE)
        q = re.sub(r'SMART', "r", q, flags=re.IGNORECASE)
        q = re.sub(r'PHANTER', "v", q, flags=re.IGNORECASE)
        q = re.sub(r'MobiDB', "g", q, flags=re.IGNORECASE)
        q = re.sub(r'SFLD', "b", q, flags=re.IGNORECASE)
        q = re.sub(r'Prosite?patterns', "p", q, flags=re.IGNORECASE)
        q = re.sub(r'GENE 3D', "x", q, flags=re.IGNORECASE)
        q = re.sub(r'TIGRFAMs', "n", q, flags=re.IGNORECASE)
        q = re.sub(r'CDD', "j", q, flags=re.IGNORECASE)
        q = re.sub(r'SUPERFAMILY', "y", q, flags=re.IGNORECASE)
        q = re.sub(r'PIRSF', "u", q, flags=re.IGNORECASE)
        q = re.sub(r'ProDom', "d", q, flags=re.IGNORECASE)
        q = re.sub(r'HAMAP', "q", q, flags=re.IGNORECASE)
        q = re.sub(r'Prints', "f", q, flags=re.IGNORECASE)
        q = re.sub(r'swissprot', "s", q, flags=re.IGNORECASE)
        q = re.sub(r'trembl', "t", q, flags=re.IGNORECASE)
        return q