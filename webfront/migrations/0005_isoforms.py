# Generated by Django 2.1.9 on 2019-06-11 11:19

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [("webfront", "0004_ida_in_protein")]

    operations = [
        migrations.CreateModel(
            name="Isoforms",
            fields=[
                (
                    "accession",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("protein_acc", models.CharField(max_length=20)),
                ("length", models.IntegerField()),
                ("sequence", models.TextField()),
                ("features", jsonfield.fields.JSONField(null=True)),
            ],
            options={"db_table": "webfront_varsplic"},
        )
    ]
