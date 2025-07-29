# jukebox.py (VERSIONE FINALE STABILE)
import asyncio
import logging
from typing import Optional
import spotipy

from tools.spotify_tools.auth import _update_active_device

logger = logging.getLogger("jukebox")

class Jukebox:
    def __init__(self, injection_queue: asyncio.Queue, spotify_polling_queue: asyncio.Queue, sp_client: spotipy.Spotify, spotify_playback_event: asyncio.Event):
        self.injection_queue = injection_queue
        self.spotify_polling_queue = spotify_polling_queue
        self.sp = sp_client
        self.current_playing_uri: Optional[str] = None
        self.stop_event = asyncio.Event()
        self.spotify_playback_event = spotify_playback_event

    async def monitor_playback(self):
        logger.info("🎶 Jukebox avviato e in attesa di un URI sulla coda...")
        while not self.stop_event.is_set():
            try:
                uri_to_monitor = await self.spotify_polling_queue.get()
                self.current_playing_uri = uri_to_monitor
                
                logger.info(f"▶️ Nuovo URI ricevuto: {uri_to_monitor}. Inizio monitoraggio.")
                
                song_ended_naturally = await self._monitor_specific_uri(uri_to_monitor)

                if song_ended_naturally:
                    logger.info(f"Brano {uri_to_monitor} terminato. Invio notifica.")
                    await self.injection_queue.put({
                        "type": "jukebox_notification",
                        "text": "La canzone che stavi ascoltando è finita."
                    })
                
                self.current_playing_uri = None
                logger.info("🎶 Monitoraggio traccia terminato. Jukebox torna in attesa di un nuovo URI.")

            except asyncio.CancelledError:
                logger.info("Task Jukebox cancellato.")
                break
            except Exception as e:
                logger.error(f"❌ Errore critico nel ciclo principale del Jukebox: {e}", exc_info=True)
                self.current_playing_uri = None
                await asyncio.sleep(5)

    async def _monitor_specific_uri(self, uri_to_monitor: str) -> bool:
        """Monitora un URI. Ritorna True se la canzone finisce naturalmente, False altrimenti."""
        while not self.stop_event.is_set() and self.current_playing_uri == uri_to_monitor:
            try:
                if not self.spotify_playback_event.is_set():
                    logger.warning("Evento di playback disattivato, il monitoraggio viene interrotto.")
                    return False

                if not _update_active_device():
                    await asyncio.sleep(5)
                    continue

                playback_info = self.sp.current_playback()
                
                if not playback_info or not playback_info.get('item') or playback_info['item']['uri'] != uri_to_monitor:
                    return True
                
                if not playback_info.get('is_playing'):
                    await asyncio.sleep(3)
                    continue
                
                track_item = playback_info['item']
                remaining_ms = track_item['duration_ms'] - playback_info['progress_ms']
                if remaining_ms < 4000:
                    return True
                
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Errore durante il monitoraggio dell'URI {uri_to_monitor}: {e}")
                await asyncio.sleep(10)
                return False
        return False

    def stop(self):
        self.stop_event.set()
        logger.info("Jukebox: segnale di stop ricevuto.")
