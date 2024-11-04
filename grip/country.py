import gettext
from typing import List
import pycountry
from pycountry.db import Country

def get_country(name: str) -> Country | None:
    country = pycountry.countries.lookup(name)
    if country is None:
        return None
    assert isinstance(country, Country)
    return country

def load_translation(language: str | None = None, languages: List[str] = []) -> gettext.GNUTranslations:
    assert language or languages

    if language:
        languages.append(language)

    translation = gettext.translation(
        'iso3166-1',
        pycountry.LOCALES_DIR,
        languages=languages,
    )
    return translation
