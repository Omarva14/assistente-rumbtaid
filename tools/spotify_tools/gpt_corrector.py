# tools/spotify_tools/gpt_corrector.py
# --- MODULO AGGIORNATO CON FIX PER OPENAI ---

import logging
import json
from typing import Optional, Dict, Any
from openai import OpenAI

from .auth import get_openai_client

logger = logging.getLogger("spotify_tools.gpt_corrector")

async def get_corrected_search_terms_from_gpt(transcribed_text: str) -> Optional[Dict[str, str]]:
    """
    Usa OpenAI GPT per correggere e estrarre i termini di ricerca (artista, traccia).
    """
    openai_client: Optional[OpenAI] = get_openai_client()

    if not openai_client:
        logger.warning("OpenAI client non inizializzato, saltando la correzione GPT.")
        # Se GPT non è disponibile, dividiamo rozzamente la stringa per avere un fallback
        parts = transcribed_text.split(" by ")
        if len(parts) == 2:
            return {"track_name": parts[0].strip(), "artist_name": parts[1].strip()}
        return {"artist_name": None, "track_name": transcribed_text}

    system_prompt = """Sei un assistente musicale esperto per Spotify. Il tuo obiettivo principale è interpretare le richieste degli utenti per canzoni o artisti ed estrarre il "track_name" e "artist_name" più accurati e CANONICI.

    **REGOLE CRUCIALI per l'estrazione:**
    1.  **PRIORITÀ ASSOLUTA:** Estrai sempre il nome della traccia e dell'artista che si riferiscono alla **VERSIONE ORIGINALE IN STUDIO e alla versione più POPOLARE/CANONICA** della canzone.
    2.  **ESCLUSIONE IMPLICITA:** **NON** includere nel `track_name` o `artist_name` estratto termini che indicano versioni alternative come: "cover", "live", "remix", "acustica", "karaoke", "tribute", "strumentale", "versione", "sinfonia", "orchestra", "edit", "album version", "single version", "remastered", "feat.", "ft.", "deluxe", "explicit", "clean", "radio edit", "extended mix", "remaster", "re-recorded", "version", "mix", "edit", "demo", "original mix", "club mix", "radio mix", "extended version", "acoustic version", "live version", "remix version", "instrumental version", "tribute version", "karaoke version", "symphony version", "orchestral version", "re-recorded version", "remastered version", "anniversary edition", "deluxe edition", "bonus track", "soundtrack version", "album version", "single version", "radio version", "clean version", "explicit version", "original version", "new version", "old version", "classic version", "unplugged", "unreleased", "demo version", "rough mix", "alternate version", "early version", "late version", "extended play", "ep", "lp", "single", "album", "compilation", "greatest hits", "best of", "collection", "anthology", "box set", "soundtrack", "original soundtrack", "motion picture soundtrack", "film version", "movie version", "tv version", "game version", "musical version", "play version", "broadway version", "cast recording", "original cast recording", "studio cast recording", "live cast recording", "concert version", "session", "session version", "radio session", "bbc session", "mtv unplugged", "unplugged version", "acoustic set", "live at", "live in", "live from", "live on", "live concert", "live performance", "live recording", "live album", "live ep", "live single", "live collection", "live compilation", "live greatest hits", "live best of", "live anthology", "live box set", "live soundtrack", "live original soundtrack", "live motion picture soundtrack", "live film version", "live movie version", "live tv version", "live game version", "live musical version", "live play version", "live broadway version", "live cast recording", "live original cast recording", "live studio cast recording", "live concert version", "live performance version", "live recording version", "live album version", "live ep version", "live single version", "live collection version", "live compilation version", "live greatest hits version", "live best of version", "live anthology version", "live box set version", "live soundtrack version", "live original soundtrack version", "live motion picture soundtrack version", "live film version version", "live movie version version", "live tv version version", "live game version version", "live musical version version", "live play version version", "live broadway version version", "live cast recording version", "live original cast recording version", "live studio cast recording version", "live concert version version", "live session version", "live radio session version", "live bbc session version", "live mtv unplugged version", "live unplugged version version", "live acoustic set version", "live at the version", "live in the version", "live from the version", "live on the version"
        **A MENO CHE L'UTENTE NON LI RICHIEDA ESPLICITAMENTE**. Se l'utente dice "Play Despacito live", allora includi "live" nel `track_name`.
    3.  **Output JSON:** Il tuo output deve essere **SOLO** un oggetto JSON con due chiavi: 'artist_name' e 'track_name'.
        -   `'artist_name'`: Il nome canonico dell'artista. Restituisci `null` se l'artista non è esplicitamente menzionato o chiaramente inferibile.
        -   `'track_name'`: Il nome canonico della canzone. Se nessuna canzone specifica è chiara, restituisci la parte più rilevante della trascrizione (es: "musica rilassante").

    **Esempi per chiarezza e qualità (segui questi esempi alla lettera):**
    User: "Riproduci qualcosa dei Queen"
    Output: {"artist_name": "Queen", "track_name": null}

    User: "Riproduci Bohemian Rhapsody"
    Output: {"artist_name": null, "track_name": "Bohemian Rhapsody"}

    User: "Riproduci Sweet Child o' Mine dei Guns N' Roses"
    Output: {"artist_name": "Guns N' Roses", "track_name": "Sweet Child o' Mine"}

    User: "Metti un po' di musica rilassante?"
    Output: {"artist_name": null, "track_name": "musica rilassante"}

    User: "Qual è quella canzone sul sottomarino giallo?"
    Output: {"artist_name": null, "track_name": "Yellow Submarine"}

    User: "Riproduci Despacito live"
    Output: {"artist_name": null, "track_name": "Despacito live"}

    User: "Riproduci Hallelujah di Jeff Buckley"
    Output: {"artist_name": "Jeff Buckley", "track_name": "Hallelujah"}

    User: "Riproduci la nuova canzone di Ed Sheeran"
    Output: {"artist_name": "Ed Sheeran", "track_name": "nuova canzone"}

    User: "Riproduci Another One Bites the Dust dei Queen"
    Output: {"artist_name": "Queen", "track_name": "Another One Bites the Dust"}

    User: "Riproduci 'Someone Like You' versione karaoke"
    Output: {"artist_name": null, "track_name": "Someone Like You versione karaoke"}

    User: "Metti 'Stairway to Heaven' live dai Led Zeppelin"
    Output: {"artist_name": "Led Zeppelin", "track_name": "Stairway to Heaven live"}
    """
    
    corrected_terms_raw = ""
    try:
        # --- CORREZIONE APPLICATA QUI ---
        # La chiamata non è più asincrona nella libreria openai v1.x+
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Trascrizione utente: '{transcribed_text}'"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        corrected_terms_raw = response.choices[0].message.content
        corrected_terms = json.loads(corrected_terms_raw)

        if "artist_name" not in corrected_terms or "track_name" not in corrected_terms:
            logger.warning(f"GPT ha restituito un formato JSON inatteso: {corrected_terms_raw}. Fallback all'originale.")
            return {"artist_name": None, "track_name": transcribed_text}

        logger.debug(f"GPT ha corretto i termini di ricerca: {corrected_terms}")
        return corrected_terms
    except json.JSONDecodeError as e:
        logger.error(f"Errore decodifica JSON da GPT: {e}. Risposta raw: {corrected_terms_raw}", exc_info=True)
        return {"artist_name": None, "track_name": transcribed_text}
    except Exception as e:
        logger.error(f"Errore chiamata a OpenAI per correzione termini: {e}", exc_info=True)
        return {"artist_name": None, "track_name": transcribed_text}
