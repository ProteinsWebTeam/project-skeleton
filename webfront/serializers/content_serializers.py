from rest_framework import serializers

from webfront.views.custom import SerializerDetail
from webfront.solr_controller import SolrController

#
# class ContentSerializer(serializers.Serializer):
#     def __init__(self, *args, **kwargs):
#         content = kwargs.pop('content', [])
#         self.detail = kwargs.pop('serializer_detail', SerializerDetail.ALL)
#
#         super(ContentSerializer, self).__init__(*args, **kwargs)
#         try:
#             for to_be_removed in set(self.Meta.optionals) - set(content):
#                 self.fields.pop(to_be_removed)
#         except AttributeError:
#             pass


class ModelContentSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        content = kwargs.pop('content', [])
        self.queryset_manager = kwargs.pop('queryset_manager', None)
        self.solr = SolrController(self.queryset_manager)
        self.detail = kwargs.pop('serializer_detail', SerializerDetail.ALL)
        self.detail_filters = kwargs.pop('serializer_detail_filters', SerializerDetail.ALL)

        self.detail_filters = [self.detail_filters[x]["filter_serializer"] for x in self.detail_filters]
        super(ModelContentSerializer, self).__init__(*args, **kwargs)
        try:
            for to_be_removed in set(self.Meta.optionals) - set(content):
                self.fields.pop(to_be_removed)
        except AttributeError:
            pass
