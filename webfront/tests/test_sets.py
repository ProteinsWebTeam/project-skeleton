from rest_framework import status

from webfront.models import Set
from webfront.tests.InterproRESTTestCase import InterproRESTTestCase


class SetsFixturesTest(InterproRESTTestCase):

    def test_the_fixtures_are_loaded(self):
        sets = Set.objects.all()
        self.assertEqual(sets.count(), 5)
        names = [t.name for t in sets]
        self.assertIn("The Clan", names)
        self.assertNotIn("unicorn", names)

    def test_can_get_the_set_count(self):
        response = self.client.get("/api/set")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("sets", response.data)
        self.assertIn("pfam", response.data["sets"])
        self.assertIn("kegg", response.data["sets"])
        self.assertNotIn("unicorn", response.data["sets"])
        self.assertNotIn("node", response.data["sets"])

    def test_can_read_set_list(self):
        response = self.client.get("/api/set/pfam")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_is_list_of_objects_with_key(response.data["results"], "metadata")
        self.assertEqual(len(response.data["results"]), 2)

        response = self.client.get("/api/set/kegg")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_is_list_of_objects_with_key(response.data["results"], "metadata")
        self.assertEqual(len(response.data["results"]), 1)

    def test_can_read_set_id(self):
        response = self.client.get("/api/set/pfam/CL0001")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_set_details(response.data["metadata"])

    def test_can_read_set_nodes(self):
        response = self.client.get("/api/set/kegg/KEGG01/node")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_is_list_of_objects_with_key(response.data["results"], "metadata")
        self.assertEqual(len(response.data["results"]), 2)

    def test_can_read_set__node_id(self):
        response = self.client.get("/api/set/kegg/KEGG01/node/KEGG01.1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_set_details(response.data["metadata"])


class EntrySetTest(InterproRESTTestCase):
    def test_can_get_the_set_count(self):
        response = self.client.get("/api/entry/set")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_set_count_overview(response.data)
        self._check_entry_count_overview(response.data)


class ProteinSetTest(InterproRESTTestCase):
    def test_can_get_the_taxonomy_count(self):
        response = self.client.get("/api/protein/set")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_set_count_overview(response.data)
        self._check_protein_count_overview(response.data)


class StructureSetTest(InterproRESTTestCase):
    def test_can_get_the_taxonomy_count(self):
        response = self.client.get("/api/structure/set")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_set_count_overview(response.data)
        self._check_structure_count_overview(response.data)


class OrganismSetTest(InterproRESTTestCase):
    def test_can_get_the_taxonomy_count(self):
        response = self.client.get("/api/organism/set")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._check_set_count_overview(response.data)
        self._check_organism_count_overview(response.data)
