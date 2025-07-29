# main.py (VERSIONE CON MUSICA FISSA AL 60%)
import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from conversational import ConversationalAgent
from jukebox import Jukebox
from tools import spotify_tools
import spotify_config
from background_music_manager import BackgroundMusicManager # RE-INSERITO
import config

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s')

async def main():
    logger = logging.getLogger("MAIN")
    logger.info("🚀 Avvio dell'Assistente Capitano con musica di sottofondo fissa... 🚀")

    # Inizializzazione
    spotify_tools.initialize_spotify(client_id=spotify_config.SPOTIPY_CLIENT_ID, client_secret=spotify_config.SPOTIPY_CLIENT_SECRET, redirect_uri=spotify_config.SPOTIPY_REDIRECT_URI, scope=spotify_config.SCOPE, cache_path=spotify_config.CACHE_PATH)
    spotify_tools.initialize_openai_client(os.getenv("OPENAI_API_KEY"))
    sp_client_instance = spotify_tools.get_spotify_client()

    # Creiamo gli eventi necessari
    hotword_event = asyncio.Event()
    playback_event = asyncio.Event()
    injection_q = asyncio.Queue()
    polling_q = asyncio.Queue()

    # Attivazione immediata per partire subito
    hotword_event.set()

    # Creiamo gli oggetti principali, incluso il manager musicale
    agent = ConversationalAgent(injection_q, polling_q, hotword_event, playback_event)
    jukebox = Jukebox(injection_q, polling_q, sp_client_instance, playback_event)
    music_path = getattr(config, 'BACKGROUND_MUSIC_PATH', "/home/omar/TRACCIASOTTOFONDO.mp3")
    background_manager = BackgroundMusicManager(track_path=music_path, spotify_playback_event=playback_event, hotword_detected_event=hotword_event, user_can_speak_event=agent.user_can_speak)

    try:
        # Avviamo tutti i moduli in parallelo
        logger.info("Avvio dei moduli di conversazione, jukebox e musica di sottofondo...")
        main_tasks = asyncio.gather(
            agent.start(),
            jukebox.monitor_playback(),
            background_manager.start()
        )
        await main_tasks

    except KeyboardInterrupt:
        logger.info("🔌 Interruzione manuale ricevuta.")
    finally:
        # Assicuriamoci di fermare tutti i componenti
        agent.stop()
        jukebox.stop()
        background_manager.stop()
        logger.info("🛑 Tutti i moduli arrestati.")

if __name__ == "__main__":
    setup_logging()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
