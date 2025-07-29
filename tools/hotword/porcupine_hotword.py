import asyncio
import pvporcupine
import sounddevice as sd
import numpy as np
import logging

logger = logging.getLogger("HOTWORD")

class PorcupineHotwordDetector:
    def __init__(self, access_key, model_path, keyword_path, hotword_detected_event):
        self._porcupine = None
        self._stream = None
        self._hotword_detected_event = hotword_detected_event
        self.running = True

        try:
            # La versione stabile usa solo la access_key e il keyword_path,
            # lasciando che Porcupine scelga il modello corretto dal file .ppn
            self._porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[keyword_path]
            )
            self._stream = sd.RawInputStream(
                samplerate=self._porcupine.sample_rate,
                blocksize=self._porcupine.frame_length,
                dtype="int16",
                channels=1,
                callback=self._audio_callback
            )
            logger.info("✅ Porcupine inizializzato correttamente.")
        except Exception as e:
            logger.critical(f"❌ Errore durante l'inizializzazione di Porcupine: {e}")
            self._porcupine = None

    def _audio_callback(self, indata, frames, time, status):
        # Non processare l'audio se siamo in arresto o se la hotword è già stata rilevata
        if not self.running or self._hotword_detected_event.is_set():
            return

        pcm = np.frombuffer(indata, dtype=np.int16)
        result = self._porcupine.process(pcm)

        if result >= 0:
            logger.info("🗣️ Hotword rilevata!")
            self._hotword_detected_event.set()

    async def run(self):
        if not self._porcupine or not self._stream:
            logger.error("Porcupine non inizializzato, impossibile avviare.")
            return
            
        self._stream.start()
        logger.info("🎙️ Stream audio attivo per Porcupine.")
        while self.running:
            await asyncio.sleep(0.1)

    def stop(self):
        self.running = False
        if self._stream and self._stream.active:
            self._stream.stop()
            self._stream.close()
        if self._porcupine:
            self._porcupine.delete()
        logger.info("🛑 HotwordDetector arrestato.")
