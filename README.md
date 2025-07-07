# django-markov

django-markov is a reusable Django app that enables you to create Markov text models, and store
them in the database. Those models can then be used to generate Markov chain sentences.
It relies on the excellent [markovify](https://github.com/jsvine/markovify) by [Jeremy Singer-Vine](https://github.com/jsvine)
and [spacy](https://spacy.io).

[![PyPI - Version](https://img.shields.io/pypi/v/django-markov)](https://pypi.org/project/django-markov/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-markov)
![PyPI - Versions from Framework Classifiers](https://img.shields.io/pypi/frameworkversions/django/django-markov)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![security: bandit](https://img.shields.io/badge/security-bandit-brightgreen.svg)](https://github.com/PyCQA/bandit)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/andrlik/django-markov/ci.yml?branch=main)
[![Coverage Status](https://coveralls.io/repos/github/andrlik/django-markov/badge.svg?branch=main)](https://coveralls.io/github/andrlik/django-markov?branch=main)


This project is extracted from [django-quotes](https://github.com/andrlik/django-quotes). Once I realized I needed it for another project, but without
the quotes, I spent an afternoon splitting it out.

## Installation

Using pip:

```bash
python -m pip install django-markov
```

Using uv:

```bash
uv pip install django-markov
```

This will install the app and all its dependencies but you will still need to download a
trained language model. You should use `en_core_web_sm`.

```bash
python -m spacy download en_core_web_sm
```

Then add the application and its dependency to your Django settings file, and optionally configure the corpus
size limit.

```python
INSTALLED_APPS = [
    ...,
    "django_markov",
    ...,
]

# Limit the total size of the corpus. This will result in
# sentences that are less likely to be sensible, but will improve
# performance when loading the compiled model from the database.
# Use 0 for no limit, or specify a character limit.
MARKOV_CORPUS_MAX_CHAR_LIMIT = 0

# Compile text models by default when writing to database.
# Compiled models are significantly more performant when
# generating sentences, but they cannot be chained with other
# model without parsing the entire corpus again.
# What's best will depend on your use case. If you don't intend
# to combine multiple models, you'll want this set to True.
MARKOV_STORE_COMPILED_MODELS = True

# Specify a state size for generated models. State size is the
# number of words the probability of a next word depends on.
# The default for the markovify library is 2.
# NOTE: models with different state sizes cannot be combined
# with one another. If you change this setting after creating
# models, you should regenerate them with their original corpus.
MARKOV_STATE_SIZE = 2
```

Then run migrations as usual.

```bash
python manage.py migrate
```

## Usage

To use, create a model object, and supply it with a corpus of text. This library can be used
both in sync and async modes. It follows the Django convention that async methods have the "a"
prefix to their names, e.g. `MarkovTextModel.update_model_from_corpus` and
`MarkovTextModel.aupdate_model_from_corpus`.

The examples below use the async methods, which are recommended as compiling or
loading a large corpus can be a longer operation.

```python
from django_markov.models import MarkovTextModel


async def create_my_text_model() -> MarkovTextModel:
    # Create the model object in the database.
    text_model = await MarkovTextModel.objects.acreate()
    # Feed it a corpus of text to build the model.
    # More is better, and you'll get the best results if you ensure
    # the sentences in your inputs are well punctuated.
    await text_model.aupdate_model_from_corpus(
        corpus_entries=[
            "My name is Inigo Montoya",
            "You killed my father.",
            "Prepare to die.",
        ],
        char_limit=0,  # Unlimited
    )
    return text_model
```

You can also later add to that model with new entries, as long as you haven't stored it in a compiled state.

```python
from django_markov.models import MarkovTextModel

my_markov_model_instance = MarkovTextModel.objects.first()
my_markov_model_instance.add_new_corpus_data_to_model(
    corpus_entries=[
        "I like burgers and fries.",
        "I once ate a pickle larger than my hand.",
    ]
)
```

Once you have a model initialized, you can have it generate a sentence. For example,
say that you have a text model in your database already, and you want a sentence generated.

```python
from django_markov.models import MarkovTextModel


async def sentence(text_model: MarkovTextModel, char_limit: int) -> str | None:
    # If the model has no data it will return None instead of a str.
    return await text_model.agenerate_sentence(char_limit=char_limit)
```

Every time a sentence is generated the `sentence_generated` signal will be emitted. You
can use this for things like collecting stats, creating an ongoing log of output, etc. The
signal will have the kwargs of:

```python
from django_markov.models import MarkovTextModel, sentence_generated

text_model = MarkovTextModel.objects.create()

sentence_generated.send(
    sender=MarkovTextModel,
    instance=text_model,
    char_limit=500,
    sentence="Life is stranger than a monkey riding a unicycle.",
)
```

## Contributing

Pull requests and improvements are welcome! First, familiarize yourself with our
[Code of Conduct](https://andrlik.github.io/django-markov/code_of_conduct/). You will need to agree to abide by this to have your contribution
included.

To enable debug mode, add the following environment variable
using `.envrc` for direnv, a `.env` file or similar.

```bash
export DJANGO_DEBUG="True"
```

We use [just](https://github.com/casey/just) and [uv](https://github.com/astral-sh/uv) to manage our project.
If you don't already have `just` installed, follow the directions on their project page.

Then run our setup command.

```bash
just install
```

It will do the following for you:

- Check if you've set the above environment variable.
- Check if pre-commit is on your path.
- Check if uv is installed, and install it if it is not.
- Install the pre-commit hooks into your repo.
- Create your virtualenv with all requirements.
- Run migrations

Our Justfile can handle a lot of the admin tasks for you without having to worry about
whether you've activated your venv. To see all the commands you can run `just` on its own.

<!-- [[[cog
import subprocess
import cog

list = subprocess.run(["just"], stdout=subprocess.PIPE)
cog.out(
    f"```\n{list.stdout.decode('utf-8')}```"
)
]]] -->
```
Available recipes:
    [lifecycle]
    build *ARGS             # Build Python package
    clean                   # Removes build and testing artifacts
    docs *ARGS              # Access mike commands
    fresh                   # Recreate environment from scratch
    install                 # Setup the venv and install all dependencies.
    upgrade                 # Update project dependencies.

    [qa]
    check-types             # Check types
    fmt                     # Run just formatter and rye formatter.
    lint                    # Run ruff linting
    safety                  # Runs bandit safety checks.
    test *ARGS              # Run the test suite
    tox *ARGS               # Run tox for code style, type checking, and multi-python tests. Uses run-parallel.

    [run]
    browser                 # Open development server in a web browser
    manage *ARGS            # Access Django management commands.
    req path="admin/" *ARGS # Send a request to the development server to print to stdout. Uses curl if present, else httpie.
    serve *ARGS             # Run the development server

    [uv]
    uv-install              # Downloads and installs uv on your system.
    uv-uninstall            # Uninstall uv
    uv-update               # Update uv
```
<!-- [[[end]]] -->

For example, to access Django functions such as `makemigrations`, run:

```bash
just manage makemigrations django_markov
```

To run the test suite:

```bash
just test
```

Then make your changes and commit as usual. Any change made to the behavior or logic
should also include tests, and updated documentation. Pull requests must also pass all
the pre-commit checks in order to be merged.

Once you've finished making all your changes, open a pull request and I'll review it as
soon as I can.
