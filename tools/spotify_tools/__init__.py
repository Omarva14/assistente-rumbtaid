# tools/spotify_tools/__init__.py (VERSIONE CORRETTA)
import logging
from . import auth
from . import search
from . import playlist_artist
from . import gpt_corrector

# Riepiloga le funzioni importanti per un accesso più semplice
initialize_spotify = auth.initialize_spotify
initialize_openai_client = auth.initialize_openai_client
get_spotify_client = auth.get_spotify_client
get_spotify_device_id = auth.get_spotify_device_id

play_specific_spotify_track = search.play_specific_spotify_track
add_to_queue = search.add_to_queue
GetCurrentSongInfo = search.GetCurrentSongInfo

PlaySpotifyPlaylist = playlist_artist.PlaySpotifyPlaylist
PlaySpotifyArtist = playlist_artist.PlaySpotifyArtist
PlayGenre = playlist_artist.PlayGenre
PlayMoodOrActivity = playlist_artist.PlayMoodOrActivity

logger = logging.getLogger("tools.spotify_tools")
