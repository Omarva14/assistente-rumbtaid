# tools/spotify_tools/playlist_artist.py
import logging
from typing import Dict, Any

from .auth import get_spotify_client, get_spotify_device_id, get_user_country, _update_active_device

logger = logging.getLogger("spotify_tools.playlist_artist")

async def PlaySpotifyPlaylist(playlist_name: str) -> Dict[str, Any]:
    sp = get_spotify_client()
    device_id = get_spotify_device_id()
    user_country = get_user_country()

    if not sp or not _update_active_device():
        logger.warning("Spotify non pronto o nessun dispositivo attivo per riproduzione playlist.")
        return {"status": "error", "message": "Spotify non pronto o nessun dispositivo attivo."}
    try:
        logger.info(f"Eseguo ricerca Spotify per playlist: '{playlist_name}'")
        results = sp.search(q=playlist_name, type="playlist", limit=1, market=user_country)
        if not results or not results['playlists']['items']: 
            logger.warning(f"Playlist '{playlist_name}' non trovata.")
            return {"status": "error", "message": f"Playlist '{playlist_name}' non trovata."}
        
        playlist = results['playlists']['items'][0]
        sp.start_playback(device_id=device_id, context_uri=playlist['uri'])
        logger.info(f"Riproduzione playlist '{playlist['name']}' avviata.")
        return {"status": "success", "playlist_name": playlist['name']}
    except Exception as e: 
        logger.error(f"Errore durante la riproduzione della playlist: {e}")
        return {"status": "error", "message": str(e)}

async def PlaySpotifyArtist(artist_name: str) -> Dict[str, Any]:
    sp = get_spotify_client()
    device_id = get_spotify_device_id()
    user_country = get_user_country()

    if not sp or not _update_active_device():
        logger.warning("Spotify non pronto o nessun dispositivo attivo per riproduzione artista.")
        return {"status": "error", "message": "Spotify non pronto o nessun dispositivo attivo."}
    try:
        logger.info(f"Eseguo ricerca Spotify per artista: '{artist_name}'")
        results = sp.search(q=f"artist:\"{artist_name}\"", type="artist", limit=1, market=user_country)
        if not results or not results['artists']['items']: 
            logger.warning(f"Artista '{artist_name}' non trovato.")
            return {"status": "error", "message": f"Artista '{artist_name}' non trovato."}
        
        artist = results['artists']['items'][0]
        top_tracks = sp.artist_top_tracks(artist['id'], country=user_country)
        if not top_tracks or not top_tracks['tracks']: 
            logger.warning(f"Nessuna top track trovata per {artist['name']}.")
            return {"status": "error", "message": f"Nessuna top track per {artist['name']}."}
        
        track_uris = [track['uri'] for track in top_tracks['tracks'][:10]] # Limita a 10 top track
        sp.start_playback(device_id=device_id, uris=track_uris)
        logger.info(f"Riproduzione top tracks di '{artist['name']}' avviata.")
        return {"status": "success", "artist_name": artist['name']}
    except Exception as e: 
        logger.error(f"Errore durante la riproduzione dell'artista: {e}")
        return {"status": "error", "message": str(e)}

async def PlayGenre(genre_name: str) -> Dict[str, Any]:
    logger.info(f"Tentativo di riprodurre il genere: '{genre_name}'")
    return await PlaySpotifyPlaylist(playlist_name=f"{genre_name} playlist")

async def PlayMoodOrActivity(mood_or_activity_description: str) -> Dict[str, Any]:
    logger.info(f"Tentativo di riprodurre per mood/attività: '{mood_or_activity_description}'")
    return await PlaySpotifyPlaylist(playlist_name=f"{mood_or_activity_description} playlist")
