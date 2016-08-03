from rest_framework import status
from webfront.tests.InterproRESTTestCase import InterproRESTTestCase


class ProteinRESTTest(InterproRESTTestCase):

    def test_can_read_protein_overview(self):
        response = self.client.get("/api/protein")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_protein_count_overview(response.data)

    def test_can_read_protein_uniprot(self):
        response = self.client.get("/api/protein/uniprot")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_is_list_of_objects_with_key(response.data["results"], "metadata")
        self.assertEqual(len(response.data["results"]), 4)

    def test_can_read_protein_uniprot_accession(self):
        response = self.client.get("/api/protein/uniprot/P16582")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data)
        self._check_protein_details(response.data["metadata"])

    def test_can_read_protein_id(self):
        url_id = "/api/protein/uniprot/CBPYA_ASPCL"
        response = self.client.get(url_id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("A1CUJ5", response.url)

    def test_can_read_protein_swissprot(self):
        response = self.client.get("/api/protein/swissprot")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_is_list_of_objects_with_key(response.data["results"], "metadata")
        self.assertEqual(len(response.data["results"]), 2)

    def test_can_read_protein_swissprot_accession(self):
        response = self.client.get("/api/protein/swissprot/A1CUJ5")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metadata", response.data)
        self._check_protein_details(response.data["metadata"])

    def test_cant_read_protein_bad_db(self):
        self._check_HTTP_response_code("/api/protein/bad_db", code=status.HTTP_404_NOT_FOUND)

    def test_cant_read_protein_uniprot_bad_id(self):
        self._check_HTTP_response_code("/api/protein/uniprot/bad_id", code=status.HTTP_404_NOT_FOUND)
