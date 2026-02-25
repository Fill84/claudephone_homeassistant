"""Home Assistant plugin - smart home device control via REST API."""

from typing import Any, Dict, List

from ..base import ConfigField, DashboardPage, DashboardWidget, PluginBase, PluginMeta


class HomeAssistantPlugin(PluginBase):
    """Home Assistant integration as a plugin."""

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="homeassistant",
            display_name="Home Assistant",
            description="Control smart home devices via Home Assistant REST API",
            version="2.0.1",
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
                    title="Now Playing",
                    icon="🎵",
                    size="medium",
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

    def _render_status_widget(self) -> str:
        """Compact overview widget for the dashboard."""
        connected = self._handler is not None
        base_url = self.context.get_env("HA_BASE_URL") if self.context else ""

        return f"""
        <div class="stat" style="margin-bottom:6px">
            <span class="status-dot {'on' if connected else 'off'}"></span>
            <span style="font-size:0.85rem">{'Connected' if connected else 'Disconnected'}</span>
            {f'<span style="color:#475569;font-size:0.7rem;margin-left:auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:160px" title="{base_url}">{base_url}</span>' if base_url else ''}
        </div>
        <div style="margin-top:8px;text-align:right">
            <a href="/plugins/homeassistant/settings" onclick="event.preventDefault();navigate('/plugins/homeassistant/settings')"
               style="color:#38bdf8;text-decoration:none;font-size:0.7rem">Settings →</a>
        </div>
        """

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

        return f"""
        <div class="grid">
            <div class="card">
                <h3>Connection</h3>
                <div class="form-row">
                    <label>Home Assistant URL</label>
                    <div style="display:flex;gap:6px">
                        <input id="ha-url" type="text" value="{base_url}"
                            placeholder="https://ha.example.com" style="flex:1">
                        <button class="btn-sm" onclick="hasSave('HA_BASE_URL', document.getElementById('ha-url').value)">Save</button>
                    </div>
                </div>
                <div class="form-row">
                    <label>Access Token</label>
                    <div style="display:flex;gap:6px">
                        <input id="ha-token" type="password" value=""
                            placeholder="{'••••••••' if has_token else 'Long-lived access token'}"
                            style="flex:1">
                        <button class="btn-sm" onclick="hasSave('HA_ACCESS_TOKEN', document.getElementById('ha-token').value)">Save</button>
                    </div>
                    <small style="color:#64748b">Generate at your HA instance under Profile &gt; Long-Lived Access Tokens</small>
                </div>
                <div class="form-row">
                    <button class="btn-sm" onclick="hasTest()">Test Connection</button>
                    <span id="ha-test-result" style="margin-left:8px"></span>
                </div>
            </div>
        </div>
        <script>
        async function hasSave(key, value) {{
            if (!value.trim()) return;
            try {{
                const r = await fetch('/api/config/', {{
                    method: 'PUT',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{key, value: value.trim()}}),
                }});
                if (!r.ok) {{ toast('Save failed: HTTP ' + r.status, 'error'); return; }}
                const d = await r.json();
                if (d.needs_restart) toast(key + ' saved. Restart required.', 'warning');
                else toast('Saved!', 'success');
            }} catch(e) {{ toast('Save failed: ' + e, 'error'); }}
        }}

        async function hasTest() {{
            const el = document.getElementById('ha-test-result');
            el.innerHTML = 'Testing...';
            el.style.color = '#94a3b8';
            try {{
                const r = await fetch('/api/plugins/homeassistant/test', {{method:'POST'}});
                if (!r.ok) {{ el.innerHTML = 'HTTP ' + r.status; el.style.color = '#ef4444'; return; }}
                const d = await r.json();
                if (d.success) {{
                    el.innerHTML = 'Connected';
                    el.style.color = '#22c55e';
                }} else {{
                    el.innerHTML = 'Failed';
                    el.style.color = '#ef4444';
                }}
            }} catch(e) {{
                el.innerHTML = 'Error: ' + e;
                el.style.color = '#ef4444';
            }}
        }}
        </script>
        """

    # --- Music Assistant API & Widget ---

    def handle_api_action(self, action: str, data: dict) -> dict:
        if action == "media/now-playing":
            if self._ma_handler:
                return self._ma_handler.get_now_playing_info()
            return {"available": False}

        if action == "media/command":
            if not self._ma_handler:
                return {"error": "Music Assistant not available"}
            cmd = data.get("command", "")
            result = False
            if cmd == "play":
                result = self._ma_handler.play()
            elif cmd == "pause":
                result = self._ma_handler.pause()
            elif cmd == "stop":
                result = self._ma_handler.stop()
            elif cmd == "next":
                result = self._ma_handler.next_track()
            elif cmd == "previous":
                result = self._ma_handler.previous_track()
            elif cmd == "volume":
                result = self._ma_handler.set_volume(float(data.get("value", 0.5)))
            elif cmd == "volume_up":
                result = self._ma_handler.volume_up()
            elif cmd == "volume_down":
                result = self._ma_handler.volume_down()
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
        return """
        <div id="ma-widget-content" style="color:#94a3b8;text-align:center;padding:8px;min-height:100px">
            Loading...
        </div>
        <script>
        (function() {
            var ACTION = '/api/plugins/homeassistant/action';

            function fmt(sec) {
                if (sec == null) return '--:--';
                var m = Math.floor(sec / 60);
                var s = Math.floor(sec % 60);
                return m + ':' + (s < 10 ? '0' : '') + s;
            }

            async function refresh() {
                try {
                    var r = await fetch(ACTION + '/media/now-playing', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
                    var d = await r.json();
                    var el = document.getElementById('ma-widget-content');
                    if (!el) return;

                    if (!d.available) {
                        el.innerHTML = '<span style="color:#64748b;font-size:0.85rem">Nothing playing</span>';
                        return;
                    }

                    var art = '';
                    if (d.artwork_url) {
                        art = '<img src="' + d.artwork_url + '" '
                            + 'style="width:64px;height:64px;border-radius:6px;object-fit:cover;flex-shrink:0" '
                            + 'onerror="this.style.display=\\'none\\'">';
                    }

                    var info = '<div style="flex:1;min-width:0;text-align:left">'
                        + '<div style="font-weight:600;font-size:0.9rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#e2e8f0">'
                        + (d.title || 'Unknown') + '</div>'
                        + '<div style="color:#94a3b8;font-size:0.8rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                        + (d.artist || '') + '</div>'
                        + '<div style="color:#64748b;font-size:0.75rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                        + (d.album || '') + '</div>'
                        + '</div>';

                    var progress = '';
                    if (d.duration) {
                        var pct = d.position ? Math.min(100, (d.position / d.duration) * 100) : 0;
                        progress = '<div style="margin-top:8px">'
                            + '<div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#64748b">'
                            + '<span>' + fmt(d.position) + '</span>'
                            + '<span>' + fmt(d.duration) + '</span></div>'
                            + '<div style="background:#1e293b;border-radius:2px;height:3px;margin-top:2px">'
                            + '<div style="background:#38bdf8;height:100%;border-radius:2px;width:'
                            + pct + '%;transition:width 1s linear"></div></div></div>';
                    }

                    var playBtn = d.state === 'playing'
                        ? '<button onclick="maCmd(\\'pause\\')" style="background:none;border:none;color:#e2e8f0;cursor:pointer;padding:4px;font-size:1.3rem" title="Pause">&#9208;</button>'
                        : '<button onclick="maCmd(\\'play\\')" style="background:none;border:none;color:#e2e8f0;cursor:pointer;padding:4px;font-size:1.3rem" title="Play">&#9654;&#65039;</button>';

                    var controls = '<div style="display:flex;justify-content:center;align-items:center;gap:16px;margin-top:8px">'
                        + '<button onclick="maCmd(\\'previous\\')" style="background:none;border:none;color:#e2e8f0;cursor:pointer;padding:4px;font-size:1.1rem" title="Previous">&#9198;</button>'
                        + playBtn
                        + '<button onclick="maCmd(\\'next\\')" style="background:none;border:none;color:#e2e8f0;cursor:pointer;padding:4px;font-size:1.1rem" title="Next">&#9197;</button>'
                        + '</div>';

                    var volPct = d.volume != null ? Math.round(d.volume * 100) : 0;
                    var volume = '<div style="display:flex;align-items:center;gap:6px;margin-top:6px;font-size:0.75rem;color:#64748b">'
                        + '<span>&#128264;</span>'
                        + '<input type="range" min="0" max="100" value="' + volPct
                        + '" style="flex:1;height:3px;accent-color:#38bdf8" '
                        + 'onchange="maVolume(this.value)">'
                        + '<span>' + volPct + '%</span></div>';

                    el.innerHTML = '<div style="display:flex;gap:12px;align-items:center">'
                        + art + info + '</div>' + progress + controls + volume;

                } catch(e) {
                    var el = document.getElementById('ma-widget-content');
                    if (el) el.innerHTML = '<span style="color:#ef4444;font-size:0.85rem">Error loading player</span>';
                }
            }

            window.maCmd = async function(cmd) {
                try {
                    await fetch(ACTION + '/media/command', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({command: cmd}),
                    });
                    setTimeout(refresh, 500);
                } catch(e) {}
            };

            window.maVolume = async function(pct) {
                try {
                    await fetch(ACTION + '/media/command', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({command: 'volume', value: parseInt(pct) / 100}),
                    });
                } catch(e) {}
            };

            refresh();
            setInterval(refresh, 5000);
        })();
        </script>
        """
