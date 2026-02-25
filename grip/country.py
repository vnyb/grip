import gettext
from collections.abc import Sequence

import pycountry
from pycountry.db import Country


def get_country(name: str) -> Country | None:
    try:
        country = pycountry.countries.lookup(name)
    except LookupError:
        return None
    return country


def load_translation(
    *,
    language: str | None = None,
    languages: Sequence[str] | None = None,
) -> gettext.NullTranslations:
    _languages = list(languages) if languages else []

    if language:
        _languages.append(language)

    translation = gettext.translation(
        "iso3166-1",
        pycountry.LOCALES_DIR,
        languages=_languages,
        fallback=True,
    )
    translation.install()
    return translation
