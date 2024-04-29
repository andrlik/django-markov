# Generated by Django 5.0.3 on 2024-04-04 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_markov", "0004_remove_markovtextmodel_compiled"),
    ]

    operations = [
        migrations.AlterField(
            model_name="markovtextmodel",
            name="data",
            field=models.JSONField(
                blank=True, help_text="The text model as JSON.", null=True
            ),
        ),
    ]