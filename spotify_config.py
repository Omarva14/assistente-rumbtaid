# spotify_config.py

import os

# --- AI-COMMENT: Inizio Sezione Credenziali Spotify ---
# Le seguenti variabili caricano le credenziali necessarie per l'autenticazione
# con l'API di Spotify. Questi valori devono essere presenti nel tuo file .env
# nella root del progetto.
#
# Per ottenere questi valori:
# 1. Vai sulla tua Spotify Developer Dashboard: https://developer.spotify.com/dashboard
# 2. Crea o seleziona la tua applicazione.
# 3. Troverai il 'Client ID' e potrai visualizzare il 'Client Secret'.
# 4. In 'Settings', assicurati di aver aggiunto il 'Redirect URI' (es. http://localhost:8888/callback)
#    e che corrisponda esattamente al valore nel tuo file .env.
# ---

# Carica il Client ID della tua applicazione Spotify dal file .env
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")

# Carica il Client Secret della tua applicazione Spotify dal file .env
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Carica il Redirect URI configurato nella tua dashboard Spotify dal file .env
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")


# --- AI-COMMENT: Inizio Sezione Autorizzazioni (Scope) ---
# La variabile 'SCOPE' definisce quali permessi l'applicazione richiederà
# all'utente al momento del login. Ogni permesso abilita l'accesso a
# funzionalità specifiche. Aggiungi o rimuovi scope in base alle necessità
# dei tuoi tool, ma fai attenzione a non rimuovere quelli essenziali per
# le funzioni attuali.
# Elenco completo degli scope: https://developer.spotify.com/documentation/web-api/concepts/scopes
# ---

SCOPE = (
    "user-modify-playback-state "   # Modificare la riproduzione (play, pausa, volume, etc.)
    "user-read-playback-state "     # Leggere lo stato della riproduzione
    "user-read-currently-playing "  # Leggere la traccia attualmente in riproduzione
    "streaming "                    # Controllare la riproduzione su client Spotify (richiesto per il Web Playback SDK)
    "user-read-private "            # Leggere informazioni private del profilo utente (es. paese)
    "playlist-read-private "        # Leggere le playlist private di un utente
    "playlist-read-collaborative"   # Leggere le playlist collaborative
)


# --- AI-COMMENT: Inizio Sezione Cache Token ---
# La variabile 'CACHE_PATH' definisce il nome del file in cui Spotipy
# salverà le informazioni del token di accesso e di refresh. Questo permette
# di non dover effettuare il login manuale ad ogni avvio dello script.
# Puoi cambiare il nome se preferisci, ma assicurati sia coerente nel progetto.
# ---

CACHE_PATH = ".spotipy_cache_loop"


# --- AI-COMMENT: Sezione Validazione Avvio ---
# Questa funzione verifica che tutte le credenziali essenziali siano state
# caricate correttamente. Se una variabile manca, logga un errore e
# restituisce False. Questo previene l'avvio di tentativi di autenticazione
# destinati a fallire.
# ---
def validate_credentials() -> bool:
    """
    Verifica che le credenziali SPOTIPY siano state caricate dall'ambiente.

    Returns:
        bool: True se tutte le credenziali sono presenti, altrimenti False.
    """
    if not all([SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI]):
        return False
    return True
