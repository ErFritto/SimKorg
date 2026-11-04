"""Server web e protocollo WebSocket della replica electribe."""
from __future__ import annotations

import asyncio
import queue
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from engine import Engine

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "samples"
SAMPLES.mkdir(exist_ok=True)
app = FastAPI(title="electribe sampler replica")
engine = Engine(SAMPLES)


@app.on_event("startup")
async def startup() -> None:
    engine.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    engine.close()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/samples")
def samples() -> list[str]:
    return sorted(p.name for p in SAMPLES.glob("*.wav") if p.is_file())


class Assignment(BaseModel):
    index: int
    filename: str


@app.post("/api/assign")
def assign(payload: Assignment) -> dict:
    try:
        engine.assign_sample(payload.index, payload.filename)
    except (ValueError, OSError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return engine.snapshot()


@app.post("/api/upload/{filename}")
async def upload(filename: str, request: Request, index: int) -> dict:
    if Path(filename).name != filename or not filename.lower().endswith(".wav"):
        raise HTTPException(400, "Nome file WAV non valido")
    if not 0 <= index < 16:
        raise HTTPException(400, "Indice pad fuori intervallo")
    path = SAMPLES / filename
    if path.exists():
        raise HTTPException(409, "Un WAV con questo nome esiste già")
    data = await request.body()
    if not data or len(data) > 20_000_000:
        raise HTTPException(400, "Il WAV deve essere non vuoto e inferiore a 20 MB")
    path.write_bytes(data)
    try:
        engine.assign_sample(index, filename)
    except (ValueError, OSError) as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(400, str(exc)) from exc
    return engine.snapshot()


@app.websocket("/ws")
async def websocket(ws: WebSocket) -> None:
    await ws.accept()
    await ws.send_json(engine.snapshot())

    async def updates() -> None:
        previous = -1
        while True:
            await asyncio.sleep(.04)
            state = engine.snapshot()
            if state["revision"] != previous:
                previous = state["revision"]
                await ws.send_json(state)

    task = asyncio.create_task(updates())
    try:
        while True:
            message = await ws.receive_json()
            try:
                engine.handle(message)
            except (ValueError, TypeError, KeyError) as exc:
                await ws.send_json({"type": "error", "message": str(exc)})
    except WebSocketDisconnect:
        pass
    finally:
        task.cancel()


@app.websocket("/audio")
async def audio_stream(ws: WebSocket) -> None:
    """Invia PCM stereo 16 bit/44,1 kHz; il browser lo riproduce soltanto."""
    await ws.accept()
    if engine.audio_error:
        await ws.send_json({"type": "audio_error", "message": engine.audio_error})
        await ws.close()
        return
    listener = engine.subscribe_audio()
    disconnect = asyncio.create_task(ws.receive())
    try:
        await ws.send_json({"type": "audio_format", "rate": 44100, "channels": 2, "format": "s16le"})
        while True:
            if disconnect.done():
                break
            try:
                block = await asyncio.to_thread(listener.get, True, .25)
            except queue.Empty:
                continue
            await ws.send_bytes(block)
    except WebSocketDisconnect:
        pass
    finally:
        disconnect.cancel()
        engine.unsubscribe_audio(listener)
