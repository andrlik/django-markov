"""Admin model registration for django_markov."""

from django.contrib import admin

from django_markov.models import MarkovTextModel


@admin.register(MarkovTextModel)
class MarkovTextModelAdmin(admin.ModelAdmin):
    pass
