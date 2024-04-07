#
# models.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

"""Models"""

from typing import Any, ClassVar, Literal

import markovify
from asgiref.sync import async_to_sync
from django import dispatch
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from django_markov.text_models import POSifiedText


class MarkovCombineError(Exception):
    """Exception raised when attempt to combine incompatible model chains."""

    pass


sentence_generated = dispatch.Signal()


def _get_corpus_char_limit() -> int:
    """Get the corpus character limit from settings or return a default."""
    if not hasattr(settings, "MARKOV_CORPUS_MAX_CHAR_LIMIT") or not isinstance(
        settings.MARKOV_CORPUS_MAX_CHAR_LIMIT, int
    ):
        return 0
    return settings.MARKOV_CORPUS_MAX_CHAR_LIMIT


class MarkovTextModel(models.Model):
    """Stores a compiled markov text model.

    Attributes:
        created (datetime.datetime): Date and time when the model was created.
        modified (datetime.datetime): Date and time when the model was last modified.
        data (JSON): The text model as JSON.
    """

    cached_properties: ClassVar[list[str]] = ["_compiled_model"]

    created = models.DateTimeField(
        auto_now_add=True, help_text=_("When the model was created.")
    )
    modified = models.DateTimeField(
        auto_now=True, help_text=_("Last modification of the record.")
    )
    data = models.JSONField(
        null=True, blank=True, help_text=_("The text model as JSON.")
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

    @classmethod
    async def acombine_models(
        cls,
        models: list["MarkovTextModel"],
        *,
        return_type: Literal["model_instance", "text_model"] = "model_instance",
        mode: Literal["strict", "permissive"] = "strict",
        weights: list[float] | None = None,
    ) -> tuple["MarkovTextModel | POSifiedText", int]:
        """Combine multiple MarkovTextModels into a single model.

        Models cannot be combined if any of the following is true:
            - They are empty of data.
            - They are stored in compiled state.
            - The state size between models is not the same.
            - The underlying text models are not the same type (if you subclass).
            - You supply weights, but not the same number as the models to combine
                or if you use permissive mode.

        Args:
            models (list[MarkovTextModel]): A list of MarkovTextModel instances to
                combine.
            return_type (Literal["model_instance", "text_model"]): The desired result
                 type.
            mode (Literal["strict", "permissive"]): strict indicates that an exception
                should be raised if any of the candidate models are incompatible, or
                if those specific instances should simply be dropped from the operation.
            weights (list[float] | None): A list of floats representing the relative
                weights to put on each source. Optional, but can only be used with
                mode='strict'.

        Returns:
            Either a new MarkovTextModel instance
                persisted to the database or a POSifiedText object to manipulate at a
                low level, and the total number of models combined.
        """
        # First we check to ensure that the models are combinable.
        empty_models = []
        compiled_models = []
        workable_models = []
        if mode not in ["strict", "permissive"]:
            msg = f"Invalid mode: {mode}. Must be one of 'strict' or 'permissive'!"
            raise ValueError(msg)
        if weights is not None and mode != "strict":
            msg = "Weights can only be provided if mode is set to strict!"
            raise ValueError(msg)
        if return_type not in ["model_instance", "text_model"]:
            msg = (
                f"Invalid return_type of {return_type} requested. Must be one of "
                "'model_instance' or 'text_model'"
            )
            raise ValueError(msg)
        for model in models:
            if not model.is_ready:
                empty_models.append(model)
            else:
                tm = model._as_text_model()
                if tm and tm.chain.compiled:
                    compiled_models.append(model)
                else:
                    workable_models.append(model)
        if mode == "strict":
            if empty_models or compiled_models:
                msg = f"There are {len(compiled_models)} compiled models "
                f"and {len(empty_models)} empty models in set!"
                raise MarkovCombineError(msg)
        if len(workable_models) <= 1:
            msg = f"There is only {len(workable_models)}. Cannot combine!"
            raise MarkovCombineError(msg)
        models_combined = len(workable_models)
        try:
            combined_model = markovify.combine(
                models=[m._as_text_model() for m in workable_models], weights=weights
            )
        except ValueError as m_err:
            msg = f"Combining models caused the following error: {m_err}"
            raise MarkovCombineError(msg) from m_err
        if not isinstance(combined_model, POSifiedText):  # no cov
            msg = "Received invalid result from markovify. "
            f"Returned type is {type(combined_model)}"
            raise MarkovCombineError(msg)
        if return_type == "text_model":
            return combined_model, models_combined  # type: ignore
        new_model = await MarkovTextModel.objects.acreate(data=combined_model.to_json())
        return new_model, models_combined

    @classmethod
    def combine_models(
        cls,
        models: list["MarkovTextModel"],
        *,
        return_type: Literal["model_instance", "text_model"] = "model_instance",
        mode: Literal["strict", "permissive"] = "strict",
        weights: list[float] | None = None,
    ) -> tuple["MarkovTextModel | POSifiedText", int]:
        """
        Sync wrapper of acombine_models.
        """
        return async_to_sync(cls.acombine_models)(  # no cov
            models=models, return_type=return_type, mode=mode, weights=weights
        )
