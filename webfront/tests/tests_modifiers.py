import unittest
from webfront.tests.InterproRESTTestCase import InterproRESTTestCase
from rest_framework import status
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


class GroupByModifierTest(InterproRESTTestCase):
    def test_can_get_the_entry_type_groups(self):
        response = self.client.get("/api/entry?group_by=type")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("domain", response.data)
        self.assertIn("family", response.data)

    def test_can_get_the_entry_type_groups_of_entries_with_proteins(self):
        response = self.client.get("/api/entry/protein?group_by=type")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("domain", response.data)
        self.assertNotIn("family", response.data)

    def test_can_get_the_entry_type_groups_proteins_by_tax_id(self):
        response = self.client.get("/api/protein?group_by=tax_id")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({}, response.data)

    def test_can_group_interpro_entries_with_member_databases(self):
        response = self.client.get("/api/entry/interpro?group_by=member_databases")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("pfam", response.data)
        self.assertIn("smart", response.data)
        self.assertIn("profile", response.data)

    def test_wrong_field_for_group_by_should_fail(self):
        self._check_HTTP_response_code(
            "/api/entry?group_by=entry_type", code=status.HTTP_404_NOT_FOUND
        )

    def test_can_get_the_match_presence_groups(self):
        response = self.client.get("/api/protein?group_by=match_presence")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("match_presence", response.data)
        self.assertIn("true", response.data["match_presence"])
        self.assertIn("false", response.data["match_presence"])
        self.assertEqual(response.data["match_presence"]["true"], 3)
        self.assertEqual(response.data["match_presence"]["false"], 1)

    def test_can_get_the_fragment_groups(self):
        response = self.client.get("/api/protein?group_by=is_fragment")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("is_fragment", response.data)
        self.assertIn("true", response.data["is_fragment"])
        self.assertIn("false", response.data["is_fragment"])
        self.assertEqual(response.data["is_fragment"]["true"], 1)
        self.assertEqual(response.data["is_fragment"]["false"], 2)

    def test_can_group_proteomes_by_is_reference(self):
        response = self.client.get(
            "/api/proteome/uniprot?group_by=proteome_is_reference"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("proteome_is_reference", response.data)
        self.assertIn("true", response.data["proteome_is_reference"])
        self.assertIn("false", response.data["proteome_is_reference"])
        self.assertEqual(response.data["proteome_is_reference"]["true"], 2)
        self.assertEqual(response.data["proteome_is_reference"]["false"], 1)


class FilterByFieldModifierTest(InterproRESTTestCase):
    def test_can_filter_pfam_by_integrated(self):
        acc = "IPR003165"
        response = self.client.get("/api/entry/pfam?integrated=" + acc)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertIn("results", response.data)
        for result in response.data["results"]:
            self.assertEqual(result["metadata"]["integrated"].lower(), acc.lower())

    def test_fails_filtering_interpro_by_integrated(self):
        self._check_HTTP_response_code(
            "/api/entry/interpro?integrated=IPR003165", code=status.HTTP_204_NO_CONTENT
        )

    def test_can_filter_smart_by_type(self):
        entry_types = ["family", "domain"]
        for entry_type in entry_types:
            response = self.client.get("/api/entry/smart?type=" + entry_type)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("count", response.data)
            self.assertEqual(response.data["count"], 1)
            self.assertIn("results", response.data)
            for result in response.data["results"]:
                self.assertEqual(result["metadata"]["type"], entry_type)

    def test_can_filter_proteins_by_match_presence(self):
        options = ["true", "false"]
        for option in options:
            response = self.client.get(
                "/api/protein/uniprot?extra_fields=counters&match_presence=" + option
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("results", response.data)
            for result in response.data["results"]:
                entries = result["extra_fields"]["counters"]["entries"]
                if option == "true":
                    self.assertGreater(entries, 0)
                else:
                    self.assertEqual(entries, 0)

    def test_can_filter_proteins_by_is_fragment(self):
        urls = ["protein/uniprot", "protein/uniprot/entry"]
        for url in urls:
            options = [True, False]
            for option in options:
                response = self.client.get(
                    "/api/{}?extra_fields=is_fragment&is_fragment={}".format(
                        url, option
                    )
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn("results", response.data)
                for result in response.data["results"]:
                    is_fragment = result["extra_fields"]["is_fragment"]
                    self.assertEqual(is_fragment, option)


class FilterByContainsFieldModifierTest(InterproRESTTestCase):
    def test_can_filter_pfam_by_signature_in(self):
        db = "pfam"
        response = self.client.get("/api/entry/interpro?signature_in=" + db)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertIn("results", response.data)
        for result in response.data["results"]:
            self.assertIn(db, result["metadata"]["member_databases"])


@unittest.skip
class SortByModifierTest(InterproRESTTestCase):
    def test_can_sort_pfam_by_accession(self):
        response = self.client.get("/api/entry/pfam?sort_by=accession")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        payload_accs = [r["metadata"]["accession"] for r in response.data["results"]]
        self.assertEqual(payload_accs, sorted(payload_accs))

    def test_can_sort_pfam_by_integrated_and_reverse_sorting(self):
        response = self.client.get("/api/entry/pfam?sort_by=integrated")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        payload_accs = [r["metadata"]["integrated"] for r in response.data["results"]]
        response = self.client.get("/api/entry/pfam?sort_by=-integrated")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        payload_accs_rev = [
            r["metadata"]["integrated"] for r in response.data["results"]
        ]
        self.assertEqual(payload_accs_rev, list(reversed(payload_accs)))


class InterProStatusModifierTest(InterproRESTTestCase):
    def test_can_apply_interpro_status(self):
        mdbs = ["profile", "smart", "pfam"]
        for db in mdbs:
            response = self.client.get("/api/entry/" + db)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("results", response.data)
            unintegrated = len(
                [
                    r["metadata"]["integrated"]
                    for r in response.data["results"]
                    if r["metadata"]["integrated"] is None
                ]
            )
            response2 = self.client.get("/api/entry/" + db + "?interpro_status")
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            self.assertEqual(response2.data["unintegrated"], unintegrated)
            self.assertEqual(
                response2.data["integrated"],
                len(response.data["results"]) - unintegrated,
            )


class IDAModifiersTest(InterproRESTTestCase):
    def test_ida_modifier(self):
        response = self.client.get("/api/entry/interpro/IPR001165?ida")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], len(response.data["results"]))

    def test_filter_by_ida_modifier(self):
        response = self.client.get("/api/protein/uniprot?ida=50134")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            "a1cuj5", response.data["results"][0]["metadata"]["accession"].lower()
        )


class ExtraFieldsModifierTest(InterproRESTTestCase):
    fields = {
        "entry": [
            "entry_id",
            "accession",
            "type",
            "name",
            "short_name",
            "source_database",
            "member_databases",
            "go_terms",
            "description",
            "wikipedia",
            "literature",
            "hierarchy",
            "cross_references",
            "entry_date",
            "is_featured",
        ],
        "protein": [
            "accession",
            "identifier",
            "organism",
            "name",
            "description",
            "sequence",
            "length",
            "proteome",
            "gene",
            "go_terms",
            "evidence_code",
            "source_database",
            "residues",
            "structure",
            "is_fragment",
            "tax_id",
        ],
        "structure": [
            "accession",
            "name",
            "experiment_type",
            "release_date",
            "literature",
            "chains",
            "source_database",
            "resolution",
        ],
        "taxonomy": [
            "accession",
            "scientific_name",
            "full_name",
            "lineage",
            "rank",
            "children",
        ],
        "proteome": ["accession", "strain", "is_reference", "assembly"],
        "set": ["accession", "name", "description", "source_database", "relationships"],
    }
    list_url = {
        "entry": "/entry/interpro",
        "protein": "/protein/uniprot",
        "structure": "/structure/pdb",
        "taxonomy": "/taxonomy/uniprot",
        "proteome": "/proteome/uniprot",
        "set": "/set/pfam",
    }

    def test_extra_fields(self):
        for endpoint in self.fields:
            for field in self.fields[endpoint]:
                url = "/api{}?extra_fields={}".format(self.list_url[endpoint], field)
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK, url)
                self.assertIn("results", response.data)
                for result in response.data["results"]:
                    self.assertIn("extra_fields", result)
                    self.assertIn(field, result["extra_fields"])
            url = "/api{}?extra_fields=ERROR".format(self.list_url[endpoint])
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_extra_fields_together(self):
        for endpoint in self.fields:
            url = "/api{}?extra_fields={}".format(
                self.list_url[endpoint], ",".join(self.fields[endpoint])
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, url)
            self.assertIn("results", response.data)
            for field in self.fields[endpoint]:
                for result in response.data["results"]:
                    self.assertIn("extra_fields", result)
                    self.assertIn(field, result["extra_fields"])
            url = "/api{}?extra_fields=name,ERROR".format(self.list_url[endpoint])
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_extra_fields_with_other_endpoint(self):
        for endpoint in self.fields:
            other_ep = [ep for ep in self.fields if ep != endpoint]
            for ep in other_ep:
                for field in self.fields[endpoint]:
                    url = "/api{}/{}?extra_fields={}".format(
                        self.list_url[endpoint], ep, field
                    )
                    response = self.client.get(url)
                    if response.status_code == status.HTTP_200_OK:
                        self.assertIn("results", response.data)
                        for result in response.data["results"]:
                            self.assertIn("extra_fields", result)
                            self.assertIn(field, result["extra_fields"])
                    else:
                        self.assertEqual(
                            response.status_code, status.HTTP_204_NO_CONTENT
                        )
                url = "/api{}/{}?extra_fields=name,ERROR".format(
                    self.list_url[endpoint], ep
                )
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ExtraFeaturesModifierTest(InterproRESTTestCase):
    def test_extra_features_modifier_is_different_than_acc_protein(self):
        response1 = self.client.get("/api/protein/uniprot/a1cuj5")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        response2 = self.client.get("/api/protein/uniprot/a1cuj5?extra_features")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertNotEquals(response1.data, response2.data)

    def test_extra_features_modifier(self):
        response2 = self.client.get("/api/protein/uniprot/a1cuj5?extra_features")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn("TMhelix", response2.data)
        self.assertIn("locations", response2.data["TMhelix"])


class IsoformsModifiersTest(InterproRESTTestCase):
    def test_isoform_modifier(self):
        response = self.client.get("/api/protein/uniprot/a1cuj5?isoforms")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], len(response.data["results"]))
        self.assertGreater(response.data["count"], 0)

    def test_isoform_detail_modifier(self):
        response = self.client.get("/api/protein/uniprot/a1cuj5?isoforms=a1cuj5-2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("accession", response.data)
        self.assertIn("features", response.data)

    def test_isoform_detail_wrong_acc_modifier(self):
        response = self.client.get("/api/protein/uniprot/a1cuj5?isoforms=wrong")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class LatestEntriesModifiersTest(InterproRESTTestCase):
    def test_can_read_entry_interpro_new_entries(self):
        response = self.client.get("/api/entry/interpro?latest_entries")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self._check_is_list_of_objects_with_key(response.data["results"], "metadata")
        self.assertEqual(
            response.data["results"][0]["metadata"]["accession"], "IPR003165"
        )


class EntryAnnotationModifiersTest(InterproRESTTestCase):
    def test_annotation_modifier_hmm(self):
        response = self.client.get("/api/entry/pfam/pf02171?annotation=hmm")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["content-type"], "application/octet-stream")

    def test_annotation_modifier_alignment(self):
        response = self.client.get("/api/entry/pfam/pf02171?annotation=alignment")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["content-type"], "application/octet-stream")

    # TODO Problem encoding logo as byte-coded json
    # def test_annotation_modifier_logo(self):
    #     response = self.client.get("/api/entry/pfam/pf02171?annotation=logo")
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response['content-type'], "application/json")

    # TODO This test should fail but doesn't
    # def test_annotation_wrong_acc_modifier(self):
    #     response = self.client.get("/api/entry/pfam/pf00001?annotation=hmm")
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ValueForFieldModifiersTest(InterproRESTTestCase):
    def test_interactions_modifier(self):
        response = self.client.get("/api/entry/interpro/IPR001165?interactions")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("interactions", response.data)
        self.assertIsInstance(response.data["interactions"], list)
        self.assertEqual(1, len(response.data["interactions"]))

    def test_no_interactions_modifier(self):
        response = self.client.get("/api/entry/interpro/IPR003165?interactions")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_pathways_modifier(self):
        response = self.client.get("/api/entry/interpro/IPR001165?pathways")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("pathways", response.data)
        self.assertIsInstance(response.data["pathways"], object)
        self.assertIn("reactome", response.data["pathways"])
        self.assertEqual(2, len(response.data["pathways"]["reactome"]))

    def test_no_pathways_modifier(self):
        response = self.client.get("/api/entry/interpro/IPR003165?pathways")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

class TaxonomyScientificNameModifierTest(InterproRESTTestCase):
    def test_scientific_name_modifier(self):
        response = self.client.get("/api/taxonomy/uniprot/?scientific_name=Penicillium+italicum")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data)
        self.assertIn("accession", response.data["metadata"])
        self.assertIn("counters", response.data["metadata"])
        self.assertEqual("40296", response.data["metadata"]["accession"])
        self.assertEqual(2, response.data["metadata"]["counters"]["entries"])