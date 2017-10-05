import json

import copy

from webfront.searcher.search_controller import SearchController
from webfront.views.custom import CustomView
from webfront.searcher.elastic_controller import ElasticsearchController


def get_id(*args):
    return "-".join([a for a in args if a is not None])


class FixtureReader:
    entries = {}
    proteins = {}
    structures = {}
    entry_protein_list = []
    protein_structure_list = {}
    tax2lineage = {}
    sets = {}
    search = None

    def __init__(self, fixture_paths):
        for path in fixture_paths:
            with open(path) as data_file:
                data = json.load(data_file)
                self.load_from_json(data)

    def load_from_json(self, data):
        for fixture in data:
            if fixture['model'] == "webfront.Entry":
                self.entries[fixture['fields']["accession"]] = fixture['fields']
            elif fixture['model'] == "webfront.Protein":
                self.proteins[fixture['fields']["accession"]] = fixture['fields']
                self.protein_structure_list[fixture['fields']["accession"]] = []
            elif fixture['model'] == "webfront.Structure":
                self.structures[fixture['fields']["accession"]] = fixture['fields']
            elif fixture['model'] == "webfront.ProteinEntryFeature":
                self.entry_protein_list.append(fixture['fields'])
            elif fixture['model'] == "webfront.ProteinStructureFeature":
                self.protein_structure_list[fixture['fields']["protein"]].append(fixture['fields'])
            elif fixture['model'] == "webfront.Taxonomy":
                self.tax2lineage[fixture['fields']["accession"]] = fixture['fields']['lineage'].split()
            elif fixture['model'] == "webfront.Set":
                self.sets[fixture['fields']["accession"]] = fixture['fields']

    def get_entry2set(self):
        e2s = {}
        for s in self.sets:
            for n in self.sets[s]["relationships"]["nodes"]:
                if n["type"] == "entry":
                    db = self.sets[s]["source_database"]
                    if db == "node":
                        db = "kegg"
                    if n["accession"] not in e2s:
                        e2s[n["accession"]] = []
                    e2s[n["accession"]].append({"accession": s, "source_database": db})
                    if self.sets[s]["integrated"] is not None:
                        for i in self.sets[s]["integrated"]:
                            e2s[n["accession"]].append({
                                "accession": i,
                                "source_database": db
                            })
        return e2s

    def get_fixtures(self):
        to_add = []
        entry2set = self.get_entry2set()
        for ep in self.entry_protein_list:
            e = ep["entry"]
            p = ep["protein"]
            obj = {
                "text": e + " " + p,
                "entry_acc": e,
                "entry_type": self.entries[e]["type"],
                "entry_db": self.entries[e]["source_database"],
                "integrated": self.entries[e]["integrated"],
                "protein_acc": p,
                "protein_db": self.proteins[p]["source_database"],
                "tax_id": self.proteins[p]["organism"]["taxid"],
                "lineage": self.tax2lineage[self.proteins[p]["organism"]["taxid"]],
                "proteomes": [pm.lower() for pm in self.proteins[p]["proteomes"]],
                "entry_protein_locations": ep["coordinates"],
                "protein_length": self.proteins[p]["length"],
                "id": get_id(e, p)
            }
            if "IDA" in ep:
                obj["IDA"] = ep["IDA"]
                obj["IDA_FK"] = ep["IDA_FK"]

            if p in self.protein_structure_list:
                for sp in self.protein_structure_list[p]:
                    c = copy.copy(obj)
                    c["structure_acc"] = sp["structure"]
                    c["structure_chain"] = sp["structure"] + " - " + sp["chain"]
                    c["chain"] = sp["chain"]
                    c["id"] = get_id(e, p, sp["structure"], sp["chain"])
                    c["protein_structure_locations"] = sp["coordinates"]
                    if e in entry2set:
                        for e2s in entry2set[e]:
                            c2 = copy.copy(c)
                            c2["set_acc"] = e2s["accession"]
                            c2["set_db"] = e2s["source_database"]
                            to_add.append(c2)
                    else:
                        to_add.append(c)
            else:
                if e in entry2set:
                    for e2s in entry2set[e]:
                        c2 = copy.copy(obj)
                        c2["set_acc"] = e2s["accession"]
                        c2["set_db"] = e2s["source_database"]
                        to_add.append(c2)
                else:
                    to_add.append(obj)

        proteins = [p["protein"] for p in self.entry_protein_list]
        for p, chains in self.protein_structure_list.items():
            if p not in proteins:
                for sp in chains:
                    to_add.append({
                        "text": p + " " + sp["structure"],
                        "protein_acc": p,
                        "protein_db": self.proteins[p]["source_database"],
                        "tax_id": self.proteins[p]["organism"]["taxid"],
                        "lineage": self.tax2lineage[self.proteins[p]["organism"]["taxid"]],
                        "proteomes": [pm.lower() for pm in self.proteins[p]["proteomes"]],
                        "protein_length": self.proteins[p]["length"],
                        "id": get_id(None, p, sp["structure"], sp["chain"]),
                        "structure_acc": sp["structure"],
                        "structure_chain": sp["structure"] + " - " + sp["chain"],
                        "chain": sp["chain"],
                        "protein_structure_locations": sp["coordinates"],
                    })

        lower = []
        for doc in to_add:
            lower.append({k: v.lower() if type(v) == str else v for k, v in doc.items()})
        return lower

    def add_to_search_engine(self, docs):
        self.search = ElasticsearchController()
        self.search.add(docs)

    def clear_search_engine(self):
        self.search.clear_all_docs()
