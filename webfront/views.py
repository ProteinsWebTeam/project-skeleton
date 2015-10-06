from django.shortcuts import render
from webfront.models import Clan, Pfama
from rest_framework import viewsets
from webfront.serializers import ClanSerializer, PfamaSerializer


def home_page(request):
    return render(request, 'home.html')


def clans_page(request):
    clans = Clan.objects.using('pfam_ro').all()
    return render(request, 'clans.html', {"clans":clans})


def clan_page(request, clan_id):
    clan = Clan.objects.using('pfam_ro').get(clan_id=clan_id)
    return render(request, 'clan.html', {"clan": clan})


class ClanViewSet(viewsets.ModelViewSet):
    queryset = Clan.objects.using('pfam_ro').all()
    serializer_class = ClanSerializer

class PFamAViewSet(viewsets.ModelViewSet):
    queryset = Pfama.objects.using('pfam_ro').all()
    serializer_class = PfamaSerializer
