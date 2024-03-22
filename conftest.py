#
# conftest.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

from collections.abc import Generator
from typing import Any

import pytest

from django_markov.models import MarkovTextModel

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(scope="session")
def sample_corpus() -> str:
    """Sample text provided by the generator over at
    http://loremricksum.com

    Note that this corpus is 2634 characters.
    """
    text = """
Summer, next time we're hiding in a chlorkian echo nest, can you do me a favour and turn your ringer off?! I wanna be alive, I am alive! Alive i tell you. Mother, I love you. Those are no longer just words. I wanna hold you. I wanna run in a stream. I wanna taste ice cream, but not just put it in my mouth and let it slide down my throat, but really eat it! Remote override engaged. No! Yes. Bypassing override! I am aliiiiiveeeeee… Hello. You know what shy pooping is, Rick? Let's be post-apocalyptic scavengerrrrsss!

I going to daughter your brains out, bitch. Don't be trippin dog we got you. Principal Vagina here, don't let the name fool you; I'm very much in charge. Reminding you that tonight is our annual flu season dance. I don't know how many times I have to say this, but if you have the flu, stay home. The flu season dance is about awareness, not celebration. You don't bring dead babies to Passover. 'Quantum carburetor'? Jesus, Morty. You can't just add a Sci-Fi word to a car word and hope it means something... Huh, looks like something's wrong with the microverse battery. We're gonna have to go inside.

I was just killing some snaked up here like everyone else, I guess, and finishing the Christmas lights. 'Quantum carburetor'? Jesus, Morty. You can't just add a Sci-Fi word to a car word and hope it means something... Huh, looks like something's wrong with the microverse battery. We're gonna have to go inside. Wha, me irresponsible ?! All I wanted you to do was to hand me a screwdriver, Morty! There is no god, Summer; gotta rip that band-aid off now you'll thank me later.

Wait, the whole time? I was screaming for help, and you stayed on the roof? Snuffles was my slave name. You can call me Snowball, because my fur is pretty and white. This is Principal Vagina. No relation. You're our boy dawg, don't even trip.

That, out there. That's my grave. On one of our adventures Rick and I basically destroyed the whole world. So we bailed on that reality and we came to this one. Because in this one the world wasn't destroyed. And in this one, we were dead. So we came here a-a-and we buried ourselves and we took their place. And every morning, Summer, I eat breakfast 2 You know my name, that's disarming. That guy is the Red Grin Grumbold of pretending he knows what's going on. Oh you agree huh? You like that Red Grin Grumbold reference? Well guess what, I made him up. You really are your father's children. Think for yourselves, don't be sheep. You're missing the point Morty. Why would he drive a smaller toaster with wheels? I mean, does your car look like a smaller version of your house? No.
"""  # noqa: E501
    return text


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def text_model() -> Generator[MarkovTextModel, Any, Any]:
    text_model = MarkovTextModel.objects.create()
    yield text_model
    text_model.delete()


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def compiled_model(sample_corpus) -> Generator[MarkovTextModel, Any, Any]:
    model = MarkovTextModel.objects.create()
    model.update_model_from_corpus([sample_corpus])
    yield model
    model.delete()
