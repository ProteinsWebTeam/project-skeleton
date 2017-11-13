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

    ORGANISM_HEADERS = 400
    ORGANISM_OVERVIEW = 401
    ORGANISM_DETAIL = 402
    ORGANISM_CHAIN = 403
    ORGANISM_ENTRY_DETAIL = 404
    ORGANISM_PROTEIN_DETAIL = 405
    ORGANISM_DB = 406
    ORGANISM_PROTEOME = 410
    ORGANISM_PROTEOME_HEADERS = 411
    ORGANISM_PROTEOME_OVERVIEW = 412
    ORGANISM_PROTEOME_DETAIL = 413
    ORGANISM_TAXONOMY_PROTEOME = 420
    ORGANISM_TAXONOMY_PROTEOME_HEADERS = 421
    ORGANISM_DETAIL_NAMES = 432

    SET_HEADERS = 500
    SET_OVERVIEW = 501
    SET_DETAIL = 502
    SET_DB = 503

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
