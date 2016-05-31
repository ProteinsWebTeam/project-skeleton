from rest_framework import status
from webfront.tests.InterproRESTTestCase import InterproRESTTestCase


class StructureRESTTest(InterproRESTTestCase):

    def test_can_read_structure_overview(self):
        response = self.client.get("/api/structure")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_structure_count_overview(response.data)

    def test_can_read_structure_pdb(self):
        response = self.client.get("/api/structure/pdb")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_is_list_of_objects_with_accession(response.data["results"])
        self.assertEqual(len(response.data["results"]), 3)

    def test_can_read_structure_pdb_accession(self):
        response = self.client.get("/api/structure/pdb/2BKM")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data)
        self._check_structure_details(response.data["metadata"])

    def test_can_read_structure_pdb_accession_chain(self):
        response = self.client.get("/api/structure/pdb/2bkm/A")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data)
        self._check_structure_details(response.data["metadata"])


    # TODO:
    def test_cant_read_structure_bad_db(self):
        self._check_HTTP_response_code("/api/structure/bad_db")

    def test_cant_read_structure_pdb_bad_chain(self):
        self._check_HTTP_response_code("/api/structure/pdb/2bkm/C")
