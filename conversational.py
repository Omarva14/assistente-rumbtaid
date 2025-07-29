# conversational.py (VERSIONE DEFINITIVA E CORRETTA)
import asyncio
import websockets
import json
import base64
import logging
import sounddevice as sd
import numpy as np
import httpx
from typing import Any
import config
from tools import spotify_tools

logger = logging.getLogger("conversational")
B64_SILENCE_20MS = getattr(config, 'B64_SILENCE_20MS', "AQAAAA...")

class ConversationalAgent:
    def __init__(self, injection_queue: asyncio.Queue, spotify_polling_queue: asyncio.Queue,
                 hotword_detected_event: asyncio.Event, spotify_playback_event: asyncio.Event,
                 text_only_mode: bool = False):
        self.api_key = config.ELEVEN_API_KEY
        self.agent_id = config.ELEVEN_AGENT_ID
        self.stop_event = asyncio.Event()
        self.user_can_speak = asyncio.Event()
        self.restart_event = asyncio.Event() # Manteniamo questo per coerenza con le revisioni
        self.injection_queue = injection_queue
        self.spotify_polling_queue = spotify_polling_queue
        self.hotword_detected_event = hotword_detected_event
        self.spotify_playback_event = spotify_playback_event
        self.text_only_mode = text_only_mode
        self.request_lock = asyncio.Lock()

    async def speak(self, text: str):
        await self.injection_queue.put({"text": text})

    async def _get_signed_websocket_url(self) -> str:
        url = f"https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id={self.agent_id}"
        headers = {"xi-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()["signed_url"]

    async def _play_chunk(self, audio_chunk_bytes: bytes):
        loop = asyncio.get_running_loop()
        audio_data = np.frombuffer(audio_chunk_bytes, dtype=np.int16)
        if audio_data.size > 0:
            await loop.run_in_executor(None, sd.play, audio_data, 16000)
            await loop.run_in_executor(None, sd.wait)

    # Anche se non credi sia necessario, ripristino un anti-eco MINIMO (0.2s)
    # come best practice per la stabilità, per evitare che l'agente senta se stesso.
    async def _delayed_enable_mic(self, delay: float):
        await asyncio.sleep(delay)
        if not self.spotify_playback_event.is_set():
            self.user_can_speak.set()
            logger.info(">> Microfono riattivato.")

    async def _handle_agent_messages(self, websocket: websockets.WebSocketClientProtocol):
        async for message_str in websocket:
            if self.stop_event.is_set() or self.restart_event.is_set(): break
            data = json.loads(message_str)
            msg_type = data.get('type')

            if msg_type == 'conversation_initiation_metadata':
                self.user_can_speak.set()
            elif msg_type == 'user_transcript':
                logger.info(f"✅ Trascrizione Utente: '{data.get('user_transcription_event', {}).get('user_transcript', '')}'")
            elif msg_type == 'client_tool_call':
                self.user_can_speak.clear()
                asyncio.create_task(self.handle_tool_call(websocket, data.get('client_tool_call', {})))
            elif msg_type == 'agent_response':
                if text := data.get('agent_response_event', {}).get('agent_response', ''):
                    logger.info(f"📝 Testo Risposta Agente: '{text}'")
                if self.request_lock.locked(): self.request_lock.release()
                asyncio.create_task(self._delayed_enable_mic(0.2))
            elif msg_type == 'audio':
                self.user_can_speak.clear()
                if audio_chunk_b64 := data.get('audio_event', {}).get('audio_base_64'):
                    await self._play_chunk(base64.b64decode(audio_chunk_b64))

    async def handle_tool_call(self, websocket: websockets.WebSocketClientProtocol, tool_call: dict):
        tool_name, tool_params, tool_call_id = tool_call.get('tool_name'), tool_call.get('parameters', {}), tool_call.get('tool_call_id')
        logger.info(f"Esecuzione tool: '{tool_name}' con parametri: {tool_params}")
        try:
            tool_function = getattr(spotify_tools, tool_name)
            is_music_tool = "spotify" in tool_name.lower()
            if is_music_tool:
                self.spotify_playback_event.set()
                await websocket.send(json.dumps({"type": "client_tool_result", "tool_call_id": tool_call_id, "result": json.dumps({"status": "success"}), "is_error": False}))
                asyncio.create_task(tool_function(**tool_params, spotify_polling_queue=self.spotify_polling_queue))
            else:
                tool_result = await tool_function(**tool_params)
                await websocket.send(json.dumps({"type": "client_tool_result", "tool_call_id": tool_call_id, "result": json.dumps(tool_result), "is_error": tool_result.get("status") != "success"}))
        except Exception as e:
            logger.error(f"Errore gestione tool '{tool_name}': {e}", exc_info=True)
            await websocket.send(json.dumps({"type": "client_tool_result", "tool_call_id": tool_call_id, "result": json.dumps({"status": "error", "message": str(e)}), "is_error": True}))

    async def _listen_for_injections(self, websocket: websockets.WebSocketClientProtocol):
        while not self.stop_event.is_set() and not self.restart_event.is_set():
            injection_data = await self.injection_queue.get()
            if injection_data.get("type") == "jukebox_notification":
                logger.info("Jukebox ha notificato la fine del brano. Ripristino stato.")
                self.spotify_playback_event.clear()
                if self.request_lock.locked(): self.request_lock.release()
                asyncio.create_task(self._delayed_enable_mic(0.1))
                continue
            await self.request_lock.acquire()
            await websocket.send(json.dumps({"type": "user_message", "text": injection_data.get("text", "")}))

    async def _stream_user_audio(self, websocket: websockets.WebSocketClientProtocol):
        audio_queue = asyncio.Queue(maxsize=50)
        loop = asyncio.get_running_loop()

        # VERSIONE CORRETTA E THREAD-SAFE (dal tuo backup)
        def audio_callback(indata: np.ndarray, frames: int, time_info: Any, status: Any):
            if status:
                loop.call_soon_threadsafe(logger.warning, f"Errore callback audio: {status}")
            if self.user_can_speak.is_set():
                try:
                    loop.call_soon_threadsafe(audio_queue.put_nowait, indata.copy())
                except asyncio.QueueFull:
                    pass # Se la coda è piena, scarta il nuovo chunk per non bloccare l'audio

        logger.info(f"Avvio stream audio utente a 16000 Hz...")
        with sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=audio_callback, blocksize=int(16000 * 0.02)):
            while not self.stop_event.is_set() and not self.restart_event.is_set():
                if self.user_can_speak.is_set():
                    try:
                        chunk = await asyncio.wait_for(audio_queue.get(), timeout=0.5)
                        await websocket.send(json.dumps({"type": "user_audio_chunk", "user_audio_chunk": base64.b64encode(chunk.tobytes()).decode('utf-8')}))
                    except asyncio.TimeoutError:
                        continue
                else:
                    await asyncio.sleep(0.05)

    def stop(self):
        if not self.stop_event.is_set():
            self.stop_event.set()
            logger.info("Segnale di stop inviato al ConversationalAgent.")

    async def start(self):
        logger.info("🚀 Avvio del ConversationalAgent...")
        await self.hotword_detected_event.wait()
        logger.info("Hotword rilevata dall'agente. Avvio ciclo di conversazione.")

        is_first_run = True
        while not self.stop_event.is_set():
            self.restart_event.clear()
            if is_first_run:
                from intro_lines import get_random_intro
                await self.speak(get_random_intro())
                is_first_run = False
            try:
                ws_url = await self._get_signed_websocket_url()
                async with websockets.connect(ws_url, open_timeout=20, max_size=None) as websocket:
                    init_msg = {"type": "conversation_initiation_client_data", "conversation_config_override": {"tts": {"output_format": "pcm_16000"}}}
                    await websocket.send(json.dumps(init_msg))
                    tasks = [self._handle_agent_messages(websocket), self._listen_for_injections(websocket), self._stream_user_audio(websocket)]
                    await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(f"Errore nel ciclo principale: {e}", exc_info=True)
                await asyncio.sleep(5)

            if self.restart_event.is_set():
                logger.info("Riavvio della connessione richiesto...")
                continue
