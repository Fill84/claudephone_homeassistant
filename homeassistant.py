"""Home Assistant plugin - smart home and media control via REST API."""

from typing import Any, Dict, List

from ..base import ConfigField, PluginBase, PluginMeta


class HomeAssistantPlugin(PluginBase):
    """Home Assistant integration as a plugin."""

    # Keywords that identify a media command (vs smart home)
    _MEDIA_KEYWORDS = {
        "nl": [
            "muziek", "speel", "afspelen", "pauze", "pauzeer",
            "volume", "harder", "zachter", "volgend", "vorig",
            "liedje", "nummer",
        ],
        "en": [
            "music", "play", "pause", "volume", "louder",
            "quieter", "softer", "next", "previous", "song", "track",
        ],
    }

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="homeassistant",
            display_name="Home Assistant",
            description="Control smart home devices and media via Home Assistant REST API",
            version="1.1.0",
            author="Phillippe Pelzer",
        )

    @property
    def keywords(self) -> Dict[str, List[str]]:
        return {
            "nl": [
                # Smart home
                "lamp", "lampen", "licht", "lichten", "verlichting",
                "schakelaar", "schakel", "zet aan", "zet uit",
                "doe aan", "doe uit", "aan doen", "uit doen",
                "temperatuur", "thermostaat", "graden",
                "helderheid", "dimmen", "dim",
                "kleur", "blauw", "rood", "groen", "oranje", "geel",
                "paars", "roze", "wit", "warm", "koel",
                "gordijn", "gordijnen", "rolluik",
                # Media
                "muziek", "speel", "afspelen", "stop", "pauze",
                "pauzeer", "volume", "harder", "zachter",
                "volgend", "vorig", "liedje", "nummer",
            ],
            "en": [
                # Smart home
                "light", "lights", "lamp", "lamps", "lighting",
                "switch", "turn on", "turn off",
                "temperature", "thermostat", "degrees",
                "brightness", "dim", "dimmer",
                "color", "colour", "blue", "red", "green", "orange", "yellow",
                "purple", "pink", "white", "warm", "cool",
                "curtain", "curtains", "blind", "blinds",
                # Media
                "music", "play", "stop", "pause",
                "volume", "louder", "quieter", "softer",
                "next", "previous", "song", "track",
            ],
        }

    @property
    def category_names(self) -> Dict[str, List[str]]:
        return {
            "nl": ["smart home", "smarthome", "domotica", "huis", "media", "muziek"],
            "en": ["smart home", "smarthome", "home automation", "house", "media", "music"],
        }

    @property
    def category_options(self) -> Dict[str, Dict[str, Any]]:
        return {
            "nl": {
                "name": "Smart Home & Media",
                "options": [
                    "Lampen aan of uit zetten",
                    "Helderheid of kleur aanpassen",
                    "Thermostaat instellen",
                    "Gordijnen openen of sluiten",
                    "Schakelaar bedienen",
                    "Muziek afspelen",
                    "Muziek pauzeren of stoppen",
                    "Volume aanpassen",
                    "Volgend of vorig nummer",
                ],
            },
            "en": {
                "name": "Smart Home & Media",
                "options": [
                    "Turn lights on or off",
                    "Adjust brightness or color",
                    "Set the thermostat",
                    "Open or close curtains",
                    "Control a switch",
                    "Play music",
                    "Pause or stop music",
                    "Adjust volume",
                    "Next or previous track",
                ],
            },
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

    def setup(self, context) -> None:
        super().setup(context)
        self._handler = None
        self._media_handler = None

    def on_enable(self) -> None:
        from .handler import HomeAssistantHandler
        from .media import MediaHandler

        base_url = self.context.get_env("HA_BASE_URL")
        access_token = self.context.get_env("HA_ACCESS_TOKEN")
        if base_url and access_token:
            self._handler = HomeAssistantHandler(
                base_url=base_url,
                access_token=access_token,
                ollama=self.context.ollama,
            )
            self._media_handler = MediaHandler(self._handler)

    def on_disable(self) -> None:
        self._handler = None
        self._media_handler = None

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

        if self._is_media_command(text, language):
            if self._media_handler:
                return self._media_handler.handle(text, language)
            return self._msg(
                "Media control is not available.",
                "Mediabediening is niet beschikbaar.",
                language,
            )

        return self._handler.handle(text, language)

    def _is_media_command(self, text: str, language: str) -> bool:
        """Detect if the text is a media command vs smart home."""
        text_lower = text.lower()
        for lang in [language, "en" if language != "en" else "nl"]:
            for keyword in self._MEDIA_KEYWORDS.get(lang, []):
                if keyword in text_lower:
                    return True
        return False
