#
# models.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

"""Models"""

from typing import Any, ClassVar

from asgiref.sync import async_to_sync
from django import dispatch
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from django_markov.text_models import POSifiedText

sentence_generated = dispatch.Signal()


def _get_corpus_char_limit() -> int:
    """Get the corpus character limit from settings or return a default."""
    if not settings.MARKOV_CORPUS_MAX_CHAR_LIMIT or not isinstance(
        settings.MARKOV_CORPUS_MAX_CHAR_LIMIT, int
    ):
        return 0
    return settings.MARKOV_CORPUS_MAX_CHAR_LIMIT


class MarkovTextModel(models.Model):
    """Stores a compiled markov text model.

    Attributes:
        created (datetime.datetime): Date and time when the model was created.
        modified (datetime.datetime): Date and time when the model was last modified.
        data (JSON): The compiled text model as JSON.
        compiled (bool): Whether the model is stored in its compiled state. Initially
            set to True for safe migrations.
    """

    cached_properties: ClassVar[list[str]] = ["_compiled_model"]

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

    def refresh_from_db(self, *args: Any, **kwargs: Any):
        """Remove the value of the cached properties before refreshing the data."""
        super().refresh_from_db(*args, **kwargs)
        for prop in self.cached_properties:
            try:
                del self.__dict__[prop]
            except KeyError:  # no cov
                pass

    @property
    def is_ready(self) -> bool:
        """Flag to indicate if the model is initialized and ready
        to generate sentences.
        """
        if self.data:
            return True
        return False

    def _as_text_model(self) -> POSifiedText | None:
        """Returns the data as a POSifiedText object. It does not attempt to coerce
        compilation.

        Returns:
            POSifiedText | None: The loaded text model, or None if there is no
                model data in the instance.
        """
        if not self.is_ready:
            return None
        text_model = POSifiedText.from_json(self.data)
        return text_model

    @cached_property
    def _compiled_model(self) -> POSifiedText | None:
        """
        The text model loaded into a POSifiedText object and compiled. You shouldn't
        ever access this property directly. It's used to optimize performance when you
        generate multiple sentences over the course of the model.

        Returns:
            POSifiedText | None: The compiled model loaded from `self.data`, or None if
                `self.data` is None
        """
        if not self.is_ready:
            return None
        text_model = self._as_text_model()
        if not text_model:
            return None
        if text_model.chain.compiled:
            return text_model
        return text_model.compile(inplace=True)  # type: ignore

    async def aupdate_model_from_corpus(
        self,
        corpus_entries: list[str],
        *,
        char_limit: int | None = None,
        store_compiled: bool | None = None,
    ) -> None:
        """Takes the corpus and updates the model, saving it.
        The corpus must not exceed the char_limit.

        Args:
            corpus_entries (list[str]): The corpus as a list of text sentences.
            char_limit (int | None): The maximum number of characters
                to allow in the corpus.
            store_compiled (bool | None): Whether to store the model in it's compiled
                state. If None, defaults to settings.MARKOV_STORE_COMPILED_MODELS or
                False.
        """
        if not char_limit:
            char_limit = _get_corpus_char_limit()
        if (
            store_compiled is None
            and hasattr(settings, "MARKOV_STORE_COMPILED_MODELS")
            and isinstance(settings.MARKOV_STORE_COMPILED_MODELS, bool)
        ):
            store_compiled = settings.MARKOV_STORE_COMPILED_MODELS
        else:
            store_compiled = False
        corpus = " ".join(corpus_entries)
        if char_limit != 0 and char_limit < len(corpus):
            msg = f"Supplied corpus is over the maximum character limit: {char_limit}"
            raise ValueError(msg)
        updated_model = POSifiedText(corpus)
        if store_compiled:
            updated_model.compile(inplace=True)
            self.compiled = True
        else:
            self.compiled = False
        self.data = updated_model.to_json()
        await self.asave()

    def update_model_from_corpus(
        self,
        corpus_entries: list[str],
        *,
        char_limit: int | None = None,
        store_compiled: bool | None = None,
    ) -> None:
        """Sync wrapper for the async version"""
        async_to_sync(self.aupdate_model_from_corpus)(  # no cov
            corpus_entries=corpus_entries,
            char_limit=char_limit,
            store_compiled=store_compiled,
        )

    def generate_sentence(self, char_limit: int = 0, tries: int = 0) -> str | None:
        """Sync wrapper for agenerate_sentence."""
        return async_to_sync(self.agenerate_sentence)(
            char_limit=char_limit, tries=tries
        )  # no cov

    async def agenerate_sentence(
        self, char_limit: int = 0, tries: int = 10
    ) -> str | None:
        """Generates a random sentence within the character limit
        based on the model.

        Args:
            char_limit (int): Maximum characters to use. If zero, no limit.
            tries (int): Number of attempts to make a sentence.
        Returns:
            str: Random sentence
        """
        if not self.is_ready or not self._compiled_model:
            return None
        sentence: str | None
        if char_limit > 0:
            sentence = self._compiled_model.make_short_sentence(
                max_chars=char_limit, tries=tries
            )
        else:
            sentence = self._compiled_model.make_sentence(tries=tries)
        # Emit a signal that can be used by other apps for things such as statistics.
        # Right now, pyright doesn't recognize the asend method as valid member of
        # django.dispatch.Signal
        if sentence is not None:
            await sentence_generated.asend(  # type: ignore
                sender=self.__class__,
                instance=self,
                char_limit=char_limit,
                sentence=sentence,
            )
        return sentence
