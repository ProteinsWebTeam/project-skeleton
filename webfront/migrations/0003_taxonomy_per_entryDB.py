# Generated by Django 2.1.10 on 2019-10-16 10:58

from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [("webfront", "0002_taxonomy_per_entry")]

    operations = [
        migrations.CreateModel(
            name="TaxonomyPerEntryDB",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("entry_db", models.CharField(db_index=True, max_length=100)),
                ("counts", jsonfield.fields.JSONField(null=True)),
                (
                    "taxonomy",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="webfront.Taxonomy",
                    ),
                ),
            ],
        )
    ]
