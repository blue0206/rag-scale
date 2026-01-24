from elevenlabs.client import AsyncElevenLabs
from fastapi import UploadFile
from uuid import uuid4
from ..db.s3 import s3_client
from ..core.config import env_config


elevenlabs_client = AsyncElevenLabs(api_key=env_config.ELEVENLABS_API_KEY)


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

    translation = await elevenlabs_client.speech_to_text.convert(
        cloud_storage_url=presigned_url,
        model_id="scribe_v2",
        tag_audio_events=False,
        language_code="en"
    )

    try:
        await s3_client.delete_file_async(
            bucket=BUCKET,
            key=KEY
        )
    except Exception as e:
        print(f"Error deleting file {file.filename}: {e}")

    return translation.text # type: ignore
