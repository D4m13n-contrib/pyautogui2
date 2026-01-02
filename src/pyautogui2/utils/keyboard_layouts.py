"""All available keyboard layouts."""


KEYBOARD_LAYOUTS: dict[str, dict[str, dict[str, str]]] = {
  "windows": {
    "0x0409": { "layout": "QWERTY", "description": "English (United States)" },
    "0x0809": { "layout": "QWERTY", "description": "English (United Kingdom)" },
    "0x0c09": { "layout": "QWERTY", "description": "English (Australia)" },
    "0x1009": { "layout": "QWERTY", "description": "English (Canada)" },

    "0x040c": { "layout": "AZERTY", "description": "French (France)" },
    "0x080c": { "layout": "AZERTY", "description": "French (Belgium)" },
    "0x0c0c": { "layout": "QWERTY", "description": "French (Canada)" },

    "0x0407": { "layout": "QWERTZ", "description": "German (Germany)" },
    "0x0807": { "layout": "QWERTZ", "description": "German (Switzerland)" },
    "0x0c07": { "layout": "QWERTZ", "description": "German (Austria)" }
  },

  "linux": {
    "us":   { "layout": "QWERTY", "description": "English (US)" },
    "gb":   { "layout": "QWERTY", "description": "English (UK)" },
    "uk":   { "layout": "QWERTY", "description": "English (UK alternative)" },
    "ca":   { "layout": "QWERTY", "description": "Canadian (English)" },

    "fr":     { "layout": "AZERTY", "description": "French (France)" },
    "fr-oss": { "layout": "AZERTY", "description": "French (OSS variant)" },
    "be":     { "layout": "AZERTY", "description": "Belgian" },
    "fr-be":  { "layout": "AZERTY", "description": "Belgian (alt name)" },

    "de":   { "layout": "QWERTZ", "description": "German" },
    "ch":   { "layout": "QWERTZ", "description": "Swiss (generic)" },
    "ch-de":{ "layout": "QWERTZ", "description": "Swiss German" },
    "ch-fr":{ "layout": "QWERTZ", "description": "Swiss French" },

    "sv": { "layout": "QWERTY", "description": "Swedish" },
    "fi": { "layout": "QWERTY", "description": "Finnish" },
    "no": { "layout": "QWERTY", "description": "Norwegian" },
    "da": { "layout": "QWERTY", "description": "Danish" }
  },

  "macos": {
    "US":              { "layout": "QWERTY", "description": "English (US)" },
    "British":         { "layout": "QWERTY", "description": "English (UK)" },
    "Canadian English":{ "layout": "QWERTY", "description": "Canadian English" },

    "French":          { "layout": "AZERTY", "description": "French (France)" },
    "French - AZERTY": { "layout": "AZERTY", "description": "Explicit AZERTY mapping" },
    "Belgian":         { "layout": "AZERTY", "description": "Belgian" },

    "German":       { "layout": "QWERTZ", "description": "German" },
    "Swiss German": { "layout": "QWERTZ", "description": "Swiss German" },
    "Swiss French": { "layout": "QWERTZ", "description": "Swiss French" },

    "Swedish":  { "layout": "QWERTY", "description": "Swedish" },
    "Finnish":  { "layout": "QWERTY", "description": "Finnish" },
    "Norwegian":{ "layout": "QWERTY", "description": "Norwegian" },
    "Danish":   { "layout": "QWERTY", "description": "Danish" }
  }
}
