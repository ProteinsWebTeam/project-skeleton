from webfront.serializers.content_serializers import ModelContentSerializer
from webfront.views.custom import SerializerDetail
from webfront.models import Taxonomy, Proteome
import webfront.serializers.interpro
import webfront.serializers.uniprot
import webfront.serializers.pdb
from webfront.views.queryset_manager import escape


class ProteomeSerializer(ModelContentSerializer):

    def to_representation(self, instance):
        representation = {}
        representation = self.endpoint_representation(representation, instance)
        # representation = self.filter_representation(representation, instance, self.detail_filters, self.detail)
        if self.queryset_manager.other_fields is not None:
            def counter_function():
                get_c = ProteomeSerializer.get_counters
                return get_c(
                    instance,
                    self.searcher,
                    self.queryset_manager.get_searcher_query()
                )
            representation = self.add_other_fields(
                representation,
                instance,
                self.queryset_manager.other_fields,
                {"counters": counter_function}
            )
        return representation

    def endpoint_representation(self, representation, instance):
        detail = self.detail
        if detail == SerializerDetail.ALL:
            representation = self.to_full_representation(instance)
        elif detail == SerializerDetail.PROTEOME_OVERVIEW:
            representation = self.to_counter_representation(instance)
        elif detail == SerializerDetail.PROTEOME_HEADERS:
            representation = self.to_headers_representation(instance)
        return representation


    def to_full_representation(self, instance):
        searcher = self.searcher
        sq = self.queryset_manager.get_searcher_query()
        return {
            "metadata": {
                "accession": instance.accession,
                "name": {
                    "name": instance.name
                },
                "source_database": "uniprot",
                "is_reference": instance.is_reference,
                "strain": instance.strain,
                "assembly": instance.assembly,
                "taxonomy": instance.taxonomy.accession if instance.taxonomy is not None else None,
                "counters": ProteomeSerializer.get_counters(instance, searcher, sq)
            }
        }

    @staticmethod
    def to_headers_representation(instance):
        return {
            "metadata": {
                "accession": instance.accession,
                "name": instance.name,
                "is_reference": instance.is_reference,
                "taxonomy": instance.taxonomy.accession if instance.taxonomy is not None else None,
                "source_database": "uniprot",
            }
        }

    @staticmethod
    def get_counters(instance, searcher, sq):
        return {
            "entries": searcher.get_number_of_field_by_endpoint("proteome", "entry_acc", instance.accession, sq),
            "structures": searcher.get_number_of_field_by_endpoint("proteome", "structure_acc", instance.accession, sq),
            "proteins": searcher.get_number_of_field_by_endpoint("proteome", "protein_acc", instance.accession, sq),
            "sets": searcher.get_number_of_field_by_endpoint("proteome", "set_acc", instance.accession, sq),
        }

    @staticmethod
    def to_counter_representation(instance):
        if "taxa" not in instance:
            if ("count" in instance and instance["count"] == 0) or \
               ("doc_count" in instance["databases"] and instance["databases"]["doc_count"] == 0):
                raise ReferenceError('There are not structures for this request')
            instance = {
                "proteomes": {
                    "uniprot": ProteomeSerializer.serialize_counter_bucket(instance["databases"], "proteomes"),
                }
            }
        return instance

    @staticmethod
    def get_proteome_header_from_search_object(obj, include_chain=False):
        header = {
            "taxonomy": obj["tax_id"],
            "lineage": obj["lineage"],
            "accession": obj["proteomes"][0],
            "source_database": "uniprot"
        }
        if include_chain:
            header["chain"] = obj["chain"]
        return header

