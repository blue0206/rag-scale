import os
from ..core.config import env_config
from groq import Groq

groq_client = Groq(api_key=env_config["GROQ_API_KEY"])


def speech_to_text(filename: str):
    """
    This function receives a filename for an audio file of a user query and
    returns the translated text.
    """

    with open(filename, "rb") as f:
        translation = groq_client.audio.translations.create(
            file=f, model="whisper-large-v3"
        )

    try:
        os.remove(filename)
    except:
        pass

    return translation.text
