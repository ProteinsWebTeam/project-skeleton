from django.db.models import Count
from django.shortcuts import redirect

from webfront.constants import get_queryset_type, QuerysetType
from webfront.serializers.uniprot import ProteinSerializer
from webfront.views.custom import CustomView, SerializerDetail
from webfront.models import Protein, ProteinEntryFeature, ProteinStructureFeature

db_members = r'(uniprot)|(trembl)|(swissprot)'


def filter_entry_overview(obj, general_handler, database, accession=None):
    prev_queryset, qs_type = general_handler.get_previous_queryset()
    matches = ProteinEntryFeature.objects.all()
    if database != "uniprot":
        matches = matches.filter(protein__source_database__iexact=database)
    if accession is not None:
        matches = matches.filter(protein=accession)

    include_structs = False
    if prev_queryset is not None:
        if qs_type == QuerysetType.ENTRY_STRUCTURE:
            matches = matches.filter(entry__entrystructurefeature__in=prev_queryset)\
                .filter(protein__accession__in=prev_queryset.values("structure__protein")) \
                .filter(protein__structure__accession__in=prev_queryset.values("structure"))
            include_structs = True
        elif qs_type == QuerysetType.ENTRY_PROTEIN:
            matches = matches.all() & prev_queryset.all()
            include_structs = True

    general_handler.set_in_store(CustomView, "queryset_for_previous_count", matches)

    # flattening the object
    obj = {**obj, **obj["member_databases"]}
    del obj["member_databases"]

    for entry_db in obj:
        if entry_db == "unintegrated":
            matches2 = matches \
                .filter(entry__integrated__isnull=True) \
                .exclude(entry__source_database__iexact="interpro")
        else:
            matches2 = matches.filter(entry__source_database__iexact=entry_db)

        entries = matches2.values("entry")
        prots = matches2.values("protein")

        if prev_queryset is not None:
            entries = matches2.values("entry")
            prots = matches2.values("protein")
            if include_structs:
                structs = set(matches2.values_list("entry__structure__accession")) \
                    .intersection(matches2.values_list("protein__structure__accession"))
                CustomView.set_counter_attributte(obj, entry_db, "structures", len(structs))

        CustomView.set_counter_attributte(obj, entry_db, "proteins", prots.distinct().count())
        CustomView.set_counter_attributte(obj, entry_db, "entries", entries.distinct().count())

    new_obj = {"member_databases": {}}
    for key, value in obj.items():
        if key == "interpro" or key == "unintegrated":
            new_obj[key] = value
        else:
            new_obj["member_databases"][key] = value
    return new_obj


def filter_structure_overview(obj, general_handler, database=None, accession=None):
    prev_queryset, qs_type = general_handler.get_previous_queryset()
    matches = ProteinStructureFeature.objects.all()
    if accession is not None:
        matches = matches.filter(protein=accession)
    if database is not None and database != "uniprot":
        matches = matches.filter(protein__source_database__iexact=database)

    prots = matches.values("protein")
    structs = matches.values("structure")
    include_entries = False
    if prev_queryset is not None:
        if qs_type == QuerysetType.ENTRY_STRUCTURE:
            matches = matches.filter(structure__entrystructurefeature__in=prev_queryset)\
                .filter(protein__in=prev_queryset.values("entry__protein"))
            include_entries = True
        elif qs_type == QuerysetType.STRUCTURE_PROTEIN:
            matches = matches.all() & prev_queryset.all()
            include_entries = True
        structs = matches.values("structure")
        prots = matches.values("protein")
        if include_entries:
            entries = set(matches.values_list("protein__entry__accession")) \
                .intersection(set(matches.values_list("structure__entry__accession")))
            CustomView.set_counter_attributte(obj, "pdb", "entries", len(entries))

    general_handler.set_in_store(CustomView, "queryset_for_previous_count", matches)

    CustomView.set_counter_attributte(obj, "pdb", "proteins",
                                      prots.distinct().count())
    CustomView.set_counter_attributte(obj, "pdb", "structures",
                                      structs.distinct().count())
    return obj


class UniprotAccessionHandler(CustomView):
    level_description = 'uniprot accession level'
    serializer_class = ProteinSerializer
    queryset = Protein.objects
    many = False
    serializer_detail_filter = SerializerDetail.PROTEIN_DETAIL

    def get(self, request, endpoint_levels, available_endpoint_handlers=None, level=0,
            parent_queryset=None, handler=None, *args, **kwargs):
        if available_endpoint_handlers is None:
            available_endpoint_handlers = {}
        if parent_queryset is not None:
            self.queryset = parent_queryset
        self.queryset = self.queryset.filter(accession=endpoint_levels[level - 1])
        if self.queryset.count() == 0:
            raise Exception("The ID '{}' has not been found in {}".format(
                endpoint_levels[level - 1], endpoint_levels[level - 2]))
        return super(UniprotAccessionHandler, self).get(
            request, endpoint_levels, available_endpoint_handlers, level,
            self.queryset, handler, *args, **kwargs
        )

    @staticmethod
    def filter(queryset, level_name="", general_handler=None):
        protein_db = general_handler.get_from_store(UniprotHandler, "protein_db")
        qs_type = get_queryset_type(queryset)
        if not isinstance(queryset, dict):
            if protein_db != "uniprot":
                if qs_type == QuerysetType.STRUCTURE_PROTEIN:
                    queryset = queryset.filter(protein=level_name, protein__source_database__iexact=protein_db)
                elif qs_type == QuerysetType.STRUCTURE:
                    queryset = queryset.filter(proteins=level_name, proteins__source_database__iexact=protein_db)
                else:
                    queryset = queryset.filter(proteinentryfeature__protein=level_name,
                                               proteinentryfeature__protein__source_database__iexact=protein_db)
            else:
                if qs_type == QuerysetType.STRUCTURE_PROTEIN:
                    queryset = queryset.filter(protein=level_name)
                elif qs_type == QuerysetType.STRUCTURE:
                    queryset = queryset.filter(proteins=level_name)
                else:
                    queryset = queryset.filter(proteinentryfeature__protein=level_name)
            if queryset.count() == 0:
                raise ReferenceError("The protein {} doesn't exist in the database {}".format(level_name, protein_db))
            return queryset
        else:
            if "entries" in queryset:
                queryset["entries"] = filter_entry_overview(queryset["entries"], general_handler,
                                                            protein_db, level_name)
            if "structures" in queryset:
                queryset["structures"] = filter_structure_overview(queryset["structures"], general_handler,
                                                                   protein_db, level_name)

        return queryset

    @staticmethod
    def post_serializer(obj, level_name="", general_handler=None):
        if type(obj) != dict:
            if not isinstance(obj.serializer, ProteinSerializer):
                arr = obj
                if isinstance(obj, dict):
                    arr = [obj]
                for o in arr:
                    if "proteins" in o:
                        for p in o["proteins"]:
                            if "accession" in p and p["accession"] != level_name:
                                o["proteins"].remove(p)
                            elif "protein" in p and p["protein"]["accession"] != level_name:
                                o["proteins"].remove(p)
        return obj


class IDAccessionHandler(UniprotAccessionHandler):
    level_description = 'uniprot id level'

    def get(self, request, endpoint_levels, available_endpoint_handlers=None, level=0,
            parent_queryset=None, handler=None, *args, **kwargs):
        if parent_queryset is not None:
            self.queryset = parent_queryset
        self.queryset = self.queryset.filter(identifier=endpoint_levels[level - 1])
        if self.queryset.count() == 0:
            raise Exception("The ID '{}' has not been found in {}".format(
                endpoint_levels[level - 1], endpoint_levels[level - 2]))
        new_url = request.get_full_path().replace(endpoint_levels[level - 1], self.queryset.first().accession)
        return redirect(new_url)


class UniprotHandler(CustomView):
    level_description = 'uniprot level'
    child_handlers = [
        (r'[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}', UniprotAccessionHandler),
        (r'.+', IDAccessionHandler),
    ]
    queryset = Protein.objects.all()
    serializer_class = ProteinSerializer
    serializer_detail = SerializerDetail.PROTEIN_HEADERS
    serializer_detail_filter = SerializerDetail.PROTEIN_OVERVIEW

    def get(self, request, endpoint_levels, available_endpoint_handlers=None, level=0,
            parent_queryset=None, handler=None, *args, **kwargs):
        if available_endpoint_handlers is None:
            available_endpoint_handlers = {}
        ds = endpoint_levels[level - 1].lower()
        if ds != "uniprot":
            self.queryset = self.queryset.filter(source_database__iexact=ds)
        if self.queryset.count() == 0:
            raise Exception("The ID '{}' has not been found in {}".format(
                endpoint_levels[level - 1], endpoint_levels[level - 2]))
        return super(UniprotHandler, self).get(
            request, endpoint_levels, available_endpoint_handlers, level,
            self.queryset, handler, *args, **kwargs
        )

    @staticmethod
    def filter(queryset, level_name="", general_handler=None):
        general_handler.set_in_store(UniprotHandler, "protein_db", level_name)
        if not isinstance(queryset, dict):
            qs_type = get_queryset_type(queryset)
            if level_name != "uniprot":
                if qs_type == QuerysetType.ENTRY:
                    queryset = queryset.filter(proteinentryfeature__protein__source_database__iexact=level_name)
                elif qs_type == QuerysetType.STRUCTURE:
                    queryset = queryset.filter(proteins__source_database__iexact=level_name).distinct()
            else:
                queryset = queryset.filter(proteins__source_database__isnull=False).distinct()
            if queryset.count() == 0:
                raise ReferenceError("There isn't any data for {}".format(level_name))

            if qs_type == QuerysetType.STRUCTURE_PROTEIN:
                general_handler.set_in_store(UniprotHandler,
                                             "protein_queryset",
                                             queryset.values("protein").all())
            else:
                general_handler.set_in_store(UniprotHandler,
                                             "protein_queryset",
                                             queryset.values("proteins").exclude(proteins=None).distinct())
        else:
            del queryset["proteins"]
            if "entries" in queryset:
                queryset["entries"] = filter_entry_overview(queryset["entries"], general_handler, level_name)
            if "structures" in queryset:
                queryset["structures"] = filter_structure_overview(queryset["structures"], general_handler, level_name)
        return queryset

    @staticmethod
    def remove_proteins(obj, protein_source):
        if "proteins" in obj:
            for p in obj["proteins"]:
                if "source_database"in p and p["source_database"] != protein_source:
                    obj["proteins"].remove(p)

    @staticmethod
    def post_serializer(obj, level_name="", general_handler=None):
        if hasattr(obj, 'serializer') and not isinstance(obj.serializer, ProteinSerializer):
            if level_name != "uniprot":
                if isinstance(obj, list):
                    for o in obj:
                        UniprotHandler.remove_proteins(o, level_name)
                else:
                    UniprotHandler.remove_proteins(obj, level_name)
        try:
            if "proteins" not in obj:
                obj["proteins"] = general_handler.get_from_store(UniprotHandler,
                                                                 "protein_queryset").count()
        finally:
            return obj


class ProteinHandler(CustomView):
    level_description = 'section level'
    from_model = False
    child_handlers = [
        (db_members, UniprotHandler),
    ]
    to_add = None
    serializer_detail_filter = SerializerDetail.ENTRY_PROTEIN_HEADERS

    @staticmethod
    def get_database_contributions(queryset, prefix=""):
        protein_counter = queryset.values(prefix+'source_database').annotate(total=Count(prefix+'source_database'))
        output = {}
        for row in protein_counter:
            output[row[prefix+"source_database"]] = row["total"]

        output["uniprot"] = sum(output.values())
        return output

    def get(self, request, endpoint_levels, available_endpoint_handlers=None, level=0,
            parent_queryset=None, handler=None, *args, **kwargs):
        if available_endpoint_handlers is None:
            available_endpoint_handlers = {}

        self.queryset = {"proteins": ProteinHandler.get_database_contributions(Protein.objects.all())}

        return super(ProteinHandler, self).get(
            request, endpoint_levels, available_endpoint_handlers, level,
            self.queryset, handler, *args, **kwargs
        )

    @staticmethod
    def filter(queryset, level_name="", general_handler=None):
        qs = Protein.objects.all()
        if isinstance(queryset, dict):
            queryset["proteins"] = ProteinHandler.get_database_contributions(qs)
        else:
            qs_type = get_queryset_type(queryset)
            if qs_type == QuerysetType.ENTRY:
                qs = Protein.objects.filter(accession__in=queryset.values('proteins'))
            elif qs_type == QuerysetType.STRUCTURE:
                qs = Protein.objects.filter(accession__in=queryset.values('proteins'))
            elif qs_type == QuerysetType.STRUCTURE_PROTEIN:
                qs = Protein.objects.filter(accession__in=queryset.values('protein'))
            general_handler.set_in_store(ProteinHandler,
                                         "protein_count",
                                         ProteinHandler.get_database_contributions(qs))
        return queryset

    @staticmethod
    def post_serializer(obj, level_name="", general_handler=None):
        if not isinstance(obj, list):
            try:
                obj["proteins"] = general_handler.get_from_store(ProteinHandler, "protein_count")
            finally:
                return obj
        return obj
