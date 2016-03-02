from django.db.models import Count
from webfront.models import Entry
from webfront.serializers.interpro import EntrySerializer
from .custom import CustomView
# from webfront.active_sites import ActiveSites
# from webfront.models import Clan, Pfama, DwEntrySignature,DwEntry
#from webfront.serializers.interpro import EntryOverviewSerializer, EntryDWSerializer
#from webfront.serializers.pfam import ClanSerializer, PfamaSerializer

#
# class PfamClanIDHandler(CustomView):
#     level_description = 'Pfam clan ID level'
#     serializer_class = ClanSerializer
#     django_db = "pfam_ro"
#     many = False
#
#     def get(self, request, endpoint_levels, available_endpoint_handlers={}, level=0, *args, **kwargs):
#         self.queryset = Clan.objects.all().filter(clan_acc=endpoint_levels[level-1])
#
#         return super(PfamClanIDHandler, self).get(
#             request, endpoint_levels, available_endpoint_handlers, level, *args, **kwargs
#         )
#
#
# class ClanHandler(CustomView):
#     level_description = 'Pfam clan level'
#     child_handlers = {
#         r'CL\d{4}': PfamClanIDHandler,
#     }
#     serializer_class = ClanSerializer
#     django_db = "pfam_ro"
#
#     def get(self, request, endpoint_levels, *args, **kwargs):
#
#         self.queryset = Clan.objects.all()
#
#         return super(ClanHandler, self).get(
#             request, endpoint_levels, *args, **kwargs
#         )
#
#
# class ActiveSitesHandler(CustomView):
#     level_description = 'Pfam ID level',
#     django_db = "pfam_ro"
#     from_model = False
#     many = False
#
#     def get(self, request, endpoint_levels, available_endpoint_handlers={}, level=0, *args, **kwargs):
#         active_sites = ActiveSites(endpoint_levels[level-2])
#         active_sites.load_from_db()
#         active_sites.load_alignment()
#
#         self.queryset = active_sites.proteins
#
#         return Response(active_sites.proteins)
#         # return super(ActiveSitesHandler, self).get(
#         #     request, endpoint_levels, *args, **kwargs
#         # )
#
#
# class PfamIDHandler(CustomView):
#     level_description = 'Pfam ID level',
#     serializer_class = PfamaSerializer
#     django_db = "pfam_ro"
#     many = False
#     child_handlers = {
#         'active_sites': ActiveSitesHandler,
#     }
#
#     def get(self, request, endpoint_levels, available_endpoint_handlers={}, level=0, *args, **kwargs):
#
#         self.queryset = Pfama.objects.all().filter(pfama_acc=endpoint_levels[level-1])
#
#         return super(PfamIDHandler, self).get(
#             request, endpoint_levels, available_endpoint_handlers, level, *args, **kwargs
#         )
#
#
class PfamHandler(CustomView):
    level_description = 'DB member level'
    #queryset = Entry.objects
    # child_handlers = {
    #     r'PF\d{5}': PfamIDHandler,
    #     'clan':     ClanHandler,
    # }
    serializer_class = EntrySerializer
    def get(self, request, endpoint_levels, available_endpoint_handlers={}, level=0, *args, **kwargs):
        self.queryset = self.queryset.filter(source_database__iexact="pfam")

        return super(PfamHandler, self).get(
            request, endpoint_levels, available_endpoint_handlers, level, *args, **kwargs
        )


class AccesionHandler(CustomView):
    level_description = 'interpro accession level'
    # child_handlers = {
    #     'pfam': PfamHandler,
    # }
    serializer_class = EntrySerializer
    queryset = Entry.objects
    many = False

    def get(self, request, endpoint_levels, available_endpoint_handlers={}, level=0, *args, **kwargs):
        self.queryset = self.queryset.filter(accession=endpoint_levels[level-1])
        if self.queryset.count()==0:
            raise Exception("The ID '{}' has not been found in {}".format(endpoint_levels[level-1], endpoint_levels[level-2]))
        return super(AccesionHandler, self).get(
            request, endpoint_levels, available_endpoint_handlers, level, *args, **kwargs
        )


class UnintegratedHandler(CustomView):
    level_description = 'interpro accession level'
    queryset = Entry.objects.all().exclude(source_database__iexact="interpro").filter(integrated__isnull=True)
    serializer_class = EntrySerializer
    # child_handlers = {
    #     'pfam': PfamHandler,
    # }


class InterproHandler(CustomView):
    level_description = 'interpro level'
    queryset = Entry.objects.filter(source_database__iexact="interpro")
    child_handlers = {
        r'IPR\d{6}':    AccesionHandler,
        'pfam': PfamHandler,
    }
    serializer_class = EntrySerializer
#
#
class EntryHandler(CustomView):
    level_description = 'section level'
    from_model = False
    child_handlers = {
        'interpro': InterproHandler,
        'unintegrated': UnintegratedHandler,
        'pfam': PfamHandler,
    }

    def get(self, request, endpoint_levels, *args, **kwargs):
        entry_counter = Entry.objects.all().values('source_database').annotate(total=Count('source_database'))
        output = {
            "interpro": 0,
            "unintegrated": 0,
            "member_databases": {}
        }
        for row in entry_counter:
            if row["source_database"].lower() == "interpro" :
                output["interpro"] = row ["total"]
            else:
                output["member_databases"][row["source_database"].lower()] = row["total"]

        output["unintegrated"] = Entry.objects.all().exclude(source_database__iexact="interpro").filter(integrated__isnull=True).count()
        self.queryset = output
        return super(EntryHandler, self).get(
            request, endpoint_levels, *args, **kwargs
        )
    # serializer_class = EntryOverviewSerializer
