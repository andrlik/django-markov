# Generated by Django 5.0.3 on 2024-03-21 19:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MarkovTextModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                ("data", models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="MarkovStats",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                (
                    "num_sentences",
                    models.PositiveIntegerField(
                        default=0, help_text="Number of sentences generated from model."
                    ),
                ),
                (
                    "num_short_sentences",
                    models.PositiveIntegerField(
                        default=0, help_text="Of the total, how many were short?"
                    ),
                ),
                (
                    "text_model",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stats",
                        to="django_markov.markovtextmodel",
                    ),
                ),
            ],
        ),
    ]
