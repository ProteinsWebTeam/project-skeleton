from webfront.models import Entry
from webfront.serializers.content_serializers import ModelContentSerializer
from webfront.serializers.uniprot import ProteinSerializer
from webfront.views.custom import SerializerDetail


class EntrySerializer(ModelContentSerializer):

    def to_representation(self, instance):
        representation = {}
        if self.detail == SerializerDetail.ALL:
            representation["metadata"] = self.to_metadata_representation(instance)
            representation["proteins"] = self.to_proteins_count_representation(instance)
        elif self.detail == SerializerDetail.PROTEIN_OVERVIEW:
            representation["metadata"] = self.to_metadata_representation(instance)
            representation["proteins"] = self.to_proteins_overview_representation(instance)
        elif self.detail == SerializerDetail.PROTEIN_DETAIL:
            representation["metadata"] = self.to_metadata_representation(instance)
            representation["proteins"] = self.to_proteins_detail_representation(instance)
        elif self.detail == SerializerDetail.PROTEIN_ENTRY_DETAIL:
            representation["metadata"] = self.to_metadata_representation(instance.entry)
            representation["proteins"] = self.to_proteins_detail_representation(instance.protein)
            # representation["metadata"] = self.to_metadata_representation(instance.entry)
            # representation["proteins"] = [ProteinSerializer.to_metadata_representation(instance.protein)]
        return representation

    @staticmethod
    def to_metadata_representation(instance):
        obj = {
            'accession': instance.accession,
            'entry_id': instance.entry_id,
            'type': instance.type,
            'go_terms': instance.go_terms,
            'source_dataBase': instance.source_database,
            'member_databases': instance.member_databases,
            'integrated': instance.integrated,
            'name': {
                'name': instance.name,
                'short': instance.short_name,
                'other': instance.other_names
            },
            "description": instance.description,
            "wikipedia": instance.wikipedia,
            "literature": instance.literature
        }
        # Just showing the accesion number instead of recursively show the entry to which has been integrated
        if instance.integrated:
            obj["integrated"] = instance.integrated.accession
        return obj

    @staticmethod
    def to_proteins_count_representation(instance):
        return instance.proteinentryfeature_set.count()

    @staticmethod
    def to_proteins_overview_representation(instance):
        return [
            EntrySerializer.to_match_representation(match)
            for match in instance.proteinentryfeature_set.all()
        ]

    @staticmethod
    def to_match_representation(match):
        return {
            "accession": match.protein_id,
            "match_start": match.match_start,
            "match_end": match.match_end
        }
    @staticmethod
    def to_proteins_detail_representation(instance):
        return [
            { **EntrySerializer.to_match_representation(match),
              **ProteinSerializer.to_metadata_representation(match.protein)
            }
            for match in instance.proteinentryfeature_set.all()
        ]
    class Meta:
        model = Entry
