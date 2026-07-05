import os
import gettext

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locales')

def load_translations():
    # Ensure directories exist
    os.makedirs(os.path.join(LOCALES_DIR, 'en', 'LC_MESSAGES'), exist_ok=True)
    os.makedirs(os.path.join(LOCALES_DIR, 'ru', 'LC_MESSAGES'), exist_ok=True)
    
    translations = {}
    try:
        ru = gettext.translation('messages', localedir=LOCALES_DIR, languages=['ru'])
        translations['ru'] = ru.gettext
    except FileNotFoundError:
        translations['ru'] = gettext.NullTranslations().gettext

    try:
        en = gettext.translation('messages', localedir=LOCALES_DIR, languages=['en'])
        translations['en'] = en.gettext
    except FileNotFoundError:
        translations['en'] = gettext.NullTranslations().gettext
        
    return translations

translations = load_translations()

def _(text, lang='en'):
    # Default to english if language not found
    t = translations.get(lang, translations.get('en'))
    if t:
        return t(text)
    return text
