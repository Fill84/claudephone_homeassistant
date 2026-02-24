# ClaudePhone Home Assistant Plugin

A smart home plugin for [ClaudePhone](https://github.com/Fill84/ClaudePhone) that controls your devices via the Home Assistant REST API.

## Features

- **Device control** — turn lights, switches, curtains, and other devices on or off
- **Brightness & color** — adjust brightness, dimming, and light colors
- **Thermostat** — set temperature on climate entities
- **LLM-powered intent** — uses Ollama to match natural language to the right entity and action
- **Keyword fallback** — basic on/off control works even without an LLM
- **Bilingual** — full Dutch and English support with automatic language detection
- **Dashboard settings page** — configure URL and access token from the web UI
- **Connection testing** — verify your Home Assistant connection from the dashboard

## Plugin Structure

```
homeassistant/
  __init__.py       # Exports HomeAssistantPlugin
  homeassistant.py  # Main plugin class (extends PluginBase)
  handler.py        # Home Assistant REST API communication
  README.md         # Documentation
```

## Requirements

- [ClaudePhone](https://github.com/Fill84/ClaudePhone) installed and running
- A [Home Assistant](https://www.home-assistant.io/) instance with the REST API enabled
- A long-lived access token (create one in your Home Assistant profile)

## Installation

### Via Dashboard (recommended)

1. Open the ClaudePhone dashboard
2. Go to the **Plugins** tab
3. Enter the GitHub repository URL and click **Install**

### Manual

Copy the `homeassistant` directory into `src/plugins/` in your ClaudePhone installation and restart the container.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `HA_BASE_URL` | Home Assistant base URL | *required* |
| `HA_ACCESS_TOKEN` | Long-lived access token | *required* |

Configure these via the dashboard Settings page.

## Usage

Once configured, control your smart home during a phone call:

- "Turn on the living room light" / "Doe de woonkamer lamp aan"
- "Dim the bedroom to 50%" / "Dim de slaapkamer naar 50%"
- "Set the thermostat to 21 degrees" / "Zet de thermostaat op 21 graden"

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
