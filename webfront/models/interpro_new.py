from django.db import models
from jsonfield import JSONField


class Entry(models.Model):
    entry_id = models.CharField(max_length=10, null=True)
    accession = models.CharField(primary_key=True, max_length=10)
    type = models.CharField(max_length=10)
    name = models.TextField()
    short_name = models.CharField(max_length=12)
    other_names = JSONField()
    source_database = models.CharField(max_length=20)
    member_databases = JSONField()
    integrated = models.ForeignKey("Entry", null=True, blank=True)
    go_terms = JSONField()
    description = JSONField()
    wikipedia = models.TextField(null=True)
    literature = JSONField()
    proteins = models.ManyToManyField('Protein', through='ProteinEntryFeature')


class Protein(models.Model):
    accession = models.CharField(max_length=20, primary_key=True)
    identifier = models.CharField(max_length=20, unique=True, null=False)
    organism = JSONField()
    name = models.CharField(max_length=20)
    short_name = models.CharField(max_length=20, null=True)
    other_names = JSONField()
    description = JSONField()
    sequence = models.TextField(null=False)
    length = models.IntegerField(null=False)
    proteome = models.CharField(max_length=20)
    gene = models.CharField(max_length=20, null=False)
    go_terms = JSONField()
    evidence_code = models.IntegerField()
    feature = JSONField() #signalpeptide, transmembrane, coiledCoil, lowComplexityDisorder, activeSites. PerResidue, diSulphideBridges
    # structure = JSONField()
    genomic_context = JSONField()
    source_database = models.CharField(max_length=20, default="uniprot")
    structures = models.ManyToManyField('Structure', through='ProteinStructureFeature')


class ProteinEntryFeature(models.Model):
    protein = models.ForeignKey("Protein", null=False)
    entry = models.ForeignKey("Entry", null=False)
    coordinates = JSONField()
    # match_start = models.IntegerField(null=True)
    # match_end = models.IntegerField(null=True)


class Structure(models.Model):
    accession = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=20)
    short_name = models.CharField(max_length=20, null=True)
    other_names = JSONField()
    experiment_type = models.CharField(max_length=30)
    release_date = models.DateField()
    authors = JSONField()
    chains = JSONField()
    source_database = models.CharField(max_length=20, default="pdb")
    proteins = models.ManyToManyField('Protein', through='ProteinStructureFeature')


class ProteinStructureFeature(models.Model):
    protein = models.ForeignKey("Protein", null=False)
    structure = models.ForeignKey("Structure", null=False)
    chain = models.CharField(max_length=1)
    length = models.IntegerField(null=True)
    organism = JSONField()
    coordinates = JSONField()
    # start_residue = models.IntegerField(null=True)
    # stop_residue = models.IntegerField(null=True)

