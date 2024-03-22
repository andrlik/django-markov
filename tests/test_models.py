#
# test_models.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

import pytest

from django_markov.models import _get_corpus_char_limit

pytestmark = pytest.mark.django_db(transaction=True)


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
    assert _get_corpus_char_limit() == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "settings_limit,char_limit,expect_error",
    [
        (500, None, True),
        (0, 500, True),
        (500, 6000, False),
        (0, None, False),
    ],
)
async def test_update_corpus_excessive(
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
            await text_model.aupdate_model_from_corpus(
                [sample_corpus, "My name is Inigo Montoya."], char_limit
            )
    else:
        await text_model.aupdate_model_from_corpus(
            [sample_corpus, "My name is Inigo Montoya."], char_limit
        )
        await text_model.arefresh_from_db()
        assert text_model.data


@pytest.mark.asyncio
async def test_update_corpus(text_model, sample_corpus) -> None:
    assert not text_model.data
    mod_time = text_model.modified
    await text_model.aupdate_model_from_corpus(
        [sample_corpus, "My name is Inigo Montoya."]
    )
    await text_model.arefresh_from_db()
    assert text_model.data
    assert text_model.modified > mod_time


@pytest.mark.asyncio
@pytest.mark.parametrize("char_limit", [0, 5000, 280, 500])
async def test_generate_sentence(compiled_model, char_limit: int) -> None:
    sentence = await compiled_model.agenerate_sentence(char_limit)
    assert sentence
    if char_limit != 0:
        assert len(sentence) < char_limit


def test_markov_not_ready(text_model) -> None:
    assert not text_model.is_ready
    assert not text_model.generate_sentence(char_limit=0)
