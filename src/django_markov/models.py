"""Models"""

from typing import Any

from asgiref.sync import async_to_sync
from django import dispatch
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.db.models import F
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

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    data = models.JSONField(null=True, blank=True)

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
        async_to_sync(self.aupdate_model_from_corpus)(
            corpus=corpus, char_limit=char_limit
        )

    def generate_sentence(self, char_limit: int = 0) -> str | None:
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
        sentence_generated.send(
            sender=self.__class__, instance=self, char_limit=char_limit
        )
        return sentence


class MarkovStats(models.Model):
    """Stores statistics on the related Markov model."""

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    text_model = models.OneToOneField(
        MarkovTextModel, related_name="stats", on_delete=models.CASCADE
    )
    num_sentences = models.PositiveIntegerField(
        default=0, help_text=_("Number of sentences generated from model.")
    )
    num_short_sentences = models.PositiveIntegerField(
        default=0, help_text=_("Of the total, how many were short?")
    )

    def __str__(self):  # no cov
        return f"Stats for {self.text_model}"


@dispatch.receiver(sentence_generated)
def update_sentence_stats(
    sender,  # noqa: ARG001
    instance,
    char_limit: int,
    *args: Any,  # noqa: ARG001
    **kwargs: Any,  # noqa: ARG001
) -> None:
    """Update the stats for the related instance."""
    stat_object = instance.stats
    stat_object.num_sentences = F("num_sentences") + 1
    if char_limit > 0:
        stat_object.num_short_sentences = F("num_short_sentences") + 1
    stat_object.save()


@dispatch.receiver(post_save, sender=MarkovTextModel)
def create_stats_object(
    sender,  # noqa: ARG001
    instance: MarkovTextModel,
    created: bool,  # noqa: FBT001
    *args: Any,  # noqa: ARG001
    **kwargs: Any,  # noqa: ARG001
) -> None:
    """Create the accompanying stats object for the new model."""
    if created:
        MarkovStats.objects.create(text_model=instance)
