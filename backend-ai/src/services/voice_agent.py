import time
import os
from fastapi import BackgroundTasks, UploadFile
from uuid import uuid4
from groq import AsyncGroq
from ..db.s3 import s3_client
from ..core.config import env_config


groq_client = AsyncGroq(api_key=env_config.GROQ_API_KEY)


async def speech_to_text(file: UploadFile):
    """
    This function receives an audio file of a user query. The file
    is uploaded to S3, its presigned url is generated and sent to STT api.
    """

    file_content = await file.read()
    BUCKET = "ragscale-audio"
    KEY = f"input_audio/{str(uuid4())}_{file.filename}"

    await s3_client.upload_file_async(
        bucket=BUCKET,
        key=KEY,
        file=file_content
    )

    presigned_url = await s3_client.create_presigned_url(
        bucket=BUCKET,
        key=KEY,
    )

    translation = await groq_client.audio.translations.create(
        url=presigned_url, 
        model="whisper-large-v3"
    )

    try:
        await s3_client.delete_file_async(
            bucket=BUCKET,
            key=KEY
        )
    except Exception as e:
        print(f"Error deleting file {file.filename}: {e}")

    return translation.text



async def text_to_speech(transcript: str, user_id: str, background_tasks: BackgroundTasks) -> str:
    """
    This function receives a transcript and a user_id. The transcript is
    converted to speech and saved as .wav audio file to disk.
    """

    response = await groq_client.audio.speech.create(
        model="canopylabs/orpheus-v1-english",
        voice="autumn",
        input=transcript,
        response_format="wav"
    )

    output_filename = f"{user_id}_{str(uuid4())}.wav"
    output_path = os.path.join("generated_audio", output_filename)
    
    await response.write_to_file(output_path)

    # Add a background task to remove the served static file after a delay to
    # ensure the output audio is deleted after the client has finished playing the same.
    background_tasks.add_task(file_cleanup, output_path)

    return output_filename


def file_cleanup(output_path: str) -> None:
    """
    This function cleans up the files in a given output path
    after a delay of 300s.
    """

    try:
        time.sleep(300)
        os.remove(output_path)
        print(f"Cleaned up audio file: {output_path}")
    except Exception as e:
        print(f"Error cleaning up file {output_path}: {e}")
