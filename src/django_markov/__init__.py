"""A reusable Django app for storing Markov text models and generating sentences."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MarkovConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_markov"
    verbose_name = _("Markov")
