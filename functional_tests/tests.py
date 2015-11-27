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

        # The page has a link for clans and the user clicks on it
        self.click_link_and_wait(self.browser.find_element_by_css_selector('a.clans_link'))

        # The clans page opens and has a title
        self.assertIn('UniFam - Clans', self.browser.title)

        # The user will have a way to choose a clan from the  DB
        clan_li =self.browser.find_element_by_css_selector('li.clan')
        clan_header =clan_li.find_element_by_tag_name('a').text
        # The user chooses a clan
        self.click_link_and_wait(clan_li.find_element_by_tag_name("a"))

        # The user will go to the page of the clan
        self.assertIn('UniFam - Clan: '+clan_header, self.browser.title)

        # The clan page displays the details of the clan

        # The clan page displays a list of the  families of the clan

        # the clan page also displays a table of the relationships

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
        test_family="PF13812"

        # check out its homepage
        self.browser.get(self.server_url)

        # The page has a link for active sites and the user clicks on it
        self.click_link_and_wait(self.browser.find_element_by_css_selector('a.active_sites_link'))

        # The active sites page opens and has a title
        self.assertIn('UniFam - Active Sites', self.browser.title)

        # The user will have to input  a protein family accession
        input_acc =self.browser.find_element_by_css_selector('input.accession')
        input_acc.send_keys(test_family)
        # The user chooses a clan
        self.click_link_and_wait(self.browser.find_element_by_css_selector("button.search"))

        # The user will go to the page of the clan
        self.assertIn('UniFam - Active Sites: '+test_family, self.browser.title)

        # The page displays the proteins with the residues where there are active sites
