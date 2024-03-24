#
# admin.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

"""Admin model registration for django_markov."""

from django.contrib import admin

from django_markov.models import MarkovTextModel


@admin.register(MarkovTextModel)
class MarkovTextModelAdmin(admin.ModelAdmin):
    """Model admin for MarkovTextModel."""

    pass
