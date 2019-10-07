from urllib.error import URLError
from webfront.views.custom import is_single_endpoint

from django.db.models import Count
from webfront.models import Entry, EntryAnnotation, Alignment, Isoforms, Release_Note
from webfront.views.custom import filter_queryset_accession_in
from webfront.exceptions import EmptyQuerysetError, HmmerWebError
from django.conf import settings

from requests import Session
from urllib import request, parse
from json import loads

# import ssl

# MAQ bypassing SSL errors
# ssl._create_default_https_context = ssl._create_unverified_context

go_terms = settings.INTERPRO_CONFIG.get("key_go_terms", {})
organisms = settings.INTERPRO_CONFIG.get("key_organisms", {})

class SmartRedirectHandler(request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        return headers

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


def group_by_is_fragment(general_handler, endpoint_queryset):
    searcher = general_handler.searcher
    # qs = general_handler.queryset_manager.get_searcher_query()
    result = searcher.get_grouped_object("protein", "protein_is_fragment")

    boolean_tag = {
        "0": "false",
        0: "false",
        False: "false",
        "False": "false",
        "false": "false",
        "1": "true",
        1: "true",
        True: "true",
        "True": "true",
        "true": "true",
    }

    response = {
        "is_fragment": {
            boolean_tag[bucket["key"]]: bucket["unique"]["value"]
            for bucket in result["groups"]["buckets"]
        }
    }
    # print(response)
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
        if "is_fragment" == field:
            return group_by_is_fragment(general_handler, endpoint_queryset)
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


def get_single_value(field, from_elastic=False):
    if from_elastic:

        def x(value, general_handler):
            q = general_handler.queryset_manager.get_searcher_query()
            obj = general_handler.searcher._elastic_json_query(
                "{} && _exists_:{}&size=1".format(q, field)
            )
            total = obj["hits"]["total"]
            if type(total) == dict:
                total = obj["hits"]["total"]["value"]

            if total < 1:
                raise EmptyQuerysetError(
                    "No documents found with the current selection"
                )
            return {field: obj["hits"]["hits"][0]["_source"][field]}

        return x

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


def filter_by_latest_entries(value, general_handler):
    notes = Release_Note.objects.all()
    notes = notes.order_by("-release_date")
    if notes.count() == 0:
        raise ReferenceError("There are not release Notes")
    note = notes.first()
    new_entries = note.content["interpro"]["new_entries"]

    general_handler.queryset_manager.add_filter("entry", accession__in=new_entries)


def get_domain_architectures(field, general_handler):
    searcher = general_handler.searcher
    size = general_handler.pagination["size"]
    cursor = general_handler.pagination["cursor"]

    if field is None or field.strip() == "":
        return searcher.get_group_obj_copy_of_field_by_query(
            None, "ida_id", rows=size, cursor=cursor, inner_field_to_count="protein_acc"
        )
    else:
        query = (
            general_handler.queryset_manager.get_searcher_query()
            + " && ida_id:"
            + field
        )
        res, length, after_key, before_key = searcher.get_list_of_endpoint(
            "protein", rows=size, query=query, cursor=cursor
        )
        general_handler.modifiers.search_size = length
        general_handler.modifiers.after_key = after_key
        general_handler.modifiers.before_key = before_key
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
    qs = (
        Alignment.objects.filter(
            set_acc__in=general_handler.queryset_manager.get_queryset()
        )
        .values_list("set_acc", "entry_acc")
        .annotate(count=Count("target_acc"))
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
    size = general_handler.pagination["size"]
    cursor = general_handler.pagination["cursor"]

    conserve_order = "ordered" in general_handler.request.query_params
    entries = value.upper().split(",")
    if conserve_order:
        query = "ida:*{}*".format("*".join(entries))
    else:
        query = " && ".join(["ida:*{}*".format(e) for e in entries])
    if "ida_ignore" in general_handler.request.query_params:
        ignore_list = general_handler.request.query_params["ida_ignore"].split(",")
        if len(ignore_list) > 0:
            query = "({}) && ({})".format(
                query, " && ".join(["!ida:*{}*".format(e) for e in ignore_list])
            )
    return searcher.get_group_obj_copy_of_field_by_query(
        query, "ida_id", rows=size, cursor=cursor, inner_field_to_count="protein_acc"
    )


def get_isoforms(value, general_handler):
    isoforms = Isoforms.objects.filter(
        protein_acc__in=general_handler.queryset_manager.get_queryset()
    )
    if value is not None and value != "":
        isoforms = isoforms.filter(accession__iexact=value)
        if len(isoforms) == 0:
            raise EmptyQuerysetError(
                "There aren't isoforms with accession {}".format(value)
            )
        isoform = isoforms.first()
        return {
            "accession": isoform.accession,
            "protein_acc": isoform.protein_acc,
            "length": isoform.length,
            "sequence": isoform.sequence,
            "features": isoform.features,
        }

    return {"results": [iso.accession for iso in isoforms], "count": len(isoforms)}


def run_hmmscan(sequence):
    """
        run hmmscan for a given uniprot sequence
        NOTE: HmmerWeb refuses to accept proteins > 4k residues

    """
    parameters = {'seq': sequence, 'hmmdb': 'pfam', 'threshold': 'cut_ga'}
    enc_params = parse.urlencode(parameters).encode()
    url = settings.INTERPRO_CONFIG.get('hmmerweb', 'http://www.ebi.ac.uk/Tools/hmmer/search/hmmscan')

    req = request.Request(url=url, data=enc_params)
    results_url = request.urlopen(req).get('Location')

    downloadlink = results_url.replace('results', 'download')
    downloadlink = f"{downloadlink}?format=json"

    with Session() as session:
        with session.get(downloadlink) as response:
            phmmerResultsHMM = response.text
            if response.status_code != 200:
                raise HmmerWebError(f"Failure getting Hmmer results from {downloadlink}")
            phmmerResultsHMM = loads(phmmerResultsHMM)
            hits = phmmerResultsHMM["results"]["hits"]
    return hits


def filter_entries(hits):
    """
    Removes entries and hits which would be filtered out by Hmmerweb Pfam post-processing
    :param entries: A dictionary of entries containing lists of domain hits
    :return: A dictionary containing filtered entries and list of domain hits where display == 1
    """
    filtered_hits = []
    for hit in hits:
        filtered_domains = list(filter(lambda x: x["display"]==1, hit["domains"]))
        if len(filtered_domains) > 0:
            hit["domains"] = filtered_domains
            filtered_hits.append(hit)
    return filtered_hits


def calculate_conservation_scores(pfam_acc):
    """
    Get HMM Logo and convert it to conservation score
    :param pfam_acc:
    :return: list of scores
    """
    logo_data = EntryAnnotation.objects.filter(
        accession_id = pfam_acc,
        type = "logo",
    )[0]
    logo_string = logo_data.value.decode("utf8")
    logo = loads(logo_string)
    max_height = logo['max_height_theory']
    scores = []
    for pos, values in enumerate(logo['height_arr']):
        total = 0
        for value in values:
            total += float(value.split(":")[1])
        #scale the total /max height ratio up by an order of magnitude
        score = round((total / max_height) * 10, 2)
        scores.append(score)
    return scores


def align_seq_to_model(domains, sequence):
    """
        align result of hmmscan with uniprot sequence
    """
    hmmfrom = domains["alihmmfrom"]
    hmmto = domains["alihmmto"]
    consensus = domains["alimodel"]
    aliseq = domains["aliaseq"]
    alisqfrom = domains["alisqfrom"]
    alisqto = domains["alisqto"]

    mappedseq = ""
    modelseq = ""
    if alisqfrom != 1:
        mappedseq += sequence[0:alisqfrom-1]
        for i in range(0, alisqfrom-1):
            modelseq += "-"
    mappedseq += aliseq.upper()
    modelseq += consensus
    if alisqfrom != 1:
        mappedseq += sequence[alisqto:len(sequence)]
        for i in range(alisqto, len(sequence)):
            modelseq += "-"

    return mappedseq, modelseq, hmmfrom, hmmto, alisqfrom, alisqto


def get_hmm_matrix(logo, alisqfrom, alisqto, hmmfrom, hmmto, seqmotif, modelmotif):
    """
        generate sequence matrix (i.e. matrix[res] = "conservation_score_seqAA_modelposition")
    """
    matrix = {}
    count = hmmfrom-1
    pos = 0
    logo_len = len(logo)
    for res in range(0, len(seqmotif)):
        if res < alisqfrom-1 or count >= hmmto:
            #matrix[pos] = f"0_{seqmotif[res]}_0"
            pos += 1
        else:
            if seqmotif[res] == '-':
                count += 1
            elif modelmotif[res] == '.':
                pos += 1
                matrix[pos] = f"-1__0"
            else:
                logo_score = logo[count]
                seq_res = seqmotif[res]
                pos += 1
                matrix[pos] = f"{logo_score}_{seq_res}_{count}"
                count += 1
    return matrix


def format_logo(matrix):
    """
        re-arrange the data
    """
    output = []
    for res in matrix:
        score, aa, modelpos = matrix[res].split('_')
        score = float(score)
        modelpos = int(modelpos)

        output.append({
            "position": res,
            "aa": aa,
            "score": score,
            "model_position": modelpos,
        })
    return output


def calculate_residue_conservation(value, general_handler):
    """
    Calculate the conservancy score of each Pfam entry matching the protein sequence
    :param value:
    :param general_handler:
    :return: An object with an array of hits and conservancy scores
    """
    queryset = general_handler.queryset_manager.get_queryset()
    # will always have one protein in queryset
    protein = queryset[0]
    sequence = protein.sequence
    opener = request.build_opener(SmartRedirectHandler())
    request.install_opener(opener)
    hits = run_hmmscan(sequence)
    filtered_entries = filter_entries(hits)
    # allow option for processing more than just pfam in future
    alignments = {
        "sequence": sequence,
        "pfam": {
            "entries": {}
        },
    }

    for entry in filtered_entries:
        pfam_hit_acc = entry["acc"]
        (pfam_acc, _version) = pfam_hit_acc.split(".")
        if pfam_acc not in alignments["pfam"]["entries"]:
            alignments["pfam"]["entries"][pfam_acc] = []

        logo_score = calculate_conservation_scores(pfam_acc)
        for hit in entry["domains"]:
            # calculate scores for each domain hit for each entry
            mappedseq, modelseq, hmmfrom, hmmto, alisqfrom, alisqto = align_seq_to_model(hit, sequence)
            matrixseq = get_hmm_matrix(logo_score, alisqfrom, alisqto, hmmfrom, hmmto, mappedseq, modelseq)
            formatted_matrix = format_logo(matrixseq)
            alignments["pfam"]["entries"][pfam_acc].append(formatted_matrix)

    return alignments


def passing(x, y):
    pass
