#
# apps.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MarkovConfig(AppConfig):
    """
    App config for Django.
    """

    name = "django_markov"
    verbose_name = _("Django Markov")
