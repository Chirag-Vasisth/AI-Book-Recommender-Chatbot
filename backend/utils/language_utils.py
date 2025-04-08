from googletrans import Translator
from typing import Optional

translator = Translator()

def translate_text(text: str, src_lang: str = 'en', dest_lang: str = 'en') -> Optional[str]:
    """
    Translate text from source language to destination language.
    
    Args:
        text: The text to translate
        src_lang: Source language code (default 'en')
        dest_lang: Destination language code (default 'en')
    
    Returns:
        Translated text or None if translation fails
    """
    if src_lang == dest_lang:
        return text
    
    try:
        translation = translator.translate(text, src=src_lang, dest=dest_lang)
        return translation.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text