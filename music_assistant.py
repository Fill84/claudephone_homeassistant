"""Music Assistant handler - media player control via Home Assistant."""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MusicAssistantHandler:
    """Detect Music Assistant and control media players via HA REST API."""

    def __init__(self, ha_handler):
        self._ha = ha_handler
        self._ma_available: Optional[bool] = None
        self._cache_ts: float = 0.0

    # --- Detection ---

    def is_available(self) -> bool:
        """Check if Music Assistant integration is present in Home Assistant.

        Checks GET /api/services for the music_assistant domain.
        Result is cached for 5 minutes.
        """
        now = time.time()
        if self._ma_available is not None and (now - self._cache_ts) < 300:
            return self._ma_available

        try:
            services = self._ha.get_services()
            self._ma_available = any(
                s.get("domain") == "music_assistant" for s in services
            )
        except Exception as e:
            logger.warning("Music Assistant detection failed: %s", e)
            self._ma_available = False

        self._cache_ts = now
        return self._ma_available

    # --- Player State ---

    def get_players(self) -> List[Dict[str, Any]]:
        """Get all media_player entities with full state and attributes."""
        entities = self._ha._get_entities()
        return [
            e for e in entities
            if e.get("entity_id", "").startswith("media_player.")
        ]

    def get_active_player(self) -> Optional[Dict[str, Any]]:
        """Get the currently playing or paused media player.

        Priority: playing > paused. Returns None if no active player.
        """
        players = self.get_players()
        for state in ("playing", "paused"):
            for p in players:
                if p.get("state") == state:
                    return p
        return None

    def get_now_playing_info(self) -> Dict[str, Any]:
        """Get structured now-playing information for the active player."""
        player = self.get_active_player()
        if not player:
            return {"available": False}

        attrs = player.get("attributes", {})

        artwork = attrs.get("entity_picture", "")
        if artwork and not artwork.startswith("http"):
            artwork = f"{self._ha.base_url}{artwork}"

        return {
            "available": True,
            "state": player.get("state", "unknown"),
            "player_name": attrs.get("friendly_name", player.get("entity_id", "")),
            "entity_id": player.get("entity_id", ""),
            "title": attrs.get("media_title", ""),
            "artist": attrs.get("media_artist", ""),
            "album": attrs.get("media_album_name", ""),
            "duration": attrs.get("media_duration"),
            "position": attrs.get("media_position"),
            "artwork_url": artwork,
            "volume": attrs.get("volume_level"),
            "shuffle": attrs.get("shuffle", False),
            "repeat": attrs.get("repeat", "off"),
            "source": attrs.get("source", ""),
            "content_type": attrs.get("media_content_type", ""),
        }

    # --- Playback Controls ---

    def play(self, entity_id: str = None) -> bool:
        entity_id = entity_id or self._active_entity_id()
        if not entity_id:
            return False
        return self._ha._call_service("media_player", "media_play", entity_id)

    def pause(self, entity_id: str = None) -> bool:
        entity_id = entity_id or self._active_entity_id()
        if not entity_id:
            return False
        return self._ha._call_service("media_player", "media_pause", entity_id)

    def stop(self, entity_id: str = None) -> bool:
        entity_id = entity_id or self._active_entity_id()
        if not entity_id:
            return False
        return self._ha._call_service("media_player", "media_stop", entity_id)

    def next_track(self, entity_id: str = None) -> bool:
        entity_id = entity_id or self._active_entity_id()
        if not entity_id:
            return False
        return self._ha._call_service("media_player", "media_next_track", entity_id)

    def previous_track(self, entity_id: str = None) -> bool:
        entity_id = entity_id or self._active_entity_id()
        if not entity_id:
            return False
        return self._ha._call_service("media_player", "media_previous_track", entity_id)

    def set_volume(self, level: float, entity_id: str = None) -> bool:
        entity_id = entity_id or self._active_entity_id()
        if not entity_id:
            return False
        level = max(0.0, min(1.0, level))
        return self._ha._call_service(
            "media_player", "volume_set", entity_id,
            {"volume_level": level},
        )

    def volume_up(self, entity_id: str = None) -> bool:
        entity_id = entity_id or self._active_entity_id()
        if not entity_id:
            return False
        return self._ha._call_service("media_player", "volume_up", entity_id)

    def volume_down(self, entity_id: str = None) -> bool:
        entity_id = entity_id or self._active_entity_id()
        if not entity_id:
            return False
        return self._ha._call_service("media_player", "volume_down", entity_id)

    # --- Voice / LLM Handle ---

    def handle(self, text: str, language: str = "en") -> str:
        """Handle music-related voice commands. Returns TTS-ready string."""
        text_lower = text.lower()

        # Now-playing queries
        if self._is_now_playing_query(text_lower, language):
            return self._format_now_playing(language)

        # Playback controls (order matters: specific before generic)
        if any(k in text_lower for k in ["pause", "pauzeer", "pauze"]):
            ok = self.pause()
            return self._msg("Paused.", "Gepauzeerd.", language) if ok else self._no_player(language)

        if any(k in text_lower for k in ["stop"]):
            ok = self.stop()
            return self._msg("Stopped.", "Gestopt.", language) if ok else self._no_player(language)

        if any(k in text_lower for k in ["next", "volgende", "volgend"]):
            ok = self.next_track()
            return self._msg("Next track.", "Volgend nummer.", language) if ok else self._no_player(language)

        if any(k in text_lower for k in ["previous", "vorige", "vorig"]):
            ok = self.previous_track()
            return self._msg("Previous track.", "Vorig nummer.", language) if ok else self._no_player(language)

        if any(k in text_lower for k in ["louder", "harder", "volume up"]):
            ok = self.volume_up()
            return self._msg("Volume up.", "Volume omhoog.", language) if ok else self._no_player(language)

        if any(k in text_lower for k in ["quieter", "softer", "zachter", "volume down", "stiller"]):
            ok = self.volume_down()
            return self._msg("Volume down.", "Volume omlaag.", language) if ok else self._no_player(language)

        # Play / resume (last — "play" is generic)
        if any(k in text_lower for k in ["play", "speel", "hervat", "resume", "afspelen"]):
            ok = self.play()
            return self._msg("Playing.", "Afspelen.", language) if ok else self._no_player(language)

        # Fallback: show what's playing
        return self._format_now_playing(language)

    # --- Private helpers ---

    def _active_entity_id(self) -> Optional[str]:
        player = self.get_active_player()
        if player:
            return player.get("entity_id")
        players = self.get_players()
        return players[0].get("entity_id") if players else None

    def _is_now_playing_query(self, text: str, language: str) -> bool:
        markers_nl = [
            "wat speelt", "wat draait", "welk nummer", "welk liedje",
            "welke muziek", "wat luister", "wat is er aan",
            "wat wordt er", "huidig nummer", "huidige nummer",
            "nu speelt", "nu draait",
        ]
        markers_en = [
            "what's playing", "what is playing", "now playing",
            "current song", "current track", "what song",
            "what track", "what music", "what am i listening",
            "currently playing",
        ]
        markers = markers_nl if language == "nl" else markers_en
        return any(m in text for m in markers)

    def _format_now_playing(self, language: str) -> str:
        info = self.get_now_playing_info()
        if not info.get("available"):
            return self._msg(
                "No music is currently playing.",
                "Er speelt momenteel geen muziek.",
                language,
            )

        title = info.get("title", "")
        artist = info.get("artist", "")
        album = info.get("album", "")
        state = info.get("state", "")
        player_name = info.get("player_name", "")

        if language == "nl":
            parts = []
            if state == "paused":
                parts.append(f"Gepauzeerd op {player_name}")
            else:
                parts.append(f"Nu speelt op {player_name}")
            if title:
                parts.append(title)
            if artist:
                parts.append(f"van {artist}")
            if album:
                parts.append(f"van het album {album}")
            return ": ".join(parts[:2]) + (
                ". " + ". ".join(parts[2:]) if len(parts) > 2 else ""
            ) + "."
        else:
            parts = []
            if state == "paused":
                parts.append(f"Paused on {player_name}")
            else:
                parts.append(f"Now playing on {player_name}")
            if title:
                parts.append(title)
            if artist:
                parts.append(f"by {artist}")
            if album:
                parts.append(f"from the album {album}")
            return ": ".join(parts[:2]) + (
                ". " + ". ".join(parts[2:]) if len(parts) > 2 else ""
            ) + "."

    def _no_player(self, language: str) -> str:
        return self._msg(
            "No media player available.",
            "Geen mediaspeler beschikbaar.",
            language,
        )

    def _msg(self, en: str, nl: str, language: str) -> str:
        return nl if language == "nl" else en
