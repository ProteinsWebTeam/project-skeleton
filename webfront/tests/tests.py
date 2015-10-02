from django.core.urlresolvers import resolve
from django.test import TransactionTestCase
from django.http import HttpRequest
from django.template.loader import render_to_string
from webfront.models import Clan
from django.utils import timezone
from webfront.views import home_page


class ImportedModelTest(TransactionTestCase):

    def test_root_url_resolves_to_home_page_view(self):
        found = resolve('/')
        self.assertEqual(found.func, home_page)

    def test_saving_clan_in_test_server(self):
        cl = Clan.objects.using('pfam_ro').create(clan_acc="TEST_ACC",clan_id="TEST_ID",updated=timezone.now())
        all_clans = Clan.objects.using('pfam_ro').all()
        self.assertEqual(all_clans.count(), 1)
        self.assertEqual(all_clans[0], cl)


    def test_home_page_returns_correct_html(self):
        request = HttpRequest()  #1
        Clan.objects.using('pfam_ro').create(clan_acc="CL0587",clan_id="CL0587",updated=timezone.now())
        response = home_page(request)  #2
        expected_html = render_to_string('home.html', {"clan": {"clan_acc": "CL0587"}})
        self.assertEqual(response.content.decode(), expected_html)