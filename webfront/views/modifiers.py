from urllib.error import URLError
from webfront.views.custom import is_single_endpoint

from django.db.models import Count
from webfront.models import Entry, EntryAnnotation, Alignment
from webfront.views.custom import filter_queryset_accession_in

from django.conf import settings

go_terms = settings.INTERPRO_CONFIG.get("key_go_terms", {})
organisms = settings.INTERPRO_CONFIG.get("key_organisms", {})


def group_by_member_databases(general_handler):
    if is_single_endpoint(general_handler):
        holder = general_handler.queryset_manager.remove_filter(
            "entry", "source_database"
        )
        dbs = Entry.objects.get_queryset().values("source_database").distinct()
        qs = {
            db["source_database"]: general_handler.queryset_manager.get_queryset()
            .filter(member_databases__contains='"{}"'.format(db["source_database"]))
            .count()
            for db in dbs
        }

        general_handler.queryset_manager.add_filter("entry", source_database=holder)
        return qs


def group_by_go_categories(general_handler):
    template = '"code": "{}"'
    groups = {
        "P": "Biological Process",
        "C": "Cellular Component",
        "F": "Molecular Function",
    }
    if is_single_endpoint(general_handler):
        qs = {
            groups[cat]: general_handler.queryset_manager.get_queryset()
            .filter(go_terms__contains=template.format(cat))
            .count()
            for cat in groups
        }
        return qs


def group_by_go_terms(general_handler):
    q = "({})".format(" OR ".join(g.replace(":", "\\:") for g in go_terms))
    searcher = general_handler.searcher
    result = searcher.get_grouped_object(
        general_handler.queryset_manager.main_endpoint, "entry_go_terms", q, size=1000
    )
    return [
        (r["key"], {"value": r["unique"]["value"], "title": go_terms[r["key"]]})
        for r in result["groups"]["buckets"]
        if r["key"] in go_terms
    ]


def get_queryset_to_group(general_handler, endpoint_queryset):
    queryset = general_handler.queryset_manager.get_queryset()
    if endpoint_queryset.objects.count() == queryset.count():
        return endpoint_queryset.objects
    return endpoint_queryset.objects.filter(accession__in=queryset.distinct())


def group_by_organism(general_handler, endpoint_queryset):
    searcher = general_handler.searcher
    qs = general_handler.queryset_manager.get_searcher_query()
    tmp = [
        (
            org,
            {
                "value": searcher.count_unique(
                    qs + " && tax_lineage:{}".format(org),
                    "{}_acc".format(general_handler.queryset_manager.main_endpoint),
                ),
                "title": organisms[org],
            },
        )
        for org in organisms
    ]
    return [t for t in tmp if t[1]["value"] > 0]


def group_by_match_presence(general_handler, endpoint_queryset):
    searcher = general_handler.searcher
    qs = general_handler.queryset_manager.get_searcher_query()
    response = {
        "match_presence": {
            "true": searcher.count_unique(qs + " && _exists_:entry_acc", "protein_acc"),
            "false": searcher.count_unique(
                qs + " && !_exists_:entry_acc", "protein_acc"
            ),
        }
    }
    return response


def group_by_is_reference(general_handler, endpoint_queryset):
    searcher = general_handler.searcher
    qs = general_handler.queryset_manager.get_searcher_query()
    response = {
        "proteome_is_reference": {
            "true": searcher.count_unique(
                qs + " && proteome_is_reference:true", "proteome_acc"
            ),
            "false": searcher.count_unique(
                qs + " && proteome_is_reference:false", "proteome_acc"
            ),
        }
    }
    return response


def group_by_annotations(general_handler):
    if is_single_endpoint(general_handler):
        queryset = EntryAnnotation.objects.values_list(
            "accession_id__source_database", "type"
        ).annotate(total=Count("type"))
        formatted_results = {}
        for source, type, total in list(queryset):
            if source not in formatted_results:
                formatted_results[source] = {}
            formatted_results[source][type] = total
        results = [(key, value) for key, value in formatted_results.items()]
        return results


def group_by(endpoint_queryset, fields):
    def inner(field, general_handler):
        if field not in fields:
            raise URLError(
                "{} is not a valid field to group entries by. Allowed fields : {}".format(
                    field, ", ".join(fields.keys())
                )
            )
        if "member_databases" == field:
            return group_by_member_databases(general_handler)
        if "go_terms" == field:
            return group_by_go_terms(general_handler)
        if "go_categories" == field:
            return group_by_go_categories(general_handler)
        if "annotation" == field:
            return group_by_annotations(general_handler)
        if "tax_id" == field:
            return group_by_organism(general_handler, endpoint_queryset)
        if "match_presence" == field:
            return group_by_match_presence(general_handler, endpoint_queryset)
        if "proteome_is_reference" == field:
            return group_by_is_reference(general_handler, endpoint_queryset)
        if (
            is_single_endpoint(general_handler)
            and general_handler.queryset_manager.main_endpoint != "protein"
        ):
            qs = get_queryset_to_group(general_handler, endpoint_queryset)
            return qs.values_list(field).annotate(total=Count(field))
        else:
            searcher = general_handler.searcher
            result = searcher.get_grouped_object(
                general_handler.queryset_manager.main_endpoint, fields[field]
            )
            return result

    return inner


def sort_by(fields):
    def x(field, general_handler):
        if not is_single_endpoint(general_handler):
            # wl = {k: v for k, v in wl.items() if v is not None}
            raise URLError(
                "Sorting is not currently supported for multi-domains queries"
            )

        if field not in fields and field[1:] not in fields:
            raise URLError(
                "This query can't be be sorted by {}. The supported fields are {}".format(
                    field, ", ".join(fields.keys())
                )
            )
        general_handler.queryset_manager.order_by(field)

    return x


def filter_by_field(endpoint, field):
    def x(value, general_handler):
        general_handler.queryset_manager.add_filter(
            endpoint, **{"{}__iexact".format(field): value.lower()}
        )

    return x


def filter_by_key_species(value, general_handler):
    general_handler.queryset_manager.add_filter(
        "taxonomy", **{"accession__in": list(organisms.keys())}
    )


def filter_by_boolean_field(endpoint, field):
    def x(value, general_handler):
        if value.lower() == "false":
            boolean_value = False
        else:
            boolean_value = True
        general_handler.queryset_manager.add_filter(
            endpoint, **{"{}".format(field): boolean_value}
        )

    return x


def filter_by_contains_field(endpoint, field, value_template="{}"):
    def x(value, general_handler):
        general_handler.queryset_manager.add_filter(
            endpoint, **{"{}__contains".format(field): value_template.format(value)}
        )

    return x


def filter_by_field_range(endpoint, field, value_template="{}"):
    def x(value, general_handler):
        pos = value.split("-")
        if is_single_endpoint(general_handler):
            general_handler.queryset_manager.add_filter(
                endpoint,
                **{
                    "{}__gte".format(field): value_template.format(pos[0]),
                    "{}__lte".format(field): value_template.format(pos[1]),
                }
            )
        else:
            general_handler.queryset_manager.add_filter(
                endpoint,
                **{
                    "{}_{}__gte".format(endpoint, field): value_template.format(pos[0]),
                    "{}_{}__lte".format(endpoint, field): value_template.format(pos[1]),
                }
            )

    return x


def filter_by_field_or_field_range(endpoint, field):
    def x(value, general_handler):
        minmax = value.split("-")
        if len(minmax) == 2 and minmax[0] and minmax[1]:
            filter_by_field_range(endpoint, field)(value, general_handler)
        elif len(minmax) == 1 and minmax[0]:
            filter_by_field(endpoint, field)(value, general_handler)
        else:
            raise URLError("{} is not a valid value for filter {}".format(value, field))

    return x


def get_single_value(field):
    def x(value, general_handler):
        queryset = general_handler.queryset_manager.get_queryset()
        first = queryset.first()
        return first.__getattribute__(field)

    return x


def get_interpro_status_counter(field, general_handler):
    queryset = general_handler.queryset_manager.get_queryset().distinct()
    total = queryset.count()
    unintegrated = queryset.filter(integrated__isnull=True).count()
    return {"integrated": total - unintegrated, "unintegrated": unintegrated}


def filter_by_match_presence(value, general_handler):
    general_handler.queryset_manager.add_filter(
        "entry", **{"source_database__isnull": value.lower() != "true"}
    )


def _get_rows(general_handler):
    return (
        general_handler.pagination["size"]
        if "size" in general_handler.pagination
        else settings.INTERPRO_CONFIG.get("default_page_size", 20)
    )


def _get_index(general_handler):
    return (
        general_handler.pagination["index"]
        if "index" in general_handler.pagination
        else 1
    )


def get_domain_architectures(field, general_handler):
    searcher = general_handler.searcher
    rows = _get_rows(general_handler)
    index = _get_index(general_handler)
    if field is None or field.strip() == "":
        return searcher.get_group_obj_of_field_by_query(
            None,
            "ida_id",
            rows=rows,
            start=index * rows - rows,
            inner_field_to_count="protein_acc",
        )
    else:
        query = (
            general_handler.queryset_manager.get_searcher_query()
            + " && ida_id:"
            + field
        )
        res, length = searcher.get_list_of_endpoint(
            "protein", query, rows, index * rows - rows
        )
        return filter_queryset_accession_in(
            general_handler.queryset_manager.get_base_queryset("protein"), res
        )


def get_entry_annotation(field, general_handler):
    annotation = []
    queryset = general_handler.queryset_manager.get_queryset()
    for entry in queryset:
        data = entry.entryannotation_set.filter(type=field)
        annotation.append(data[0])
    return annotation


def get_set_alignment(field, general_handler):
    qs = Alignment.objects.filter(
        set_acc__in=general_handler.queryset_manager.get_queryset()
    )
    if field is not None and field != "":
        qs = qs.filter(entry_acc__accession__iexact=field)
    general_handler.modifiers.search_size = qs.count()
    return qs.order_by("entry_acc")


def add_extra_fields(endpoint, *argv):
    supported_fields = [
        f.name for f in endpoint._meta.get_fields() if not f.is_relation
    ] + list(argv)

    def x(fields, general_handler):
        fs = fields.split(",")
        for field in fs:
            if field not in supported_fields:
                raise URLError(
                    "{} is not a valid field to to be included. Allowed fields : {}".format(
                        field, ", ".join(supported_fields)
                    )
                )
        general_handler.queryset_manager.other_fields = fs

    return x


def ida_search(value, general_handler):
    searcher = general_handler.searcher
    rows = _get_rows(general_handler)
    index = _get_index(general_handler)

    conserve_order = "ordered" in general_handler.request.query_params
    entries = value.lower().split(",")
    if conserve_order:
        query = "*{}*".format("*".join(entries))
    else:
        query = " && ".join(["ida:*{}*".format(e) for e in entries])
    if "ida_ignore" in general_handler.request.query_params:
        ignore_list = general_handler.request.query_params["ida_ignore"].split(",")
        if len(ignore_list) > 0:
            query = "({}) && ({})".format(
                query, " && ".join(["!ida:*{}*".format(e) for e in ignore_list])
            )
    return searcher.get_group_obj_of_field_by_query(
        query,
        "ida_id",
        rows=rows,
        start=index * rows - rows,
        inner_field_to_count="protein_acc",
    )


def passing(x, y):
    pass
