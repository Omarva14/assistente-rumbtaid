# tools/spotify_tools/search.py
# --- VERSIONE FINALE E COMPLETA DI TUTTE LE FUNZIONI ---

import logging
import asyncio
from typing import Dict, Any, Optional, List

from .auth import get_spotify_client, get_user_country, _update_active_device, get_spotify_device_id
from .gpt_corrector import get_corrected_search_terms_from_gpt

logger = logging.getLogger("spotify_tools.search")

def _find_best_track_match(
    tracks: List[Dict[str, Any]],
    search_track: str,
    search_artist: Optional[str],
    original_artist_id: Optional[str]
) -> Optional[Dict[str, Any]]:
    best_track: Optional[Dict[str, Any]] = None
    best_score: int = -999
    undesired_keywords = [
        'cover', 'tribute', 'karaoke', 'remix', 're-recorded', 'live', 'acoustic', 
        'instrumental', 'edit', 'version', 'symphony', 'orchestra', 
        'made popular by', 'in the style of'
    ]
    undesired_artists = [
        'karaoke', 'tribute band', 'all stars', 'party tyme', 'ameritz', 
        'royal philharmonic orchestra', 'tolga kashif', 'studio group'
    ]
    
    logger.debug(f"Inizio analisi di {len(tracks)} tracce per '{search_track}' di '{search_artist or 'N/A'}'. ID artista rif: {original_artist_id or 'N/A'}")
    for track in tracks:
        current_score = 0
        track_name_lower = track['name'].lower()
        track_artists = track.get('artists', [])
        
        if original_artist_id:
            artist_ids_in_track = {artist['id'] for artist in track_artists}
            if original_artist_id in artist_ids_in_track:
                current_score += 500
            else:
                logger.debug(f"SCARTATA (ID Artista non corrispondente): '{track_name_lower}'.")
                continue
        
        current_score += track.get('popularity', 0)
        
        for keyword in undesired_keywords:
            if keyword in track_name_lower: current_score -= 250
        
        for artist in track_artists:
            for undesired in undesired_artists:
                if undesired in artist.get('name', '').lower(): current_score -= 300

        if search_track.lower() in track_name_lower: current_score += 50
        
        if track.get('album', {}).get('album_type') == 'album': current_score += 25
        elif track.get('album', {}).get('album_type') == 'compilation': current_score -= 25
            
        logger.debug(f"Valutazione finale per '{track_name_lower}': Score={current_score}")
        if current_score > best_score:
            best_score = current_score
            best_track = track
            
    if best_track:
        logger.info(f"✅ Miglior corrispondenza: '{best_track['name']}' di '{best_track['artists'][0]['name']}' (Score: {best_score})")
    return best_track

async def _perform_search(search_track: str, search_artist: Optional[str], sp) -> Optional[Dict[str, Any]]:
    query_parts = [f'track:"{search_track}"']
    if search_artist: query_parts.append(f'artist:"{search_artist}"')
    query = " ".join(query_parts)

    logger.info(f"Eseguo ricerca Spotify: '{query}'")
    results = sp.search(q=query, limit=20, type='track', market=get_user_country())
    tracks = results.get('tracks', {}).get('items', [])
    if not tracks: return None

    original_artist_id: Optional[str] = None
    if search_artist:
        artist_results = sp.search(q=f'artist:"{search_artist}"', type='artist', limit=1)
        if artist_results and artist_results.get('artists', {}).get('items', []):
            original_artist_id = artist_results['artists']['items'][0]['id']
    
    if search_artist and not original_artist_id:
        logger.error(f"Impossibile trovare un ID ufficiale per '{search_artist}'. Salto tentativo di ricerca.")
        return None

    return _find_best_track_match(tracks, search_track, search_artist, original_artist_id)

async def play_specific_spotify_track(
    track_name: str, 
    artist_name: Optional[str] = None, 
    spotify_polling_queue: Optional[asyncio.Queue] = None
) -> Dict[str, Any]:
    if not _update_active_device():
        return {"status": "error", "message": "Spotify non pronto o nessun dispositivo attivo."}

    sp = get_spotify_client()
    device_id = get_spotify_device_id()

    logger.info("--- FASE 1: TENTATIVO CON RICERCA DIRETTA ---")
    best_track = await _perform_search(track_name, artist_name, sp)

    if not best_track:
        logger.info("--- FASE 2: TENTATIVO CON RICERCA CORRETTA DA GPT ---")
        full_request = f"{track_name} {artist_name}" if artist_name else track_name
        try:
            corrected_terms = await get_corrected_search_terms_from_gpt(full_request)
            if corrected_terms and corrected_terms.get("track_name"):
                best_track = await _perform_search(corrected_terms["track_name"], corrected_terms.get("artist_name"), sp)
        except Exception as e:
            logger.error(f"Errore durante la chiamata al correttore GPT: {e}")

    if not best_track:
        return {"status": "error", "message": f"Non ho trovato una versione valida di '{track_name}'."}

    track_uri = best_track['uri']
    display_name = f"'{best_track['name']}' di '{best_track['artists'][0]['name']}'"
    
    try:
        logger.info(f"Invio comando di riproduzione per {display_name}...")
        sp.start_playback(device_id=device_id, uris=[track_uri])
        await asyncio.sleep(2)
        playback = sp.current_playback()
        if playback and playback.get('is_playing') and playback.get('item') and playback['item']['uri'] == track_uri:
            logger.info(f"✅ CONFERMATO: {display_name} è ora in riproduzione.")
            if spotify_polling_queue:
                await spotify_polling_queue.put(track_uri)
            return {"status": "success", "message": f"Riproduzione di {display_name} avviata e confermata."}
        else:
            logger.error(f"❌ FALLIMENTO CONFERMA: Spotify non sta riproducendo la traccia richiesta.")
            return {"status": "error", "message": f"Ho inviato il comando per '{track_name}', ma non ho ricevuto conferma."}
    except Exception as e:
        logger.error(f"Errore durante il comando di riproduzione o la verifica: {e}", exc_info=True)
        return {"status": "error", "message": "Si è verificato un errore tecnico durante l'invio del comando a Spotify."}


async def add_to_queue(track_name: str, artist_name: Optional[str] = None) -> Dict[str, Any]:
    sp = get_spotify_client()
    if not sp or not _update_active_device():
        return {"status": "error", "message": "Spotify non pronto o nessun dispositivo attivo."}
    
    query = f'track:"{track_name}"'
    if artist_name: query += f' artist:"{artist_name}"'

    logger.info(f"Eseguo ricerca Spotify per accodare: '{query}'")
    try:
        results = sp.search(q=query, limit=10, type='track', market=get_user_country())
        if not results or not results['tracks']['items']:
            return {"status": "error", "message": "Traccia da accodare non trovata."}
        
        track_to_queue = max(results['tracks']['items'], key=lambda x: x['popularity'])
        
        sp.add_to_queue(uri=track_to_queue['uri'], device_id=get_spotify_device_id())
        logger.info(f"Aggiunto '{track_to_queue['name']}' alla coda di Spotify.")
        return {"status": "success", "track_name": track_to_queue['name']}
    except Exception as e:
        logger.error(f"Errore durante l'accodamento: {e}")
        return {"status": "error", "message": str(e)}

async def GetCurrentSongInfo() -> Dict[str, Any]:
    sp = get_spotify_client()
    if not sp or not _update_active_device():
        return {"status": "error", "message": "Spotify non pronto o nessun dispositivo attivo."}
    try:
        playback = sp.current_playback()
        if playback and playback.get('is_playing') and playback.get('item'):
            track = playback['item']
            artist_names = ", ".join([a['name'] for a in track['artists']])
            logger.info(f"Brano corrente: '{track['name']}' di '{artist_names}'.")
            return {"status": "success", "is_playing": True, "track_name": track['name'], "artist_name": artist_names}
        else:
            return {"status": "success", "is_playing": False, "message": "Nessuna traccia in riproduzione."}
    except Exception as e:
        logger.error(f"Errore recupero info brano corrente: {e}")
        return {"status": "error", "message": str(e)}
