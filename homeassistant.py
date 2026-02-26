"""Home Assistant plugin - smart home device control via REST API."""

import string
from pathlib import Path
from typing import Any, Dict, List

from ..base import ConfigField, DashboardPage, DashboardWidget, PluginBase, PluginMeta

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class HomeAssistantPlugin(PluginBase):
    """Home Assistant integration as a plugin."""

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="homeassistant",
            display_name="Home Assistant",
            description="Control smart home devices via Home Assistant REST API",
            version="2.0.2",
            author="Phillippe Pelzer",
        )

    @property
    def keywords(self) -> Dict[str, List[str]]:
        nl = [
            "lamp", "lampen", "licht", "lichten", "verlichting",
            "schakelaar", "schakel", "zet aan", "zet uit",
            "doe aan", "doe uit", "aan doen", "uit doen",
            "temperatuur", "thermostaat", "graden",
            "helderheid", "dimmen", "dim",
            "kleur", "blauw", "rood", "groen", "oranje", "geel",
            "paars", "roze", "wit", "warm", "koel",
            "gordijn", "gordijnen", "rolluik",
        ]
        en = [
            "light", "lights", "lamp", "lamps", "lighting",
            "switch", "turn on", "turn off",
            "temperature", "thermostat", "degrees",
            "brightness", "dim", "dimmer",
            "color", "colour", "blue", "red", "green", "orange", "yellow",
            "purple", "pink", "white", "warm", "cool",
            "curtain", "curtains", "blind", "blinds",
        ]

        if self._ma_handler and self._ma_handler.is_available():
            nl += [
                "muziek", "speel", "afspelen", "pauzeer", "pauze",
                "nummer", "liedje", "wat speelt", "wat draait",
                "harder", "zachter", "stiller", "volume",
                "volgend", "volgende", "vorig", "vorige",
                "mediaspeler",
            ]
            en += [
                "music", "play", "pause", "stop music",
                "song", "track", "what's playing", "now playing",
                "louder", "quieter", "softer", "volume",
                "next track", "previous track", "media player",
            ]

        return {"nl": nl, "en": en}

    @property
    def category_names(self) -> Dict[str, List[str]]:
        return {
            "nl": ["smart home", "smarthome", "domotica", "huis"],
            "en": ["smart home", "smarthome", "home automation", "house"],
        }

    @property
    def category_options(self) -> Dict[str, Dict[str, Any]]:
        nl_options = [
            "Lampen aan of uit zetten",
            "Helderheid of kleur aanpassen",
            "Thermostaat instellen",
            "Gordijnen openen of sluiten",
            "Schakelaar bedienen",
        ]
        en_options = [
            "Turn lights on or off",
            "Adjust brightness or color",
            "Set the thermostat",
            "Open or close curtains",
            "Control a switch",
        ]

        if self._ma_handler and self._ma_handler.is_available():
            nl_options.append("Muziek afspelen of bedienen")
            en_options.append("Play or control music")

        return {
            "nl": {"name": "Smart Home", "options": nl_options},
            "en": {"name": "Smart Home", "options": en_options},
        }

    @property
    def config_schema(self) -> List[ConfigField]:
        return [
            ConfigField(key="HA_BASE_URL", label="Base URL",
                        required=True, placeholder="https://ha.example.com"),
            ConfigField(key="HA_ACCESS_TOKEN", label="Access Token",
                        required=True, field_type="password",
                        placeholder="Long-lived access token", sensitive=True),
        ]

    def __init__(self):
        self._handler = None
        self._ma_handler = None

    def setup(self, context) -> None:
        super().setup(context)

    def on_enable(self) -> None:
        from .handler import HomeAssistantHandler
        from .music_assistant import MusicAssistantHandler

        base_url = self.context.get_env("HA_BASE_URL")
        access_token = self.context.get_env("HA_ACCESS_TOKEN")
        if base_url and access_token:
            self._handler = HomeAssistantHandler(
                base_url=base_url,
                access_token=access_token,
                ollama=self.context.ollama,
            )
            self._ma_handler = MusicAssistantHandler(self._handler)

    def on_disable(self) -> None:
        self._handler = None
        self._ma_handler = None

    def test_connection(self) -> bool:
        base_url = self.context.get_env("HA_BASE_URL")
        access_token = self.context.get_env("HA_ACCESS_TOKEN")
        if not base_url or not access_token:
            return False
        if self._handler:
            return self._handler.test_connection()
        from .handler import HomeAssistantHandler
        handler = HomeAssistantHandler(
            base_url=base_url, access_token=access_token)
        return handler.test_connection()

    def handle(self, text: str, language: str = "en") -> str:
        if not self._handler:
            return self._msg(
                "Home Assistant is not available.",
                "Home Assistant is niet beschikbaar.",
                language,
            )

        # Route music/media queries to Music Assistant when available
        if self._ma_handler and self._ma_handler.is_available():
            if self._is_music_query(text, language):
                return self._ma_handler.handle(text, language)

        return self._handler.handle(text, language)

    def _is_music_query(self, text: str, language: str) -> bool:
        """Detect if the text is about music/media playback."""
        text_lower = text.lower()
        markers = [
            # Dutch — now-playing queries
            "wat speelt", "wat draait", "welk nummer", "welk liedje",
            "welke muziek", "nu speelt", "nu draait",
            # Dutch — playback controls
            "pauzeer", "pauze", "hervat",
            "volgend nummer", "vorig nummer", "volgende", "vorige",
            "harder", "zachter", "stiller",
            "speel muziek", "stop muziek",
            # Dutch — search/play
            "speel iets", "speel wat", "speel het nummer", "speel het liedje",
            "speel het album", "draai iets", "draai wat", "draai het",
            "zet muziek op", "zet iets op", "start met afspelen",
            "begin met afspelen", "speel af",
            "muziek van", "iets van",
            # English — now-playing queries
            "what's playing", "what is playing", "now playing",
            "current song", "current track", "what song", "what track",
            # English — playback controls
            "pause", "resume",
            "next track", "next song", "previous track", "previous song",
            "volume up", "volume down", "louder", "quieter", "softer",
            "stop music", "stop playing", "play music",
            # English — search/play
            "play something", "play some", "play the song", "play the track",
            "play the album", "put on some", "put on the",
            "something by", "music by",
        ]
        if any(m in text_lower for m in markers):
            return True

        # Heuristic: "speel/play/draai" + content that is not a smart-home device
        smart_home_words = {
            "lamp", "lampen", "licht", "lichten", "verlichting",
            "schakelaar", "gordijn", "gordijnen", "thermostaat",
            "switch", "light", "lights", "curtain", "curtains", "thermostat",
        }
        if text_lower.startswith(("speel ", "play ", "draai ")):
            remaining = set(text_lower.split()[1:])
            if not remaining.intersection(smart_home_words):
                return True

        return False

    # --- Dashboard ---

    @property
    def dashboard_widgets(self) -> List[DashboardWidget]:
        widgets = [
            DashboardWidget(
                id="ha-status",
                title="Home Assistant",
                icon="🏠",
                size="small",
                order=10,
            ),
        ]
        if self._ma_handler and self._ma_handler.is_available():
            widgets.append(
                DashboardWidget(
                    id="ha-media-player",
                    title="Media Players",
                    icon="🎵",
                    size="large",
                    order=11,
                ),
            )
        return widgets

    def render_widget(self, widget_id: str) -> str:
        if widget_id == "ha-status":
            return self._render_status_widget()
        if widget_id == "ha-media-player":
            return self._render_media_widget()
        return ""

    def _render_template(self, name: str, **kwargs) -> str:
        """Load an HTML template from the templates/ directory."""
        path = _TEMPLATE_DIR / name
        tpl = string.Template(path.read_text(encoding="utf-8"))
        return tpl.safe_substitute(**kwargs)

    def _render_status_widget(self) -> str:
        """Compact overview widget for the dashboard."""
        connected = self._handler is not None
        base_url = self.context.get_env("HA_BASE_URL") if self.context else ""

        base_url_section = (
            f'<span style="color:#475569;font-size:0.7rem;margin-left:auto;'
            f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
            f'max-width:160px" title="{base_url}">{base_url}</span>'
            if base_url else ""
        )

        return self._render_template(
            "status_widget.html",
            status_class="on" if connected else "off",
            status_text="Connected" if connected else "Disconnected",
            base_url_section=base_url_section,
        )

    @property
    def dashboard_pages(self) -> List[DashboardPage]:
        return [
            DashboardPage(id="settings", title="Settings", type="config"),
        ]

    def render_page(self, page_id: str) -> str:
        if page_id == "settings":
            return self._render_settings_page()
        return ""

    def _render_settings_page(self) -> str:
        base_url = self.context.get_env("HA_BASE_URL") if self.context else ""
        has_token = bool(self.context.get_env("HA_ACCESS_TOKEN")) if self.context else False

        return self._render_template(
            "settings_page.html",
            base_url=base_url,
            token_placeholder="••••••••" if has_token else "Long-lived access token",
        )

    # --- Music Assistant API & Widget ---

    def handle_api_action(self, action: str, data: dict) -> dict:
        if action == "media/all-players":
            if self._ma_handler:
                return {"players": self._ma_handler.get_all_players_info()}
            return {"players": []}

        if action == "media/now-playing":
            if self._ma_handler:
                return self._ma_handler.get_now_playing_info()
            return {"available": False}

        if action == "media/command":
            if not self._ma_handler:
                return {"error": "Music Assistant not available"}
            cmd = data.get("command", "")
            eid = data.get("entity_id")
            result = False
            if cmd == "play":
                result = self._ma_handler.play(entity_id=eid)
            elif cmd == "pause":
                result = self._ma_handler.pause(entity_id=eid)
            elif cmd == "stop":
                result = self._ma_handler.stop(entity_id=eid)
            elif cmd == "next":
                result = self._ma_handler.next_track(entity_id=eid)
            elif cmd == "previous":
                result = self._ma_handler.previous_track(entity_id=eid)
            elif cmd == "volume":
                result = self._ma_handler.set_volume(
                    float(data.get("value", 0.5)), entity_id=eid)
            elif cmd == "volume_up":
                result = self._ma_handler.volume_up(entity_id=eid)
            elif cmd == "volume_down":
                result = self._ma_handler.volume_down(entity_id=eid)
            return {"success": result}

        if action == "media/play-media":
            if not self._ma_handler:
                return {"error": "Music Assistant not available"}
            query = data.get("query", "")
            if not query:
                return {"error": "No query provided"}
            result = self._ma_handler.play_media(
                query, media_type=data.get("media_type"))
            return {"success": result}

        return {"error": "Unknown action"}

    def _render_media_widget(self) -> str:
        return self._render_template("media_player_widget.html")
