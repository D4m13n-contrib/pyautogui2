# Keyboard Mapping Internals

This page explains how PyAutoGUI2 translates characters into physical key events,
regardless of the keyboard layout active on the system.

> **Audience:** This page targets contributors and advanced users who want to
> understand or extend the keyboard subsystem.

---

## The Problem

Different keyboard layouts place characters at different physical positions.
When PyAutoGUI2 types `"aqua"`, it must press the correct physical key for the
current layout — not just assume a QWERTY arrangement.

```
QWERTY:                       AZERTY:
┌──┬──┬──┬──┬──┬──┬──┬───┐   ┌──┬──┬──┬──┬──┬──┬──┬───┐
│Q │W │E │R │T │Y │U │...│   │A │Z │E │R │T │Y │U │...│
│₁ │₂ │₃ │₄ │₅ │₆ │₇ │   │   │₁ │₂ │₃ │₄ │₅ │₆ │₇ │   │
├──┼──┼──┼──┼──┼──┼──┼───┤   ├──┼──┼──┼──┼──┼──┼──┼───┤
│A │S │D │F │G │H │J │...│   │Q │S │D │F │G │H │J │...│
│₈ │₉ │₁₀│₁₁│₁₂│₁₃│₁₄│   │   │₈ │₉ │₁₀│₁₁│₁₂│₁₃│₁₄│   │
└──┴──┴──┴──┴──┴──┴──┴───┘   └──┴──┴──┴──┴──┴──┴──┴───┘

write("aqua") presses:
Character │ QWERTY pos │ AZERTY pos │ Note
──────────┼────────────┼────────────┼─────────────
   'a'    │     8      │     1      │ Different position!
   'q'    │     1      │     8      │ Different position!
   'u'    │     7      │     7      │ Same position
   'a'    │     8      │     1      │ Different position!

Output: "aqua" on both layouts ✅
```

PyAutoGUI2 solves this with a two-step approach: a static mapping table
(`KEYBOARD_MAPPINGS`) compiled into the source, and a runtime resolution
structure (`_char_map`) built at initialization from the active layout.

---

## `KEYBOARD_MAPPINGS` — The Static Table

`KEYBOARD_MAPPINGS` is defined in `controllers/keyboard.py` and covers all
supported layouts. Its structure is:

```python
KEYBOARD_MAPPINGS: dict[str, dict[str, list[str]]] = {
    "QWERTY": {
        "_":          [...],  # base layer              — no modifier
        "shift":      [...],  # Shift layer
        "altgr":      [...],  # AltGr layer
        "shift_altgr":[...],  # Shift + AltGr layer
    },
    "AZERTY": { ... },
    "QWERTZ": { ... },
}
```

Each list contains **one string per physical key**, in keyboard order
(row by row, left to right). The four lists are aligned: index `N` in `_`,
`shift`, `altgr`, and `shift_altgr` all refer to the same physical key.

### Reading an entry

For AZERTY, the `<` and `>` characters are only reachable via Shift+AltGr:

| Index | `_` | `shift` | `altgr` | `shift_altgr` |
|-------|-----|---------|---------|---------------|
| 0 | `²` | `~` | `¬` | `¬` |
| 1 | `&` | `1` | `¹` | `¡` |
| … | … | … | … | … |
| N | `z` | `Z` | `«` | `<` |
| N+1 | `w` | `W` | `ł` | `>` |

> **Empty entries:** Use an empty string `""` for any key/layer combination
> that produces no character. A layer list can be entirely empty (`[]`) if
> the layout does not use that modifier at all — `setup_postinit()` skips it.

---

## Layout Detection

At initialization, PyAutoGUI2 queries the OS for the active keyboard layout
identifier and resolves it to a layout family via `KEYBOARD_LAYOUTS`
(defined in `utils/keyboard_layouts.py`):

```python
# Simplified — actual call goes through the OSAL layer
layout_id = osal.keyboard.get_layout()    # e.g. "0x040c" on Windows, "fr" on Linux
layout    = KEYBOARD_LAYOUTS[platform][layout_id]["layout"]  # e.g. "AZERTY"
```

`KEYBOARD_LAYOUTS` maps platform-specific identifiers (Windows HKL codes,
Linux XKB names, MacOS input source identifiers) to one of the supported
families: `"QWERTY"`, `"AZERTY"`, or `"QWERTZ"`.

> **OS-specific details:** See [Platform Guide](../platforms/index.md) for how
> each OS exposes its active layout identifier.

---

## `_char_map` — The Runtime Structure

`_char_map` is built by `setup_postinit()` on each OSAL keyboard backend. It
maps every **character or key name** to the information needed to synthesize
the corresponding key event:

```python
_char_map: dict[str, tuple[scancode, str] | tuple[None, None]]
```

- **Key:** a character (`"a"`, `"€"`) or a named key (`"enter"`, `"f1"`)
- **Value:** a `(scancode, modifier)` tuple, or `(None, None)` if unmapped

`modifier` is the string key from `KEYBOARD_MAPPINGS`: `"_"`, `"shift"`,
`"altgr"`, or `"shift_altgr"`. At injection time, this string is resolved
to the actual keycodes stored in `_mods_keycodes`:

```python
self._mods_keycodes = (
    ('shift', self._get_keycode('SHIFT')),
    ('altgr', self._get_keycode('RMENU')),
)
```

`"_"` means no modifier. `"shift_altgr"` means both `shift` and `altgr`
must be held simultaneously.

### How `setup_postinit()` builds `_char_map`

`setup_postinit()` is called once during controller initialization. It
pre-fills `_char_map` with all known key names mapped to `(None, None)`,
then walks every layer of `KEYBOARD_MAPPINGS` for the active layout:

```python
undefined_key = (None, None)
self._char_map = dict.fromkeys(key_names, undefined_key)  # pre-fill named keys

for modifier, kb_mod in all_keymapping[layout].items():
    if len(kb_mod) == 0:                       # skip empty layers entirely
        continue
    for char, key in zip(kb_mod, base_keys, strict=True):
        # first occurrence wins — do not overwrite an already-resolved character
        if char and self._char_map.get(char, undefined_key) == undefined_key:
            self._char_map[char] = (key, modifier)
```

`base_keys` is an ordered list of scancodes matching the physical key order
used in `KEYBOARD_MAPPINGS`. `zip(..., strict=True)` enforces that every
layer has exactly the same length as `base_keys` — a mismatch raises
`ValueError` at initialization time.

**First occurrence wins** — layers are iterated in dict insertion order
(`_` → `shift` → `altgr` → `shift_altgr`). If a character appears in
multiple layers (e.g. a duplicate introduced by a custom mapping), the
first one encountered takes precedence.

---

## Resolution at Runtime

When `write("a")` is called, the full call chain is:

```
KeyboardController.write("a")
  → KeyboardController.press_key("a")
      → osal.keyboard.key_down("a")
          → _char_map["a"]  →  (scancode, modifier)
          → if modifier != "_": inject modifier key_down
          → inject key_down(scancode)
      → osal.keyboard.key_up("a")
          → inject key_up(scancode)
          → if modifier != "_": inject modifier key_up
```

If the character is **not found in `_char_map`** (value is `(None, None)`),
`press_key()` falls back to `codepoint()`, which injects the character
directly via a Unicode input mechanism — bypassing the scancode layer entirely:

```
press_key("é")  →  _char_map lookup → (None, None)
                →  codepoint(0x00E9)   ← Unicode fallback
```

This means `write("été")` works correctly on any layout:
- On AZERTY: `é` is in `_char_map` → direct key press with the correct scancode
- On QWERTY: `é` is not mapped → `codepoint()` fallback

The same fallback applies to dead keys: if a key combination would produce
a dead key (e.g. `^` on some layouts), `press_key()` also routes through
`codepoint()` to guarantee the character is typed as-is.

---

## Adding a New Layout

To add support for a new keyboard layout:

1. **Add the layout family** to `KEYBOARD_MAPPINGS` in `controllers/keyboard.py`,
   following the existing structure (four aligned lists: `_`, `shift`, `altgr`,
   `shift_altgr`). Empty layers can be omitted or set to `[]`.

2. **Register the layout identifiers** for each platform in
   `utils/keyboard_layouts.py`, mapping OS-specific codes to the new family name.

3. **Test** with `write()` on a machine (or VM) running the target layout, using
   the parametrized test suite in `tests/test_controller/test_keyboard.py`.

> **`zip(..., strict=True)`** — every non-empty layer list must have exactly
> the same length as `base_keys`. A mismatch raises `ValueError` at
> initialization time, not silently at runtime.

---

## See Also

- [Keyboard Guide](../guides/keyboard.md) — user-facing API documentation
- [Platform Guide](../platforms/index.md) — OS-specific layout detection details
- [`utils/keyboard_layouts.py`](../../src/pyautogui2/utils/keyboard_layouts.py) — layout identifier mappings
- [`controllers/keyboard.py`](../../src/pyautogui2/controllers/keyboard.py) — `KEYBOARD_MAPPINGS` definition
