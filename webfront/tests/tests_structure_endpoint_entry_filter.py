from rest_framework import status
from webfront.tests.InterproRESTTestCase import InterproRESTTestCase


class StructureWithFilterEntryRESTTest(InterproRESTTestCase):

    def test_can_get_structure_amount_from_entry(self):
        response = self.client.get("/api/structure/entry")
        self._check_structure_count_overview(response.data)
        self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
        self._check_entry_count_overview(response.data["entries"])

    def test_urls_that_return_list_of_accessions_and_entries(self):
        urls = [
            "/api/structure/pdb/entry/",
            ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self._check_is_list_of_objects_with_accession(response.data["results"])
            self._check_is_list_of_objects_with_key(response.data["results"], "entries")

    def test_can_get_entries_from_structure_id(self):
        urls = ["/api/structure/pdb/"+pdb+"/entry/" for pdb in ["1JM7", "2BKM", "1T2V"]]
        for url in urls:
            response = self.client.get(url)
            self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
            self._check_structure_details(response.data["metadata"])
            self._check_entry_count_overview(response.data["entries"])

    def test_can_get_entries_from_structure_id_chain(self):
        urls = ["/api/structure/pdb/"+pdb+"/A/entry/" for pdb in ["1JM7", "2BKM", "1T2V"]]
        for url in urls:
            response = self.client.get(url)
            self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
            self._check_structure_details(response.data["metadata"])
            self._check_entry_count_overview(response.data["entries"])
            for chain in response.data["metadata"]["chains"].values():
                self._check_structure_chain_details(chain)
                self.assertEqual(chain["chain"], "A")

    def test_gets_empty_entries_array_for_structure_with_no_matches(self):
        acc = "1JZ8"
        response = self.client.get("/api/structure/pdb/"+acc+"/entry/")
        self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
        self._check_structure_details(response.data["metadata"])
        self._check_entry_count_overview(response.data["entries"])
        self.assertDictEqual(response.data["entries"]["member_databases"], {},
                             "there should not be reports of member db")
        self.assertEqual(response.data["entries"]["interpro"], 0, "no interpro entries")
        self.assertEqual(response.data["entries"]["unintegrated"], 0, "no unintegrated entries")

    def test_urls_that_should_fails(self):
        tests = [
            "/api/structure/bad_db/entry/",
            ]
        for url in tests:
            self._check_HTTP_response_code(url, msg="The URL ["+url+"] should've failed.")


class StructureWithFilterEntryDatabaseRESTTest(InterproRESTTestCase):

    def test_urls_that_return_object_of_structure_and_entry_counts(self):
        acc = "IPR003165"
        urls = [
            "/api/structure/entry/interpro",
            "/api/structure/entry/pfam",
            "/api/structure/entry/unintegrated",
            "/api/structure/entry/unintegrated/pfam",
            "/api/structure/entry/unintegrated/smart",
            "/api/structure/entry/interpro/pfam",
            "/api/structure/entry/interpro/"+acc+"/pfam",
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIsInstance(response.data, dict, url+" should have returned a dict")
            for prot_db in response.data:
                self.assertEqual(prot_db, "pdb")
                self.assertIn("structures", response.data[prot_db])
                self.assertIn("entries", response.data[prot_db])

    def test_urls_that_return_list_of_structure_accessions_with_matches(self):
        acc = "IPR003165"
        urls = [
            "/api/structure/pdb/entry/interpro",
            "/api/structure/pdb/entry/pfam",
            "/api/structure/pdb/entry/unintegrated",
            "/api/structure/pdb/entry/unintegrated/pfam",
            "/api/structure/pdb/entry/interpro/pfam",
            "/api/structure/pdb/entry/interpro/"+acc+"/pfam",
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self._check_is_list_of_objects_with_accession(response.data["results"])
            self._check_is_list_of_objects_with_key(response.data["results"], "entries",
                                                    "It should have the key 'entries' for the URL ["+url+"]")
            for structure in response.data["results"]:
                for match in structure["entries"]:
                    self._check_entry_structure_details(match)

    def test_urls_that_return_a_structure_details_with_matches(self):
        pdb_1 = "1JM7"
        pdb_2 = "2BKM"
        acc = "IPR003165"
        urls = {
            "/api/structure/pdb/"+pdb_2+"/entry/unintegrated": ["PF17180"],
            "/api/structure/pdb/"+pdb_1+"/entry/unintegrated": ["PF17180", "PF17176"],
            "/api/structure/pdb/"+pdb_1+"/entry/interpro": ["IPR003165", "IPR001165"],
            "/api/structure/pdb/"+pdb_2+"/entry/pfam": ["PF17180"],
            "/api/structure/pdb/"+pdb_1+"/entry/interpro/pfam": ["PF02171"],
            "/api/structure/pdb/"+pdb_1+"/entry/interpro/smart": ["SM00950"],
            "/api/structure/pdb/"+pdb_1+"/entry/interpro/"+acc+"/smart": ["SM00950"],
            "/api/structure/pdb/"+pdb_1+"/entry/interpro/"+acc+"/pfam": ["PF02171"],
            "/api/structure/pdb/"+pdb_2+"/entry/unintegrated/pfam": ["PF17180"],
        }
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self._check_structure_details(response.data["metadata"])
            self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
            self.assertEqual(len(response.data["entries"]), len(urls[url]),
                             "The nember of entries dhould be the sem URL: [{}]".format(url))
            for entry in response.data["entries"]:
                self.assertIn(entry["entry"], urls[url])

    def test_urls_that_return_a_structure_details_with_matches_from_chain(self):
        pdb_1 = "1JM7"
        pdb_2 = "2BKM"
        acc = "IPR003165"
        urls = {
            "/api/structure/pdb/"+pdb_2+"/B/entry/unintegrated": ["PF17180"],
            "/api/structure/pdb/"+pdb_1+"/A/entry/unintegrated": ["PF17176"],
            "/api/structure/pdb/"+pdb_1+"/B/entry/unintegrated": ["PF17180"],
            "/api/structure/pdb/"+pdb_1+"/A/entry/interpro": ["IPR003165", "IPR001165"],
            "/api/structure/pdb/"+pdb_2+"/B/entry/pfam": ["PF17180"],
            "/api/structure/pdb/"+pdb_1+"/A/entry/interpro/pfam": ["PF02171"],
            "/api/structure/pdb/"+pdb_1+"/A/entry/interpro/smart": ["SM00950"],
            "/api/structure/pdb/"+pdb_1+"/A/entry/interpro/"+acc+"/smart": ["SM00950"],
            "/api/structure/pdb/"+pdb_1+"/A/entry/interpro/"+acc+"/pfam": ["PF02171"],
            "/api/structure/pdb/"+pdb_2+"/B/entry/unintegrated/pfam": ["PF17180"],
        }
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self._check_structure_details(response.data["metadata"])
            self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
            self.assertEqual(len(response.data["entries"]), len(urls[url]),
                             "The number of entries should be the same. URL: [{}]".format(url))
            for entry in response.data["entries"]:
                self.assertIn(entry["entry"], urls[url])

    def test_urls_that_should_return_empty_entries(self):
        pdb_1 = "1JM7"
        pdb_2 = "2BKM"
        acc = "IPR003165"
        tests = [
            "/api/structure/pdb/"+pdb_2+"/A/entry/unintegrated",
            "/api/structure/pdb/"+pdb_1+"/B/entry/interpro",
            "/api/structure/pdb/"+pdb_2+"/A/entry/pfam",
            "/api/structure/pdb/"+pdb_1+"/B/entry/interpro/pfam",
            "/api/structure/pdb/"+pdb_1+"/B/entry/interpro/smart",
            "/api/structure/pdb/"+pdb_1+"/B/entry/interpro/"+acc+"/smart",
            "/api/structure/pdb/"+pdb_1+"/B/entry/interpro/"+acc+"/pfam",
            "/api/structure/pdb/"+pdb_2+"/A/entry/unintegrated/pfam",
            "/api/structure/pdb/"+pdb_2+"/B/entry/unintegrated/smart",
            "/api/structure/pdb/entry/unintegrated/smart",
            ]
        for url in tests:
            self._check_HTTP_response_code(url, msg="The URL ["+url+"] should've failed.")

#
# class structureWithFilterEntryDatabaseAccessionRESTTest(InterproRESTTestCase):
#
#     def test_urls_that_return_object_of_structure_and_entry_counts(self):
#         acc = "IPR003165"
#         pfam = "PF02171"
#         pfam_u = "PF17180"
#         urls = [
#             "/api/structure/entry/unintegrated/pfam/"+pfam_u,
#             "/api/structure/entry/interpro/pfam/"+pfam,
#             "/api/structure/entry/pfam/"+pfam,
#             "/api/structure/entry/interpro/"+acc+"/pfam/"+pfam,
#             "/api/structure/entry/interpro/"+acc,
#             ]
#         for url in urls:
#             response = self.client.get(url)
#             self.assertEqual(response.status_code, status.HTTP_200_OK)
#             self.assertIsInstance(response.data, dict)
#             for prot_db in response.data:
#                 self.assertIn(prot_db, ["pdb", "pdb", "pdb"])
#                 self.assertIn("structures", response.data[prot_db])
#                 self.assertIn("entries", response.data[prot_db])
#
#     def test_can_get_entries_from_structure_id_interpro_ids(self):
#         acc = "A1CUJ5"
#         ips = ["IPR001165", "IPR003165"]
#         for ip in ips:
#             response = self.client.get("/api/structure/pdb/"+acc+"/entry/interpro/"+ip)
#             self._check_single_entry_response(response)
#
#     def test_urls_that_return_list_of_structure_accessions_with_matches_and_detailed_entries(self):
#         acc = "IPR003165"
#         pfam = "PF02171"
#         smart = "SM00950"
#         urls = [
#             "/api/structure/pdb/entry/interpro/"+acc,
#             "/api/structure/pdb/entry/interpro/"+acc,
#             "/api/structure/pdb/entry/interpro/"+acc,
#             "/api/structure/pdb/entry/pfam/"+pfam,
#             "/api/structure/pdb/entry/unintegrated/pfam/"+pfam,
#             "/api/structure/pdb/entry/unintegrated/smart/"+smart,
#             "/api/structure/pdb/entry/interpro/pfam/"+pfam,
#             "/api/structure/pdb/entry/interpro/"+acc+"/pfam/"+pfam,
#             ]
#         for url in urls:
#             response = self.client.get(url)
#             self.assertEqual(response.status_code, status.HTTP_200_OK)
#             self._check_is_list_of_objects_with_accession(response.data["results"])
#             self._check_is_list_of_objects_with_key(response.data["results"], "entries",
#                                                     "It should have the key 'entries' for the URL ["+url+"]")
#             for structure in response.data["results"]:
#                 for match in structure["entries"]:
#                     self._check_match(match)
#                     self._check_entry_details(match["entry"])
#
#     def test_urls_that_return_a_structure_details_with_matches(self):
#         sp_1 = "M5ADK6"
#         sp_2 = "A1CUJ5"
#         acc = "IPR003165"
#         pfam = "PF02171"
#         pfam_u = "PF17180"
#         smart = "SM00950"
#         urls = [
#             "/api/structure/pdb/"+sp_2+"/entry/interpro/"+acc,
#             "/api/structure/pdb/"+sp_2+"/entry/pfam/"+pfam,
#             "/api/structure/pdb/"+sp_2+"/entry/interpro/pfam/"+pfam,
#             "/api/structure/pdb/"+sp_2+"/entry/interpro/smart/"+smart,
#             "/api/structure/pdb/"+sp_2+"/entry/interpro/"+acc+"/smart/"+smart,
#             "/api/structure/pdb/"+sp_2+"/entry/interpro/"+acc+"/pfam/"+pfam,
#             "/api/structure/pdb/"+sp_1+"/entry/unintegrated/pfam/"+pfam_u,
#         ]
#         for url in urls:
#             response = self.client.get(url)
#             self._check_structure_details(response.data["metadata"])
#             self.assertIn("entries", response.data, "'entries' should be one of the keys in the response")
#             self.assertEqual(len(response.data["entries"]), 1,
#                              "The number of entries should be 1. URL: [{}]".format(url))
#             self._check_match(response.data["entries"][0])
#             self._check_entry_details(response.data["entries"][0]["entry"])
#
#     def test_can_get_entries_from_structure_id_pfam_id(self):
#         acc = "A1CUJ5"
#         pfam = "PF02171"
#         response = self.client.get("/api/structure/pdb/"+acc+"/entry/pfam/"+pfam)
#         self._check_single_entry_response(response)
#
#     def test_urls_that_should_fails(self):
#         tr_1 = "P16582"
#         sp_1 = "M5ADK6"
#         acc = "IPR003165"
#         pfam = "PF02171"
#         pfam_u = "PF17180"
#         tests = [
#             "/api/structure/pdb/"+tr_1+"/entry/unintegrated/pfam/"+pfam_u,
#             "/api/structure/pdb/"+tr_1+"/entry/unintegrated/pfam/"+pfam_u,
#             "/api/structure/pdb/"+sp_1+"/entry/unintegrated/pfam/"+pfam_u,
#             "/api/structure/pdb/"+sp_1+"/entry/interpro/"+acc,
#             "/api/structure/pdb/"+sp_1+"/entry/interpro/"+acc+"/pfam/"+pfam,
#             ]
#         for url in tests:
#             self._check_HTTP_response_code(url, msg="The URL ["+url+"] should've failed.")
