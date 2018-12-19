from enum import Enum


class SerializerDetail(Enum):
    ALL = 1

    ENTRY_HEADERS = 100
    ENTRY_OVERVIEW = 101
    ENTRY_DETAIL = 102
    ENTRY_MATCH = 103
    ENTRY_PROTEIN_HEADERS = 105
    ENTRY_DB = 106

    PROTEIN_HEADERS = 200
    PROTEIN_OVERVIEW = 201
    PROTEIN_DETAIL = 202
    PROTEIN_ENTRY_DETAIL = 203
    PROTEIN_DB = 204

    STRUCTURE_HEADERS = 300
    STRUCTURE_OVERVIEW = 301
    STRUCTURE_DETAIL = 302
    STRUCTURE_CHAIN = 303
    STRUCTURE_ENTRY_DETAIL = 304
    STRUCTURE_PROTEIN_DETAIL = 305
    STRUCTURE_DB = 306

    TAXONOMY_HEADERS = 400
    TAXONOMY_OVERVIEW = 401
    TAXONOMY_DETAIL = 402
    # TAXONOMY_CHAIN = 403
    # TAXONOMY_ENTRY_DETAIL = 404
    # TAXONOMY_PROTEIN_DETAIL = 405
    TAXONOMY_DB = 406
    TAXONOMY_DETAIL_NAMES = 432

    PROTEOME_OVERVIEW = 450
    PROTEOME_HEADERS = 451
    PROTEOME_DETAIL = 453
    ORGANISM_TAXONOMY_PROTEOME = 420
    ORGANISM_TAXONOMY_PROTEOME_HEADERS = 421
    PROTEOME_DB = 460

    SET_HEADERS = 500
    SET_OVERVIEW = 501
    SET_DETAIL = 502
    SET_DB = 503
    SET_ALIGNMENT = 504

    IDA_LIST = 600

    GROUP_BY = 800
    GROUP_BY_MEMBER_DATABASES = 801

    ANNOTATION_BLOB = 1000

class QuerysetType(Enum):
    ENTRY = 100
    PROTEIN = 200
    STRUCTURE = 300
    ENTRY_PROTEIN = 150
    ENTRY_STRUCTURE = 160
    STRUCTURE_PROTEIN = 250
