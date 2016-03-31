from django.test import TransactionTestCase

from unifam import settings
from webfront.models import Entry
from rest_framework import status
from rest_framework.test import APITransactionTestCase


class ModelTest(TransactionTestCase):
    fixtures = ['webfront/tests/fixtures.json', 'webfront/tests/protein_fixtures.json']

    def test_dummy_dataset_is_loaded(self):
        self.assertGreater(Entry.objects.all().count(), 0, "The dataset has to have at least one Entry")
        self.assertIn(Entry.objects.filter(source_database="interpro").first().accession, ["IPR003165","IPR001165"])

    def test_content_of_a_json_attribute(self):
        entry = Entry.objects.get(accession="IPR003165")
        self.assertEqual(entry.member_databases["pfam"][0], "PF02171")


class EntryRESTTest(APITransactionTestCase):
    fixtures = ['webfront/tests/fixtures.json', 'webfront/tests/protein_fixtures.json']
    db_members = {
        "pfam": 3,
        "smart": 2,
        "prosite_profiles": 2,
    }

    def test_can_read_entry_overview(self):
        response = self.client.get("/api/entry")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("member_databases", response.data)
        self.assertIn("interpro", response.data)
        self.assertIn("unintegrated", response.data)

    def test_can_read_entry_interpro(self):
        response = self.client.get("/api/entry/interpro")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_can_read_entry_unintegrated(self):
        response = self.client.get("/api/entry/unintegrated")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)

    def test_can_read_entry_interpro_id(self):
        acc = "IPR003165"
        response = self.client.get("/api/entry/interpro/"+acc)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(acc, response.data["metadata"]["accession"])

    def test_fail_entry_interpro_unknown_id(self):
        prev = settings.DEBUG
        settings.DEBUG = False
        response = self.client.get("/api/entry/interpro/IPR999999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        settings.DEBUG = prev

    def test_bad_entry_point(self):
        prev = settings.DEBUG
        settings.DEBUG = False
        response = self.client.get("/api/bad_entry_point")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        settings.DEBUG = prev

    def test_can_read_entry_member(self):
        for member in self.db_members:
            response = self.client.get("/api/entry/"+member)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), self.db_members[member])

    def test_can_read_entry_interpro_member(self):
        for member in self.db_members:
            response = self.client.get("/api/entry/interpro/"+member)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 1, "The dataset only has one interpro entry with 1 member entry")

    def test_can_read_entry_unintegrated_member(self):
        for member in self.db_members:
            response = self.client.get("/api/entry/unintegrated/"+member)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), self.db_members[member]-1)

    def test_can_read_entry_interpro_id_member(self):
        acc = "IPR003165"
        for member in self.db_members:
            response = self.client.get("/api/entry/interpro/"+acc+"/"+member)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 1)
            self.assertEqual(acc, response.data["results"][0]["metadata"]["integrated"])

    def test_can_read_entry_interpro_id_pfam_id(self):
        acc = "IPR003165"
        pfam = "PF02171"
        response = self.client.get("/api/entry/interpro/"+acc+"/pfam/"+pfam)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(acc, response.data["metadata"]["integrated"])

    def test_cant_read_entry_interpro_id_pfam_id_not_in_entry(self):
        prev = settings.DEBUG
        settings.DEBUG = False
        acc = "IPR003165"
        pfam = "PF17180"
        response = self.client.get("/api/entry/interpro/"+acc+"/pfam/"+pfam)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        settings.DEBUG = prev

    def test_can_read_entry_unintegrated_pfam_id(self):
        pfam = "PF17180"
        response = self.client.get("/api/entry/unintegrated/pfam/"+pfam)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data.keys())
        self.assertIn("proteins", response.data.keys())

    def test_cant_read_entry_unintegrated_pfam_id_integrated(self):
        prev = settings.DEBUG
        settings.DEBUG = False
        pfam = "PF02171"
        response = self.client.get("/api/entry/unintegrated/pfam/"+pfam)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        settings.DEBUG = prev


class ProteinRESTTest(APITransactionTestCase):
    fixtures = ['webfront/tests/fixtures.json', 'webfront/tests/protein_fixtures.json']

    def test_can_read_protein_overview(self):
        response = self.client.get("/api/protein")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("uniprot", response.data)

    def test_can_read_protein_uniprot(self):
        response = self.client.get("/api/protein/uniprot")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_can_read_protein_uniprot_accession(self):
        response = self.client.get("/api/protein/uniprot/P16582")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data)

    def test_can_read_protein_id(self):
        response = self.client.get("/api/protein/uniprot/CBPYA_ASPCL")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data)

    def test_can_read_protein_id(self):
        response = self.client.get("/api/protein/uniprot/CBPYA_ASPCL")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data)


class ProteinEntryRESTTest(APITransactionTestCase):
    fixtures = ['webfront/tests/fixtures.json', 'webfront/tests/protein_fixtures.json']

    def test_can_get_protein_amount_from_interpro_id(self):
        acc = "IPR003165"
        response = self.client.get("/api/entry/interpro/"+acc)
        self.assertIn("proteins", response.data, "'proteins' should be one of the keys in the response")
        self.assertEqual(response.data["proteins"], 2)

    def test_can_get_protein_amount_from_interpro_id_pfam(self):
        acc = "IPR003165"
        response = self.client.get("/api/entry/interpro/"+acc+"/pfam")
        self.assertIn("proteins", response.data["results"][0], "'proteins' should be one of the keys in the response")
        self.assertEqual(response.data["results"][0]["proteins"], 1)

    def test_can_get_protein_overview_from_interpro_id_protein(self):
        acc = "IPR003165"
        response = self.client.get("/api/entry/interpro/"+acc+"/protein")
        self.assertEqual(len(response.data["proteins"]), 2)

    def test_can_get_proteins_from_interpro_id_protein(self):
        acc = "IPR003165"
        response = self.client.get("/api/entry/interpro/"+acc+"/protein/uniprot")
        self.assertIn("proteins", response.data, "'proteins' should be one of the keys in the response")
        self.assertEqual(len(response.data["proteins"]), 2)
        ids = [x["accession"] for x in response.data["proteins"]]
        self.assertIn("A1CUJ5", ids)
        self.assertIn("P16582", ids)

    def test_can_get_proteins_from_interpro_id_protein_id(self):
        acc = "IPR003165"
        uni = "A1CUJ5"
        response = self.client.get("/api/entry/interpro/"+acc+"/protein/uniprot/"+uni)
        self.assertIn("proteins", response.data, "'proteins' should be one of the keys in the response")
        self.assertEqual(len(response.data["proteins"]), 1)
        ids = [x["accession"] for x in response.data["proteins"]]
        self.assertIn(uni, ids)
        self.assertNotIn("P16582", ids)

    def test_can_get_protein_overview_from_pfam_id(self):
        pfam = "PF02171"
        response = self.client.get("/api/entry/pfam/"+pfam+"/protein/")
        self.assertIn("proteins", response.data, "'proteins' should be one of the keys in the response")
        self.assertEqual(len(response.data["proteins"]), 1)
        ids = [x["accession"] for x in response.data["proteins"]]
        self.assertIn("A1CUJ5", ids)
        self.assertNotIn("P16582", ids)

    def test_can_get_proteins_from_pfam_id(self):
        pfam = "PF02171"
        response = self.client.get("/api/entry/pfam/"+pfam+"/protein/uniprot")
        self.assertIn("proteins", response.data, "'proteins' should be one of the keys in the response")
        self.assertEqual(len(response.data["proteins"]), 1)
        ids = [x["accession"] for x in response.data["proteins"]]
        self.assertIn("A1CUJ5", ids)
        self.assertNotIn("P16582", ids)

    def test_can_get_proteins_from_unintegrated_pfam_id(self):
        pfam = "PF17180"
        response = self.client.get("/api/entry/unintegrated/pfam/"+pfam+"/protein/uniprot")
        self.assertIn("proteins", response.data, "'proteins' should be one of the keys in the response")
        self.assertEqual(len(response.data["proteins"]), 1)
        ids = [x["accession"] for x in response.data["proteins"]]
        self.assertIn("M5ADK6", ids)
        self.assertNotIn("P16582", ids)

    def test_gets_empty_protein_array_for_entry_with_no_matches(self):
        pfam = "PF17176"
        response = self.client.get("/api/entry/unintegrated/pfam/"+pfam+"/protein/uniprot")
        self.assertIn("proteins", response.data, "'proteins' should be one of the keys in the response")
        self.assertEqual(len(response.data["proteins"]), 0)

    def test_can_get_entries_from_protein_id(self):
        acc = "P16582"
        response = self.client.get("/api/protein/uniprot/"+acc+"/entry/")
        self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
        self.assertEqual(len(response.data["entries"]), 2)
        ids = [x["accession"] for x in response.data["entries"]]
        self.assertIn("IPR003165", ids)
        self.assertIn("PS50822", ids)


    # def test_can_get_entries_from_protein_id_interpro(self):
    #     acc = "P16582"
    #     response = self.client.get("/api/protein/uniprot/"+acc+"/entry/interpro")
    #     self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
    #     self.assertEqual(len(response.data["entries"]), 1)
    #     ids = [x["accession"] for x in response.data["entries"]]
    #     self.assertIn("IPR003165", ids)
    #     self.assertNotIn("PS50822", ids)

    def test_gets_empty_entries_array_for_protein_with_no_matches(self):
        acc = "A0A0A2L2G2"
        response = self.client.get("/api/protein/uniprot/"+acc+"/entry/")
        self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
        self.assertEqual(len(response.data["entries"]), 0)
