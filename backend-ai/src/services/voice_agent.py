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
    except Exception as e:
        print(f"Error deleting file {filename}: {e}")

    return translation.text


def text_to_speech(transcript: str, user_id: str):
    """
    This function receives a transcript and a user_id. The transcript is
    converted to speech and saved as .wav audio file to disk.
    """

    response = groq_client.audio.speech.create(
        model="canopylabs/orpheus-v1-english",
        voice="troy",
        input=transcript,
    )

    filename = f"output_{user_id}.wav"
    response.write_to_file(filename)
