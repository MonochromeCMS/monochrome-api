from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from .media import media

mount = FastAPI(title="Monochrome media API")


@mount.get("/{file:path}")
async def get_media_file(file: str):
    """Get the media files from Deta Drive"""
    headers = {"Cache-Control": "max-age=1728000"}

    try:
        res = media.get(file)
    except FileNotFoundError:
        raise HTTPException(404, "Resource not found")
    return StreamingResponse(res.iter_chunks(1024), media_type="image/png", headers=headers)
