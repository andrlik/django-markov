# django-markov

django-markov is a reusable Django app that enables you to generate text models and store
them in the database. Those models can then be retrieved and used to generate markov sentences.

![PyPI - Version](https://img.shields.io/pypi/v/django-markov)
![PyPI - Versions from Framework Classifiers](https://img.shields.io/pypi/frameworkversions/django/:packageName)
[![Rye](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/rye/main/artwork/badge.json)](https://rye-up.com)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This project is extracted from [django-quotes](https://github.com/andrlik/django-quotes) which
uses some of this functionality. Once I realized I needed it for another project, but without
the quotes, I spent an afternoon splitting it out.

**NOT READY FOR USE YET**

## Installation

Using pip:

`python -m pip install django-markov`

Using uv:

`python -m uv pip install django-markov`

This will install the app and all its dependencies but you will still need to download a
trained language model.

`python -m spacy download en-core-web-trf`

Then add the application and its dependency to your Django settings file, and optionally configure the corpus
size limit.

```python
INSTALLED_APPS = [
    ...,
    "django_typer",
    "django_markov",
    ...,
]

# Limit the total size of the corpus. This will result in
# sentences that are less likely to be sensible, but will improve
# performance when loading the compiled model from the database.
MARKOV_CORPUS_MAX_CHAR_LIMIT = 0  # Use 0 for no limit, or specify a character limit.
```

Then run migrations as usual.

`python manage.py migrate`
