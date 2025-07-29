# tools/spotify_tools/auth.py
import logging
import asyncio
import os
from typing import Optional, Dict, Any

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI 

logger = logging.getLogger("spotify_tools.auth")

_sp: Optional[spotipy.Spotify] = None
_auth_manager: Optional[SpotifyOAuth] = None
_openai_client: Optional[OpenAI] = None
_spotify_device_id: Optional[str] = None
_spotify_device_name: str = "N/D"
_user_country_spotify: Optional[str] = None

def initialize_spotify(client_id, client_secret, redirect_uri, scope, cache_path) -> bool:
    global _sp, _auth_manager, _user_country_spotify
    logger.info("--- Inizializzazione modulo Spotify (Auth)... ---")

    if not all([client_id, client_secret, redirect_uri]):
        logger.error("❌ Credenziali Spotify (ID, Secret, URI) mancanti.")
        return False

    _auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=cache_path,
        open_browser=False
    )

    try:
        token_info = _auth_manager.get_cached_token()
        if token_info:
            if _auth_manager.is_token_expired(token_info):
                logger.info("Token scaduto, tento il refresh...")
                token_info = _auth_manager.refresh_access_token(token_info['refresh_token'])
            access_token = token_info['access_token']
        else:
            auth_url = _auth_manager.get_authorize_url()
            print(f"\n🔗 Visita questo URL per autorizzare Spotify:\n{auth_url}\n")
            auth_code_url = input("📥 Incolla qui l’URL reindirizzato: ")
            code = _auth_manager.parse_response_code(auth_code_url)
            token_info = _auth_manager.get_access_token(code, as_dict=True, check_cache=False)
            access_token = token_info.get('access_token')

        if not access_token:
            raise Exception("Impossibile ottenere un access token valido.")

        _sp = spotipy.Spotify(auth=access_token)
        user = _sp.current_user()
        logger.info(f"✅ Autenticazione Spotify RIUSCITA per {user['display_name']}!")

        me_info = _sp.me()
        _user_country_spotify = me_info.get('country')
        if _user_country_spotify:
            logger.info(f"Paese utente: {_user_country_spotify}")

        _update_active_device()
        logger.info("--- Inizializzazione Spotify (Auth) completata ---")
        return True

    except Exception as e:
        logger.error(f"❌ Errore critico autenticazione Spotify: {e}", exc_info=False)
        return False

def initialize_openai_client(api_key: Optional[str]):
    global _openai_client
    if api_key:
        _openai_client = OpenAI(api_key=api_key)
        logger.info("✅ Client OpenAI inizializzato.")
    else:
        logger.warning("Chiave API di OpenAI non fornita, il correttore GPT non sarà disponibile.")

def get_spotify_client() -> Optional[spotipy.Spotify]:
    return _sp

def get_openai_client() -> Optional[OpenAI]:
    return _openai_client

def get_spotify_device_id() -> Optional[str]:
    return _spotify_device_id

def get_user_country() -> Optional[str]:
    return _user_country_spotify

def _update_active_device() -> bool:
    global _sp, _spotify_device_id, _spotify_device_name
    if not _sp: 
        logger.warning("Spotify client non inizializzato per aggiornamento dispositivo.")
        return False
    try:
        devices_info = _sp.devices()
        if not devices_info or not devices_info.get('devices'):
            logger.warning("Nessun dispositivo Spotify trovato nell'account.")
            _spotify_device_id = None
            return False

        available_devices = devices_info['devices']
        active_device = next((d for d in available_devices if d.get('is_active')), None)
        if not active_device:
            for dtype in ["Computer", "Smartphone", "Speaker"]:
                active_device = next((d for d in available_devices if d.get('type') == dtype), None)
                if active_device: break
        
        if not active_device and available_devices:
            active_device = available_devices[0]
            
        if active_device and active_device.get('id'):
            _spotify_device_id = active_device['id']
            _spotify_device_name = active_device.get('name', 'N/D')
            logger.info(f"Dispositivo attivo aggiornato: {_spotify_device_name}")
            return True
        
        logger.warning("Nessun dispositivo Spotify attivo o utilizzabile trovato.")
        _spotify_device_id = None
        return False
    except Exception as e:
        logger.error(f"Errore aggiornamento dispositivi: {e}")
        _spotify_device_id = None
        return False
