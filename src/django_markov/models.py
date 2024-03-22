#
# models.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

"""Models"""

from asgiref.sync import async_to_sync
from django import dispatch
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_markov.text_models import POSifiedText

sentence_generated = dispatch.Signal()


def get_corpus_char_limit() -> int:
    if not settings.MARKOV_CORPUS_MAX_CHAR_LIMIT or not isinstance(
        settings.MARKOV_CORPUS_MAX_CHAR_LIMIT, int
    ):
        return 0
    return settings.MARKOV_CORPUS_MAX_CHAR_LIMIT


class MarkovTextModel(models.Model):
    """Stores a compiled markov text model."""

    created = models.DateTimeField(
        auto_now_add=True, help_text=_("When the model was created.")
    )
    modified = models.DateTimeField(
        auto_now=True, help_text=_("Last modification of the record.")
    )
    data = models.JSONField(
        null=True, blank=True, help_text=_("The compiled text model as JSON.")
    )

    def __str__(self):  # no cov
        return f"MarkovModel {self.pk}"

    @property
    def is_ready(self) -> bool:
        if self.data:
            return True
        return False

    async def aupdate_model_from_corpus(
        self, corpus: str, char_limit: int | None = None
    ) -> None:
        """Takes the corpus and updates the model, saving it.
        The corpus must not exceed the char_limit.
        Args:
            corpus (str): The corpus as a string of text sentences.
            char_limit (int | None): The maximum number of characters
                to allow in the corpus.
        """
        if not char_limit:
            char_limit = get_corpus_char_limit()
        if char_limit != 0 and char_limit < len(corpus):
            msg = f"Supplied corpus is over the maximum character limit: {char_limit}"
            raise ValueError(msg)
        updated_model = POSifiedText(corpus)
        updated_model.compile(inplace=True)
        self.data = updated_model.to_json()
        await self.asave()

    def update_model_from_corpus(
        self, corpus: str, char_limit: int | None = None
    ) -> None:
        """Sync wrapper for the async version"""
        async_to_sync(self.aupdate_model_from_corpus)(  # no cov
            corpus=corpus, char_limit=char_limit
        )

    def generate_sentence(self, char_limit: int = 0) -> str | None:
        """Sync wrapper for agenerate_sentence."""
        return async_to_sync(self.agenerate_sentence)(char_limit)  # no cov

    async def agenerate_sentence(self, char_limit: int = 0) -> str | None:
        """Generates a random sentence within the character limit
        based on the model.
        Args:
            char_limit (int): Maximum characters to use. If zero, no limit.
        Returns:
            str: Random sentence
        """
        if not self.is_ready:
            return None
        text_model = POSifiedText.from_json(self.data)
        sentence: str | None
        if char_limit > 0:
            sentence = text_model.make_short_sentence(max_chars=char_limit)
        else:
            sentence = text_model.make_sentence()
        # Emit a signal that can be used by other apps for things such as statistics.
        # Right now, pyright doesn't recognize the asend method as valid member of
        # django.dispatch.Signal
        sentence_generated.asend(  # type: ignore
            sender=self.__class__,
            instance=self,
            char_limit=char_limit,
            sentence=sentence,
        )
        return sentence
