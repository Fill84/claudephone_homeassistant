"""Home Assistant REST API handler for smart home device control."""

import json
import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class HomeAssistantHandler:
    """Control Home Assistant devices via the REST API."""

    def __init__(self, base_url: str, access_token: str, ollama=None):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.ollama = ollama
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def test_connection(self) -> bool:
        """Test if Home Assistant is reachable."""
        try:
            r = requests.get(
                f"{self.base_url}/api/",
                headers=self._headers,
                timeout=5,
            )
            return r.status_code == 200
        except Exception as e:
            logger.warning("HA connection test failed: %s", e)
            return False

    def handle(self, text: str, language: str = "en") -> str:
        """Handle a smart home command using the LLM to interpret intent."""
        text_lower = text.lower()

        # Try to interpret the command with LLM if available
        if self.ollama:
            return self._handle_with_llm(text, language)

        # Fallback: keyword-based handling
        return self._handle_keywords(text_lower, language)

    def _handle_with_llm(self, text: str, language: str) -> str:
        """Use LLM to interpret the smart home command."""
        entities = self._get_entities()
        if not entities:
            return self._msg(
                "Could not retrieve devices from Home Assistant.",
                "Kon geen apparaten ophalen van Home Assistant.",
                language,
            )

        # Build entity list for context
        entity_names = []
        for e in entities[:50]:  # Limit to avoid huge prompts
            eid = e.get("entity_id", "")
            name = e.get("attributes", {}).get("friendly_name", eid)
            state = e.get("state", "unknown")
            entity_names.append(f"- {name} ({eid}): {state}")

        entities_text = "\n".join(entity_names)

        prompt = (
            f"You are a smart home assistant. The user said: \"{text}\"\n\n"
            f"Available devices:\n{entities_text}\n\n"
            f"Respond with a JSON object containing:\n"
            f"- \"domain\": the HA domain (e.g. light, switch, climate)\n"
            f"- \"service\": the service to call (e.g. turn_on, turn_off, toggle)\n"
            f"- \"entity_id\": the entity to control\n"
            f"- \"data\": optional service data dict\n"
            f"- \"response\": a short {'Dutch' if language == 'nl' else 'English'} "
            f"confirmation message\n\n"
            f"If you cannot determine the action, set \"service\" to null and "
            f"provide a helpful \"response\".\n"
            f"Respond with ONLY the JSON object, no other text."
        )

        try:
            result = self.ollama.generate(prompt)
            if not result:
                return self._msg(
                    "Could not process the command.",
                    "Kon het commando niet verwerken.",
                    language,
                )

            # Try to parse LLM response as JSON
            result_text = result.strip()
            # Strip markdown code block if present
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[-1]
                result_text = result_text.rsplit("```", 1)[0]

            data = json.loads(result_text)
            service = data.get("service")
            response_msg = data.get("response", "")

            if service and data.get("entity_id"):
                self._call_service(
                    data["domain"],
                    service,
                    data["entity_id"],
                    data.get("data"),
                )
                return response_msg or self._msg("Done.", "Gedaan.", language)

            return response_msg or self._msg(
                "I don't understand that command.",
                "Ik begrijp dat commando niet.",
                language,
            )
        except Exception as e:
            logger.warning("LLM smart home handling failed: %s", e)
            return self._handle_keywords(text.lower(), language)

    def _handle_keywords(self, text: str, language: str) -> str:
        """Fallback keyword-based handling without LLM."""
        entities = self._get_entities()
        if not entities:
            return self._msg(
                "No devices available.",
                "Geen apparaten beschikbaar.",
                language,
            )

        # Simple on/off detection
        turn_on = any(k in text for k in [
            "aan", "on", "doe aan", "zet aan", "turn on",
        ])
        turn_off = any(k in text for k in [
            "uit", "off", "doe uit", "zet uit", "turn off",
        ])

        if not turn_on and not turn_off:
            return self._msg(
                "Please say what you want to turn on or off.",
                "Zeg wat je aan of uit wilt zetten.",
                language,
            )

        # Find matching entity by name
        target = self._find_entity(text, entities)
        if not target:
            return self._msg(
                "I could not find that device.",
                "Ik kon dat apparaat niet vinden.",
                language,
            )

        entity_id = target["entity_id"]
        domain = entity_id.split(".")[0]
        service = "turn_on" if turn_on else "turn_off"

        self._call_service(domain, service, entity_id)
        name = target.get("attributes", {}).get("friendly_name", entity_id)
        action = self._msg("on", "aan", language) if turn_on else self._msg("off", "uit", language)
        return f"{name} {action}."

    def _find_entity(self, text: str, entities: list) -> Optional[dict]:
        """Find the best matching entity for the given text."""
        text_lower = text.lower()
        best = None
        best_score = 0

        for e in entities:
            eid = e.get("entity_id", "")
            name = e.get("attributes", {}).get("friendly_name", "")
            # Score based on how many words from the entity name appear in text
            words = name.lower().split()
            score = sum(1 for w in words if w in text_lower)
            if score > best_score:
                best_score = score
                best = e

        return best if best_score > 0 else None

    def has_media_players(self) -> bool:
        """Check if Home Assistant has any media_player entities."""
        entities = self._get_entities()
        return any(
            e.get("entity_id", "").startswith("media_player.")
            for e in entities
        )

    def get_services(self) -> List[Dict[str, Any]]:
        """Get available service domains from Home Assistant."""
        try:
            r = requests.get(
                f"{self.base_url}/api/services",
                headers=self._headers,
                timeout=5,
            )
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.warning("Failed to get HA services: %s", e)
        return []

    def _get_entities(self) -> List[Dict[str, Any]]:
        """Get all entities from Home Assistant."""
        try:
            r = requests.get(
                f"{self.base_url}/api/states",
                headers=self._headers,
                timeout=10,
            )
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.warning("Failed to get HA entities: %s", e)
        return []

    def _call_service(
        self, domain: str, service: str, entity_id: str,
        data: Optional[Dict] = None,
    ) -> bool:
        """Call a Home Assistant service."""
        payload = {"entity_id": entity_id}
        if data:
            payload.update(data)
        try:
            r = requests.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                headers=self._headers,
                json=payload,
                timeout=10,
            )
            return r.status_code in (200, 201)
        except Exception as e:
            logger.error("HA service call failed: %s", e)
            return False

    def _msg(self, en: str, nl: str, language: str) -> str:
        return nl if language == "nl" else en
