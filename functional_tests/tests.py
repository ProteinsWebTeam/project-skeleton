import time
from functional_tests.base import FunctionalTest
import json

class NewVisitorTest(FunctionalTest):
    fixtures = ['functional_tests/dummy_data.json']

    def test_can_navigate_clans(self):
        # check out its homepage
        self.browser.get(self.server_url)

        # the page title and header mention UniFam
        self.assertIn('UniFam', self.browser.title)

        header_text = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('UNIFAM', header_text)

        # The User navigates trough the website until it finds the clans page
        self.click_link_and_wait(self.browser.find_element_by_css_selector('a.entries_link'))
        self.click_link_and_wait(self.browser.find_element_by_css_selector('a.interpro_link'))
        self.click_link_and_wait(self.browser.find_element_by_css_selector('a.interpro_all_link'))
        self.click_link_and_wait(self.browser.find_element_by_css_selector('a.member_db_link.pfam'))
        self.click_link_and_wait(self.browser.find_element_by_css_selector('a.interpro_member_option_link.clans'))

        # The clans page opens and has a title
        self.assertIn('UniFam - Clans', self.browser.title)

        # The user will have a way to choose a clan from the  DB
        clan_li =self.browser.find_element_by_css_selector('li.clan')
        clan_header =clan_li.find_element_by_tag_name('a').text
        # The user chooses a clan
        self.click_link_and_wait(clan_li.find_element_by_tag_name("a"))

        # The user will go to the page of the clan
        self.assertIn('UniFam - Clan: ', self.browser.title)

        # The clan page displays the details of the clan

        # The clan page displays a list of the  families of the clan

        # the clan page also displays an SVG
        svg = self.browser.find_element_by_tag_name("svg")
        self.assertEqual("clanviewer",svg.get_attribute("class"))
        node = svg.find_element_by_css_selector(".node")
        self.assertIn("node_",node.get_attribute("id"))

    def test_uses_the_REST_for_clan(self):
        # Test that the server returns JSON
        self.browser.get(self.server_url+"/api/clans/?format=json")
        content = self.browser.find_element_by_tag_name('body').text

        jsonp = json.loads(content)

        self.assertEqual(jsonp["count"],2)
        self.assertEqual(len(jsonp["results"]), jsonp["count"])

        self.assertIn('"TEST_ACC"', content)
        self.assertIn('"TEST_ACC_2"', content)

        self.browser.get(self.server_url+"/api/pfama/?format=json")
        content = self.browser.find_element_by_tag_name('body').text

        jsonp = json.loads(content)

        self.assertEqual(jsonp["count"],2)
        self.assertEqual(len(jsonp["results"]),jsonp["count"])

        self.assertIn('"TEST_PFAM_ACC"', content)
        self.assertIn('"TEST_PFAM_ACC_2"', content)

        self.browser.get(self.server_url+"/api/clans/TEST_ACC/?format=json")
        content = self.browser.find_element_by_tag_name('body').text

        jsonp = json.loads(content)

        self.assertEqual(jsonp["clan_acc"], "TEST_ACC")
        self.assertEqual(sum([x["num_full"] for x in jsonp["members"]]), jsonp["total_occurrences"])


    def test_can_navigate_active_sites(self):
        test_family="TEST_PFAM_ACC"

        # check out its homepage
        self.browser.get(self.server_url+"/entry/interpro/all/pfam/"+test_family)

        # The page has a link for active sites and the user clicks on it
        self.click_link_and_wait(self.browser.find_element_by_css_selector('a.interpro_member_option_link.active_sites'))

        # The active sites page opens and has a title
        self.assertIn('Active Sites', self.browser.title)
        self.assertIn(test_family, self.browser.title)

        # The user will have to input  a protein family accession
        content =self.browser.find_element_by_css_selector('.active_sites').text

        self.assertIn("TEST_SEQ_ACC_1",content)
        self.assertIn("TEST_SEQ_ACC_2",content)
        self.assertNotIn("TEST_SEQ_ACC_3",content)