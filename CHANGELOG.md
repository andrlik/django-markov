# Changelog

## Unreleased

[Compare the full difference](https://github.com/andrlik/django-markov/compare/0.2.3...HEAD)

- Adds a new optional setting `MARKOV_STATE_SIZE` to override the default value used by `markovify`. Note that state sizes need to be consistent, so changing this setting means you should regenerate your text models with the new size.

## 0.2.3

[Compare the full difference](https://github.com/andrlik/django-markov/compare/0.2.2...0.2.3)

- Adds a cached property `is_compiled_model` to `MarkovTextModel`. This allows a user to check in advance if models are compiled without having to know the internals of `markovify`.

## 0.2.2

[Compare the full difference](https://github.com/andrlik/django-markov/compare/0.2.1...0.2.2)

- Bug fix: gracefully handle when `MARKOV_CORPUS_MAX_CHAR_LIMIT` is not set.

## 0.2.1

[Compare the full difference](https://github.com/andrlik/django-markov/compare/0.2.0...0.2.1)

- Adds a migration for data field in MarkovTextModel.

## 0.2.0

[Compare the full difference](https://github.com/andrlik/django-markov/compare/0.1.1...0.2.0)

- Improves sentence generation performance by loading the text model into a cached property.
    - Cached properties are cleared when calling `refresh_from_db`.
- Enables storing non-compiled models to the database for use in combining multiple models into a single chain.
    - Adds boolean settings parameter `MARKOV_STORE_COMPILED_MODELS` to set default behavior.
    - This can be overridden when calling `update_model_from_corpus` using the `store_compiled` kwarg.
    - Adds ability to auto-detect if a loaded model is compiled or not, and will automatically compile for sentence generation if needed.
- Adds support for the `tries` directive when calling `generate_sentence`.
- Adds support for combining multiple models into one via `MarkovTextModel.combine_models`

## 0.1.1

[Compare the full difference](https://github.com/andrlik/django-markov/compare/0.1.0...0.1.1)

- Remove extraneous dependencies that should only appear in dev-dependencies.

## 0.1.0

- Initial release
