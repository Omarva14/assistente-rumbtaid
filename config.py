# config.py

import os
import logging

# --- AI-COMMENT: Inizio Sezione Credenziali Servizi Esterni ---
# Questo modulo centralizza le configurazioni e le chiavi API per tutti i
# servizi non legati a Spotify, come ElevenLabs e OpenAI.
# Assicurati che le variabili corrispondenti siano presenti nel tuo file .env.
# ---

logger = logging.getLogger(__name__)

# --- Credenziali ElevenLabs ---
# La tua API Key per i servizi di ElevenLabs.
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
# L'ID del tuo Agente Conversazionale su ElevenLabs.
ELEVEN_AGENT_ID = os.getenv("ELEVEN_AGENT_ID")
# Nuovo timeout per la connessione WebSocket a ElevenLabs (in secondi).
# Aumentalo se la connessione fallisce per timeout.
ELEVEN_WEBSOCKET_TIMEOUT = 30 # AUMENTATO A 30 SECONDI PER MAGGIORE ROBUSTezza
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

# Impostazione per il rilevamento del silenzio nel ConversationalAgent.
# Questo valore (RMS) determina la soglia sotto la quale un chunk audio è considerato silenzioso.
# Un valore più basso rende il sistema meno sensibile al silenzio (potrebbe rilevare rumori di fondo).
# Un valore più alto rende il sistema più sensibile al silenzio (potrebbe tagliare l'inizio delle parole).
# Si consiglia di partire da 200 e aggiustare in base al proprio ambiente.
SILENCE_THRESHOLD = 200


# Costante per 20ms di silenzio PCM 16kHz, 1 canale, Base64 encoded, senza wrap.
# Generata con i comandi sox e base64.
B64_SILENCE_20MS = "AQAAAAAA//8AAAEAAAAAAAAAAAAAAAAA//8AAP///////wAAAQD//wAAAQAAAAAAAQD//wAA//8AAAAAAAAAAAEAAAD//wAAAAAAAAAAAAAAAAAAAAAAAP//AAAAAAAA/////wAAAAABAAAAAQAAAAEAAAD//wAAAAAAAP//AAAAAAAAAQAAAAEAAAAAAAEAAAAAAAAAAAAAAAAA////////AQD//wAA//8AAAAA//8AAAAAAAAAAAAAAAAAAP//AQAAAAAA/////wEAAAD//wAA//8AAAAAAAABAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAA//8AAAAA//8BAAAAAAABAAAAAAD//wAAAQAAAAAAAAAAAAAA//////////8AAAAAAAABAAAAAAAAAAAAAAAAAP//AAABAAAAAAAAAAAAAQAAAAAA//8AAAAAAAAAAAAAAAAAAAAAAAD//wAAAAD//wAAAQAAAAEA//8AAAAA//8AAAAAAAAAAAEAAAAAAP//AAD//wAAAAD//wAAAAAAAAAAAQAAAAAAAAAAAAAAAAABAAEAAAAAAAAAAQD//wEAAAAAAP//AQABAAAAAAAAAAAAAAAAAP//AAAAAAAAAAAAAAAA//8AAP//AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAABAAAAAAAAAAAAAAD//wAAAAD/////AAAAAAAAAAAAAAAAAAAAAAAA//8AAAAA//8AAAEAAAAAAP//AAABAAAAAAAAAAAAAAAAAP//AAAAAP////8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAABAA=="

# --- Credenziali OpenAI (per risposte dinamiche future) ---
# AI-COMMENT: Abbiamo aggiunto questa variabile in previsione della futura
# implementazione delle risposte dinamiche del "Capitano" tramite GPT-4.
# Puoi aggiungere la chiave al tuo file .env quando sarai pronto.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def validate_elevenlabs_credentials() -> bool:
    """
    Verifica che le credenziali essenziali di ElevenLabs siano state caricate.

    Returns:
        bool: True se le credenziali sono presenti, altrimenti False.
    """
    if not all([ELEVEN_API_KEY, ELEVEN_AGENT_ID]):
        logger.error("❌ Credenziali ElevenLabs (API_KEY, AGENT_ID) mancanti nel file .env.")
        return False
    logger.info("✅ Credenziali ElevenLabs verificate.")
    return True
