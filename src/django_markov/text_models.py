#
# text_models.py
#
# Copyright (c) 2024 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

import markovify
import spacy

nlp = spacy.load("en_core_web_trf")


class POSifiedText(markovify.Text):
    """Uses spacy to parse the text into a model.

    For information on the inherited properties and functions,
    see the markovify documentation at
    [https://github.com/jsvine/markovify](https://github.com/jsvine/markovify)
    """

    def word_split(self, sentence):
        """Split the sentence into words and there respective role in the
        sentence."""
        return ["::".join((word.orth_, word.pos_)) for word in nlp(sentence)]

    def word_join(self, words):
        """Join words back into a sentence."""
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence
