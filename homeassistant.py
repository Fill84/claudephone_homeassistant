"""Home Assistant plugin - smart home device control via REST API."""

from typing import Any, Dict, List

<<<<<<< HEAD
from ..base import ConfigField, DashboardPage, DashboardWidget, PluginBase, PluginMeta
=======
from ..base import ConfigField, DashboardPage, PluginBase, PluginMeta
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d


class HomeAssistantPlugin(PluginBase):
    """Home Assistant integration as a plugin."""

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="homeassistant",
            display_name="Home Assistant",
            description="Control smart home devices via Home Assistant REST API",
            version="2.0.0",
            author="Phillippe Pelzer",
        )

    @property
    def keywords(self) -> Dict[str, List[str]]:
        return {
            "nl": [
                "lamp", "lampen", "licht", "lichten", "verlichting",
                "schakelaar", "schakel", "zet aan", "zet uit",
                "doe aan", "doe uit", "aan doen", "uit doen",
                "temperatuur", "thermostaat", "graden",
                "helderheid", "dimmen", "dim",
                "kleur", "blauw", "rood", "groen", "oranje", "geel",
                "paars", "roze", "wit", "warm", "koel",
                "gordijn", "gordijnen", "rolluik",
            ],
            "en": [
                "light", "lights", "lamp", "lamps", "lighting",
                "switch", "turn on", "turn off",
                "temperature", "thermostat", "degrees",
                "brightness", "dim", "dimmer",
                "color", "colour", "blue", "red", "green", "orange", "yellow",
                "purple", "pink", "white", "warm", "cool",
                "curtain", "curtains", "blind", "blinds",
            ],
        }

    @property
    def category_names(self) -> Dict[str, List[str]]:
        return {
            "nl": ["smart home", "smarthome", "domotica", "huis"],
            "en": ["smart home", "smarthome", "home automation", "house"],
        }

    @property
    def category_options(self) -> Dict[str, Dict[str, Any]]:
        return {
            "nl": {
                "name": "Smart Home",
                "options": [
                    "Lampen aan of uit zetten",
                    "Helderheid of kleur aanpassen",
                    "Thermostaat instellen",
                    "Gordijnen openen of sluiten",
                    "Schakelaar bedienen",
                ],
            },
            "en": {
                "name": "Smart Home",
                "options": [
                    "Turn lights on or off",
                    "Adjust brightness or color",
                    "Set the thermostat",
                    "Open or close curtains",
                    "Control a switch",
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
            ConfigField(key="HA_MEDIA_ENABLED", label="Enable Media Control",
                        field_type="toggle", default="true"),
        ]

    def __init__(self):
        self._handler = None

    def setup(self, context) -> None:
        super().setup(context)

    def on_enable(self) -> None:
        from .handler import HomeAssistantHandler

        base_url = self.context.get_env("HA_BASE_URL")
        access_token = self.context.get_env("HA_ACCESS_TOKEN")
        if base_url and access_token:
            self._handler = HomeAssistantHandler(
                base_url=base_url,
                access_token=access_token,
                ollama=self.context.ollama,
            )
<<<<<<< HEAD

    def on_disable(self) -> None:
        self._handler = None
=======
            self._enable_media()

    def on_disable(self) -> None:
        self._handler = None
        self._disable_media()

    def _enable_media(self) -> None:
        """Enable media control if the toggle is on and HA handler is ready."""
        if not self._handler:
            return
        media_enabled = self.context.get_env("HA_MEDIA_ENABLED", "true")
        if media_enabled.lower() in ("true", "1", "yes"):
            from .media import MediaHandler
            self._media_handler = MediaHandler(self._handler)
        else:
            self._media_handler = None

    def _disable_media(self) -> None:
        """Disable media control."""
        self._media_handler = None
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d

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
        return self._handler.handle(text, language)

<<<<<<< HEAD
    # --- Dashboard ---

    @property
    def dashboard_widgets(self) -> List[DashboardWidget]:
        return [
            DashboardWidget(
                id="ha-status",
                title="Home Assistant",
                icon="🏠",
                size="small",
                order=10,
            ),
        ]

    def render_widget(self, widget_id: str) -> str:
        if widget_id == "ha-status":
            return self._render_status_widget()
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
=======
    # --- Dashboard Pages ---
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d

    @property
    def dashboard_pages(self) -> List[DashboardPage]:
        return [
            DashboardPage(id="settings", title="Settings", type="config"),
<<<<<<< HEAD
=======
            DashboardPage(id="media", title="Media Player", type="custom"),
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d
        ]

    def render_page(self, page_id: str) -> str:
        if page_id == "settings":
            return self._render_settings_page()
<<<<<<< HEAD
=======
        if page_id == "media":
            return self._render_media_widget()
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d
        return ""

    def _render_settings_page(self) -> str:
        base_url = self.context.get_env("HA_BASE_URL") if self.context else ""
<<<<<<< HEAD
        has_token = bool(self.context.get_env("HA_ACCESS_TOKEN")) if self.context else False
=======
        has_url = bool(base_url)
        has_token = bool(self.context.get_env("HA_ACCESS_TOKEN")) if self.context else False
        media_enabled = (self.context.get_env("HA_MEDIA_ENABLED", "true") or "").lower() in ("true", "1", "yes") if self.context else True
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d

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
<<<<<<< HEAD
=======
            <div class="card">
                <h3>Media Control</h3>
                <div class="form-row">
                    <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
                        <input type="checkbox" id="ha-media-toggle" {'checked' if media_enabled else ''}
                            onchange="hasSave('HA_MEDIA_ENABLED', this.checked ? 'true' : 'false')">
                        Enable media player control
                    </label>
                    <small style="color:#64748b">Control media players connected to Home Assistant via voice commands.</small>
                </div>
            </div>
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d
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
<<<<<<< HEAD
                if (!r.ok) {{ toast('Save failed: HTTP ' + r.status, 'error'); return; }}
=======
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d
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
<<<<<<< HEAD
                if (!r.ok) {{ el.innerHTML = 'HTTP ' + r.status; el.style.color = '#ef4444'; return; }}
=======
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d
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
<<<<<<< HEAD
=======

    def _render_media_widget(self) -> str:
        media_enabled = (self.context.get_env("HA_MEDIA_ENABLED", "true") or "").lower() in ("true", "1", "yes") if self.context else True

        if not media_enabled:
            return """
            <div class="card" style="text-align:center;padding:2rem">
                <h3 style="margin-bottom:8px">Media Control Disabled</h3>
                <p style="color:#94a3b8">Enable media control in the Settings page to use this widget.</p>
            </div>
            """

        return """
        <div class="card" style="max-width:420px;margin:0 auto">
            <div id="mp-status" style="text-align:center;margin-bottom:16px">
                <div id="mp-title" style="font-size:1.1rem;font-weight:600;color:#e2e8f0">No media playing</div>
                <div id="mp-artist" style="font-size:0.85rem;color:#64748b;margin-top:2px"></div>
                <div id="mp-state" style="font-size:0.75rem;color:#94a3b8;margin-top:4px"></div>
            </div>
            <div style="display:flex;justify-content:center;align-items:center;gap:12px;margin-bottom:16px">
                <button class="btn-sm" onclick="mpCmd('previous')" title="Previous">&#9198;</button>
                <button class="btn-sm" onclick="mpCmd('stop')" title="Stop">&#9209;</button>
                <button class="btn-sm" onclick="mpCmd('play')" title="Play" id="mp-play-btn" style="font-size:1.3rem;padding:8px 16px">&#9654;</button>
                <button class="btn-sm" onclick="mpCmd('pause')" title="Pause">&#9208;</button>
                <button class="btn-sm" onclick="mpCmd('next')" title="Next">&#9197;</button>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
                <span style="color:#94a3b8;font-size:0.8rem">Vol</span>
                <button class="btn-sm" onclick="mpCmd('volume_down')" title="Volume down">&#128265;</button>
                <div style="flex:1;background:#1e293b;border-radius:4px;height:6px;position:relative">
                    <div id="mp-vol-bar" style="background:#38bdf8;height:100%;border-radius:4px;width:50%;transition:width 0.3s"></div>
                </div>
                <button class="btn-sm" onclick="mpCmd('volume_up')" title="Volume up">&#128266;</button>
            </div>
        </div>
        <script>
        async function mpCmd(action) {
            try {
                const r = await fetch('/api/plugins/homeassistant/media/' + action, {method: 'POST'});
                const d = await r.json();
                if (d.success) {
                    mpRefresh();
                } else {
                    toast(d.error || 'Command failed', 'error');
                }
            } catch(e) { toast('Error: ' + e, 'error'); }
        }

        async function mpRefresh() {
            try {
                const r = await fetch('/api/plugins/homeassistant/media/status');
                const d = await r.json();
                if (d.entity_id) {
                    document.getElementById('mp-title').textContent =
                        d.media_title || d.friendly_name || d.entity_id;
                    document.getElementById('mp-artist').textContent =
                        d.media_artist || '';
                    document.getElementById('mp-state').textContent =
                        d.state || '';
                    if (d.volume_level !== undefined) {
                        document.getElementById('mp-vol-bar').style.width =
                            Math.round(d.volume_level * 100) + '%';
                    }
                }
            } catch(e) { /* silent */ }
        }

        // Refresh on load and every 5 seconds
        mpRefresh();
        setInterval(mpRefresh, 5000);
        </script>
        """

    def _is_media_command(self, text: str, language: str) -> bool:
        """Detect if the text is a media command vs smart home."""
        text_lower = text.lower()
        for lang in [language, "en" if language != "en" else "nl"]:
            for keyword in self._MEDIA_KEYWORDS.get(lang, []):
                if keyword in text_lower:
                    return True
        return False
>>>>>>> 4aa4586fece03553ce68537453a971532f389c0d
