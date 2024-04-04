# Changelog

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
