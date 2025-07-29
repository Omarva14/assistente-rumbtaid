# background_music_manager.py (VERSIONE CON VOLUME FISSO)
import asyncio
import logging
import subprocess
import psutil

logger = logging.getLogger("BackgroundMusicManager")

def find_ffplay_process():
    """Cerca un processo ffplay attivo."""
    for proc in psutil.process_iter(['pid', 'name']):
        if 'ffplay' in proc.info['name'].lower():
            return proc
    return None

class BackgroundMusicManager:
    # Impostiamo il volume di default a 60
    def __init__(self, track_path: str, spotify_playback_event: asyncio.Event, hotword_detected_event: asyncio.Event, user_can_speak_event: asyncio.Event, volume_percent: int = 60):
        self.track_path = track_path
        self.spotify_playback_event = spotify_playback_event
        self.hotword_detected_event = hotword_detected_event
        # L'evento user_can_speak viene ricevuto ma non più utilizzato in questa versione
        self.user_can_speak_event = user_can_speak_event
        
        # L'unico livello di volume che ci interessa
        self.normal_volume = volume_percent
        
        self.process = None
        self.logger = logger
        self.running = True

    async def _start_music_if_not_running(self):
        # NUOVA LOGICA SEMPLIFICATA: se ffplay non è attivo, lo avvia. Altrimenti non fa nulla.
        if not find_ffplay_process():
            try:
                self.logger.info(f"🎵 Avvio musica di sottofondo a volume fisso {self.normal_volume}%...")
                self.process = await asyncio.create_subprocess_exec(
                    "ffplay", "-nodisp", "-autoexit", "-loop", "0",
                    "-volume", str(self.normal_volume), self.track_path,
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
                self.logger.info(f"Processo 'ffplay' avviato con PID: {self.process.pid}")
            except Exception as e:
                self.logger.error(f"❌ Errore durante l'esecuzione di ffplay: {e}")
                self.process = None

    def _force_kill_ffplay(self, log=True):
        if log: self.logger.warning("Esecuzione di un comando di terminazione forzata tramite 'pkill'...")
        try:
            subprocess.run(["pkill", "-f", "ffplay"], capture_output=True, text=True, check=False)
            if log: self.logger.info("✅ Comando 'pkill' eseguito.")
            self.process = None
        except Exception as e:
            self.logger.error(f"Errore imprevisto durante l'esecuzione di pkill: {e}")

    def stop(self):
        self.running = False
        self._force_kill_ffplay()

    async def start(self):
        await self.hotword_detected_event.wait()
        self.logger.info("Hotword rilevata! Avvio ciclo di gestione musica di sottofondo.")

        while self.running:
            # Se Spotify sta suonando, la musica di sottofondo deve essere spenta
            if self.spotify_playback_event.is_set():
                if find_ffplay_process():
                    self.logger.info("🎵 Pausa musica di sottofondo per Spotify...")
                    self._force_kill_ffplay()
            # Altrimenti, assicurati che la musica sia in esecuzione
            else:
                await self._start_music_if_not_running()

            await asyncio.sleep(1)
