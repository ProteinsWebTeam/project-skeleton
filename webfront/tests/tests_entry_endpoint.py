from webfront.models import Entry
from webfront.tests.InterproRESTTestCase import InterproRESTTestCase
from rest_framework import status


class ModelTest(InterproRESTTestCase):

    def test_dummy_dataset_is_loaded(self):
        self.assertGreater(Entry.objects.all().count(), 0, "The dataset has to have at least one Entry")
        self.assertIn(Entry.objects.filter(source_database="interpro").first().accession, ["IPR003165", "IPR001165"])

    def test_content_of_a_json_attribute(self):
        entry = Entry.objects.get(accession="IPR003165")
        self.assertEqual(entry.member_databases["pfam"][0], "PF02171")


class EntryRESTTest(InterproRESTTestCase):
    db_members = {
        "pfam": 3,
        "smart": 2,
        "prosite_profiles": 2,
    }

    def test_can_read_entry_overview(self):
        response = self.client.get("/api/entry")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_entry_count_overview(response.data)

    def test_can_read_entry_interpro(self):
        response = self.client.get("/api/entry/interpro")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_is_list_of_objects_with_key(response.data["results"], "metadata")
        self.assertEqual(len(response.data["results"]), 2)

    def test_can_read_entry_unintegrated(self):
        response = self.client.get("/api/entry/unintegrated")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_is_list_of_objects_with_key(response.data["results"], "metadata")
        self.assertEqual(len(response.data["results"]), 4)

    def test_can_read_entry_interpro_id(self):
        acc = "IPR003165"
        response = self.client.get("/api/entry/interpro/"+acc)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_entry_details(response.data["metadata"])

    def test_fail_entry_interpro_unknown_id(self):
        self._check_HTTP_response_code("/api/entry/interpro/IPR999999")

    def test_bad_entry_point(self):
        self._check_HTTP_response_code("/api/bad_entry_point")

    def test_can_read_entry_member(self):
        for member in self.db_members:
            response = self.client.get("/api/entry/"+member)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), self.db_members[member])
            self._check_is_list_of_objects_with_key(response.data["results"], "metadata")

    def test_can_read_entry_interpro_member(self):
        for member in self.db_members:
            response = self.client.get("/api/entry/interpro/"+member)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 1,
                             "The testdataset only has one interpro entry with 1 member entry")
            self._check_is_list_of_objects_with_key(response.data["results"], "metadata")
            # self._check_is_list_of_objects_with_key(response.data["results"], "proteins")

    def test_can_read_entry_unintegrated_member(self):
        for member in self.db_members:
            response = self.client.get("/api/entry/unintegrated/"+member)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), self.db_members[member]-1)
            self._check_is_list_of_objects_with_key(response.data["results"], "metadata")

    def test_can_read_entry_interpro_id_member(self):
        acc = "IPR003165"
        for member in self.db_members:
            response = self.client.get("/api/entry/interpro/"+acc+"/"+member)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 1)
            self._check_is_list_of_objects_with_key(response.data["results"], "metadata")

    def test_can_read_entry_interpro_id_pfam_id(self):
        acc = "IPR003165"
        pfam = "PF02171"
        response = self.client.get("/api/entry/interpro/"+acc+"/pfam/"+pfam)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(acc, response.data["metadata"]["integrated"])
        self._check_entry_details(response.data["metadata"])

    def test_cant_read_entry_interpro_id_pfam_id_not_in_entry(self):
        acc = "IPR003165"
        pfam = "PF17180"
        self._check_HTTP_response_code("/api/entry/interpro/"+acc+"/pfam/"+pfam)

    def test_can_read_entry_pfam_id(self):
        pfam = "PF17180"
        response = self.client.get("/api/entry/pfam/"+pfam)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data.keys())
        self.assertIn("counters", response.data["metadata"].keys())
        self.assertIn("proteins", response.data["metadata"]["counters"].keys())
        self._check_entry_details(response.data["metadata"])

    def test_can_read_entry_unintegrated_pfam_id(self):
        pfam = "PF17180"
        response = self.client.get("/api/entry/unintegrated/pfam/"+pfam)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data.keys())
        self.assertIn("counters", response.data["metadata"].keys())
        self.assertIn("proteins", response.data["metadata"]["counters"].keys())
        self._check_entry_details(response.data["metadata"])

    def test_cant_read_entry_unintegrated_pfam_id_integrated(self):
        pfam = "PF02171"
        self._check_HTTP_response_code("/api/entry/unintegrated/pfam/"+pfam)

    def test_can_get_protein_amount_from_interpro_id(self):
        acc = "IPR003165"
        response = self.client.get("/api/entry/interpro/"+acc)
        self.assertIn("counters", response.data["metadata"], "'proteins' should be one of the keys in the response")
        self.assertEqual(response.data["metadata"]["counters"]["proteins"], 2)

    def test_can_get_protein_amount_from_interpro_id_pfam_id(self):
        acc = "IPR003165"
        pf = "PF02171"
        response = self.client.get("/api/entry/interpro/"+acc+"/pfam/"+pf)
        self.assertIn("counters", response.data["metadata"], "'proteins' should be one of the keys in the response")
        self.assertEqual(response.data["metadata"]["counters"]["proteins"], 1)