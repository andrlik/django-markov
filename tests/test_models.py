#
# test_models.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

from typing import Any

import pytest
from faker import Faker

from django_markov.models import (
    MarkovCombineError,
    MarkovTextModel,
    _get_corpus_char_limit,
)
from django_markov.text_models import POSifiedText

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


def test_get_char_limit_missing_settings(settings):
    del settings.MARKOV_CORPUS_MAX_CHAR_LIMIT
    assert _get_corpus_char_limit() == 0  # Setting was not present


def test_text_models_return_none_on_empty_directive():
    model = MarkovTextModel.objects.create()
    assert not model._as_text_model()
    assert not model._compiled_model


def test_do_not_recompile_compiled_model(compiled_model):
    assert (
        compiled_model._as_text_model().to_json()
        == compiled_model._compiled_model.to_json()
    )


def test_compile_non_compiled_model(sample_corpus):
    model = MarkovTextModel.objects.create()
    model.update_model_from_corpus(
        [sample_corpus, "My name is Inigo Montoya."], store_compiled=False
    )
    assert model.data
    model.refresh_from_db()
    assert not model._as_text_model().chain.compiled
    assert model._compiled_model.chain.compiled


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
                [sample_corpus, "My name is Inigo Montoya."], char_limit=char_limit
            )
    else:
        await text_model.aupdate_model_from_corpus(
            [sample_corpus, "My name is Inigo Montoya."], char_limit=char_limit
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
    sentence = await compiled_model.agenerate_sentence(char_limit, tries=200)
    assert sentence
    if char_limit != 0:
        assert len(sentence) < char_limit


def test_markov_not_ready(text_model) -> None:
    assert not text_model.is_ready
    assert not text_model.generate_sentence(char_limit=0)


@pytest.mark.asyncio
async def test_combine_strict_fail_on_ready(text_model, compiled_model) -> None:
    with pytest.raises(MarkovCombineError):
        await MarkovTextModel.acombine_models(models=[text_model, compiled_model])


@pytest.mark.asyncio
async def test_combine_strict_fail_on_compiled(compiled_model, sample_corpus) -> None:
    new_model = await MarkovTextModel.objects.acreate()
    await new_model.aupdate_model_from_corpus(
        [sample_corpus, "My name is Inigo Montoya"], store_compiled=False
    )
    with pytest.raises(MarkovCombineError):
        await MarkovTextModel.acombine_models(models=[new_model, compiled_model])


@pytest.mark.asyncio
async def test_combine_permissive_fail_on_small_set(compiled_model, text_model) -> None:
    faker = Faker()
    corpus = faker.paragraph(nb_sentences=10)
    new_model = await MarkovTextModel.objects.acreate(
        data=POSifiedText(corpus).to_json()
    )
    with pytest.raises(MarkovCombineError):
        await MarkovTextModel.acombine_models(
            models=[text_model, compiled_model, new_model],
            mode="permissive",
            return_type="model_instance",
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode,return_type,weights,expected_error_type",
    [
        ("frieds", "text_model", [0.6, 1.4], ValueError),
        ("permissive", "text_model", [0.6, 1.4], ValueError),
        ("permissive", "goulash", None, ValueError),
        ("strict", "model_instance", [0.5, 0.4, 0.1], MarkovCombineError),
    ],
)
async def test_combine_invalid_parameter_combinations(
    compiled_model,
    sample_corpus,
    mode: str,
    return_type: str,
    weights: list[float] | None,
    expected_error_type: Exception,
) -> None:
    new_model = await MarkovTextModel.objects.acreate()
    await new_model.aupdate_model_from_corpus(
        [sample_corpus, "My name is Inigo Montoya"], store_compiled=False
    )
    await compiled_model.aupdate_model_from_corpus(
        [sample_corpus, "You killed my father.", "Prepare to die."],
        store_compiled=False,
    )
    with pytest.raises(expected_error_type):
        await MarkovTextModel.acombine_models(
            models=[new_model, compiled_model],
            mode=mode,
            return_type=return_type,
            weights=weights,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "num_clean,num_empty,num_compiled,mode,result_type,weights,expected_result_type",
    [
        (3, 0, 0, "strict", "model_instance", [1.0, 1.0, 1.0], MarkovTextModel),
        (3, 0, 0, "strict", "text_model", [1.0, 1.0, 1.0], POSifiedText),
        (3, 0, 0, "strict", "model_instance", None, MarkovTextModel),
        (3, 0, 0, "strict", "text_model", None, POSifiedText),
        (3, 2, 3, "permissive", "model_instance", None, MarkovTextModel),
        (3, 2, 4, "permissive", "text_model", None, POSifiedText),
    ],
)
async def test_acombine_successful(
    num_clean: int,
    num_empty: int,
    num_compiled: int,
    mode: str,
    result_type: str,
    weights: list[float] | None,
    expected_result_type: Any,
) -> None:
    # Generate models.
    faker = Faker()
    models_to_combine = []
    if num_empty:
        for _ in range(num_empty):
            models_to_combine.append(await MarkovTextModel.objects.acreate())
    if num_compiled:
        for _ in range(num_compiled):
            corpus = faker.paragraph(nb_sentences=10)
            pos_model = POSifiedText(corpus).compile(inplace=True)
            comp_model = await MarkovTextModel.objects.acreate(data=pos_model.to_json())
            models_to_combine.append(comp_model)
    for _ in range(num_clean):
        corpus = faker.paragraph(nb_sentences=10)
        clean_model = await MarkovTextModel.objects.acreate()
        await clean_model.aupdate_model_from_corpus([corpus], store_compiled=False)
        await clean_model.arefresh_from_db()
        models_to_combine.append(clean_model)
    result, total_combined = await MarkovTextModel.acombine_models(
        models=models_to_combine, mode=mode, return_type=result_type, weights=weights
    )
    assert isinstance(result, expected_result_type)
    assert total_combined == num_clean
