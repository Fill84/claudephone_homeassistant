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

    def on_disable(self) -> None:
        self._handler = None

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
0d
