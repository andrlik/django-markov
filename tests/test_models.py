#
# test_models.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

import pytest

from django_markov.models import MarkovStats, MarkovTextModel, get_corpus_char_limit

pytestmark = pytest.mark.django_db(transaction=True)


def test_stats_model_created() -> None:
    num_stat_objects = MarkovStats.objects.count()
    text_model = MarkovTextModel.objects.create()
    updated_stat_objects = MarkovStats.objects.count()
    assert updated_stat_objects - num_stat_objects == 1
    text_model.refresh_from_db()
    assert text_model.stats
    assert MarkovTextModel.objects.count() == updated_stat_objects


@pytest.mark.parametrize(
    "override_value,expected_result",
    [
        (None, 0),
        (500, 500),
    ],
)
def test_get_char_limit(
    settings, override_value: int | None, expected_result: int
) -> None:
    settings.MARKOV_CORPUS_MAX_CHAR_LIMIT = override_value
    assert get_corpus_char_limit() == expected_result


@pytest.mark.parametrize(
    "settings_limit,char_limit,expect_error",
    [
        (500, None, True),
        (0, 500, True),
        (500, 6000, False),
        (0, None, False),
    ],
)
def test_update_corpus_excessive(
    transactional_db,
    settings,
    text_model,
    sample_corpus,
    settings_limit: int,
    char_limit: int | None,
    expect_error: bool,
) -> None:
    settings.MARKOV_CORPUS_MAX_CHAR_LIMIT = settings_limit
    if expect_error:
        with pytest.raises(ValueError):
            text_model.update_model_from_corpus(sample_corpus, char_limit)
    else:
        text_model.update_model_from_corpus(sample_corpus, char_limit)
        text_model.refresh_from_db()
        assert text_model.data


def test_update_corpus(transactional_db, text_model, sample_corpus) -> None:
    assert not text_model.data
    mod_time = text_model.modified
    text_model.update_model_from_corpus(sample_corpus)
    text_model.refresh_from_db()
    assert text_model.data
    assert text_model.modified > mod_time


@pytest.mark.parametrize("char_limit", [0, 5000, 280, 500])
def test_generate_sentence(transactional_db, compiled_model, char_limit: int) -> None:
    sentence = compiled_model.generate_sentence(char_limit)
    assert sentence
    if char_limit != 0:
        assert len(sentence) < char_limit


@pytest.mark.parametrize(
    "char_limit,short_add,total_add",
    [
        (0, 0, 1),
        (500, 1, 1),
        (1000, 1, 1),
    ],
)
def test_sentence_stats_update(
    transactional_db, compiled_model, char_limit: int, short_add: int, total_add: int
) -> None:
    stat_object: MarkovStats = compiled_model.stats
    num_sentences = stat_object.num_sentences
    num_short = stat_object.num_short_sentences
    sentence = compiled_model.generate_sentence(char_limit)
    assert sentence
    stat_object.refresh_from_db()
    assert stat_object.num_sentences - num_sentences == total_add
    assert stat_object.num_short_sentences - num_short == short_add


def test_non_sentence_does_not_update_stats(transactional_db, text_model) -> None:
    stat_object: MarkovStats = text_model.stats
    num_sentences = stat_object.num_sentences
    num_short = stat_object.num_short_sentences
    sentence = text_model.generate_sentence()
    assert not sentence
    stat_object.refresh_from_db()
    assert stat_object.num_sentences == num_sentences
    assert stat_object.num_short_sentences == num_short
