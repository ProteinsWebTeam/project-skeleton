from webfront.constants import get_queryset_type, QuerysetType
from webfront.models import Protein

from webfront.serializers.content_serializers import ModelContentSerializer
import webfront.serializers.interpro
from webfront.views.custom import SerializerDetail


class ProteinSerializer(ModelContentSerializer):

    def to_representation(self, instance):
        representation = {}

        representation = self.endpoint_representation(representation, instance, self.detail)
        representation = self.filter_representation(representation, instance, self.detail_filters)

        return representation

    def endpoint_representation(self, representation, instance, detail):
        if detail == SerializerDetail.ALL:
            representation = self.to_full_representation(instance)
        elif detail == SerializerDetail.PROTEIN_HEADERS:
            representation = self.to_headers_representation(instance)
        return representation

    @staticmethod
    def filter_representation(representation, instance, detail_filters):
        # qs_type = get_queryset_type(instance)
        # if SerializerDetail.ENTRY_OVERVIEW in detail_filters:
        #     representation["entries"] = ProteinSerializer.to_entries_count_representation(instance)
        # if SerializerDetail.ENTRY_MATCH in detail_filters:
        #     representation["entries"] = ProteinSerializer.to_entries_overview_representation(instance, False)
        # if SerializerDetail.ENTRY_DETAIL in detail_filters:
        #     representation["entries"] = ProteinSerializer.to_entries_overview_representation(instance, True)
        # if SerializerDetail.STRUCTURE_HEADERS in detail_filters:
        #     representation["structures"] = ProteinSerializer.to_structures_count_representation(instance)
        # if SerializerDetail.STRUCTURE_OVERVIEW in detail_filters:
        #     representation["structures"] = ProteinSerializer.to_structures_overview_representation(instance)
        # if SerializerDetail.STRUCTURE_DETAIL in detail_filters:
        #     if qs_type == QuerysetType.PROTEIN:
        #         representation["structures"] = ProteinSerializer.to_structures_overview_representation(instance, True)
        return representation

    def to_full_representation(self, instance):
        return {
            "metadata": self.to_metadata_representation(instance),
            "representation": instance.feature,
            "genomic_context": instance.genomic_context,
            # "source_database": instance.source_database
        }

    @staticmethod
    def to_headers_representation(instance):
        return {
            "metadata": {
                "accession": instance.accession,
                "name": instance.name,
                "source_database": instance.source_database,
                "length": instance.length
            }
        }

    def to_metadata_representation(self, instance):
        return {
            "accession": instance.accession,
            "id": instance.identifier,
            "source_organism": instance.organism,
            "name": {
                "name": instance.name,
                "short": instance.short_name,
                "other": instance.other_names,
            },
            "description": instance.description,
            "length": instance.length,
            "sequence": instance.sequence,
            "proteome": instance.proteome,
            "gene": instance.gene,
            "go_terms": instance.go_terms,
            "protein_evidence": 4,
            "source_database": instance.source_database,
            "counters": {
                "entries": self.solr.get_number_of_field_by_endpoint("protein", "entry_acc", instance.accession),
                "structures": self.solr.get_number_of_field_by_endpoint("protein", "structure_acc", instance.accession),
            }
        }

    @staticmethod
    def to_match_representation(match, full=False):
        output = {
            "coordinates": match.coordinates,
            "accession": match.entry_id,
            "source_database": match.entry.source_database,
            "name": match.entry.name,
        }
        if match.entry.integrated:
            output["integrated"]= match.entry.integrated.accession

        if full:
            output["entry"] = webfront.serializers.interpro.EntrySerializer.to_metadata_representation(match.entry)

        return output

    # @staticmethod
    # def to_entries_representation(instance):
    #     return [
    #         ProteinSerializer.to_match_representation(match)
    #         for match in instance.proteinentryfeature_set.all()
    #     ]

    @staticmethod
    def to_entries_count_representation(instance):
        return instance.proteinentryfeature_set.count()
    #
    @staticmethod
    def to_structures_count_representation(instance):
        return instance.structures.distinct().count()

    @staticmethod
    def to_chain_representation(instance, full=False):
        from webfront.serializers.pdb import StructureSerializer

        chain = {
            "chain": instance.chain,
            "accession": instance.structure.accession,
            "source_database": instance.structure.source_database,
            "length": instance.length,
            "organism": instance.organism,
            "coordinates": instance.coordinates,
        }
        if full:
            chain["structure"] = StructureSerializer.to_metadata_representation(instance.structure)
        return chain

    @staticmethod
    def to_structures_overview_representation(instance, is_full=False):
        return [
            ProteinSerializer.to_chain_representation(match, is_full)
            for match in instance.proteinstructurefeature_set.all()
            ]

    @staticmethod
    def to_entries_overview_representation(instance, is_full=False):
        return [
            ProteinSerializer.to_match_representation(match, is_full)
            for match in instance.proteinentryfeature_set.all()
            ]

    class Meta:
        model = Protein
