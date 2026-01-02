# Tweening Guide

**Tweening** (or **easing**) functions control how values change over time during
animations. Instead of moving at constant speed, tweening creates natural, smooth,
or dramatic motion effects.

In PyAutoGUI2, tweening applies to:

- Mouse movements — `pointer.move_to()`, `pointer.move_rel()`
- Drag operations — `pointer.drag_to()`, `pointer.drag_rel()`

All tweening functions are managed by the `TweeningManager` singleton, which
provides built-in easing functions (via `pytweening`) and lets you register
your own.

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()

# Constant speed
pag.pointer.move_to(500, 500, duration=1.0, tween="linear")

# Natural deceleration
pag.pointer.move_to(500, 500, duration=1.0, tween="easeOutQuad")

# Bounce at destination
pag.pointer.move_to(500, 500, duration=1.5, tween="easeOutBounce")
```

> **Note:** If `duration=0` (the default), tweening is ignored and movement is
> instant regardless of the `tween` parameter.

---

## Available Easing Functions

Easing functions require `pytweening` to be installed (see
[Installation](../get-started/installation.md)). If `pytweening` is not
available, PyAutoGUI2 falls back to `linear`-only mode — all other tween names
will raise an error at runtime.

### Visualization Legend

The visualizations below show how movement progresses from start (0%) to end
(100%):

**Legend:**
- `▁▂▃▄▅▆▇█` — speed (short bar = slow, tall bar = fast)
- `◀` — pullback (movement backward before starting)
- `▶` — overshoot (movement beyond destination before settling)
- `〰` — bounce (oscillation on one side, like a bouncing ball)
- `∿` — elastic (oscillation on both sides, like a spring)

| Function | Description | Shape | Reference |
|---|---|---|---|
| **Linear** |
| `linear` | Constant speed, no easing | `▄▄▄▄▄▄▄▄` | - |
| **Quadratic** |
| `easeInQuad` | Starts slow, accelerates | `▁▁▂▃▄▅▇█` | [🔍](https://easings.net/#easeInQuad) |
| `easeOutQuad` | Starts fast, decelerates | `█▇▅▄▃▂▁▁` | [🔍](https://easings.net/#easeOutQuad) |
| `easeInOutQuad` | Slow at both ends, fast in middle | `▁▂▄█▄▂▁` | [🔍](https://easings.net/#easeInOutQuad) |
| **Cubic** |
| `easeInCubic` | Starts very slow, accelerates sharply | `▁▁▁▂▃▅▇█` | [🔍](https://easings.net/#easeInCubic) |
| `easeOutCubic` | Starts very fast, decelerates sharply | `█▇▅▃▂▁▁▁` | [🔍](https://easings.net/#easeOutCubic) |
| `easeInOutCubic` | Sharp acceleration and deceleration | `▁▁▃█▃▁▁` | [🔍](https://easings.net/#easeInOutCubic) |
| **Quartic** |
| `easeInQuart` | Extremely slow start, explosive finish | `▁▁▁▁▂▄▇█` | [🔍](https://easings.net/#easeInQuart) |
| `easeOutQuart` | Explosive start, extremely slow finish | `█▇▄▂▁▁▁▁` | [🔍](https://easings.net/#easeOutQuart) |
| `easeInOutQuart` | Very sharp acceleration and deceleration | `▁▁▂█▂▁▁` | [🔍](https://easings.net/#easeInOutQuart) |
| **Quintic** |
| `easeInQuint` | Near-stationary start, maximum acceleration | `▁▁▁▁▁▃▇█` | [🔍](https://easings.net/#easeInQuint) |
| `easeOutQuint` | Maximum deceleration, near-stationary finish | `█▇▃▁▁▁▁▁` | [🔍](https://easings.net/#easeOutQuint) |
| `easeInOutQuint` | Extreme acceleration and deceleration | `▁▁▁█▁▁▁` | [🔍](https://easings.net/#easeInOutQuint) |
| **Sine** |
| `easeInSine` | Gentle slow start | `▁▂▃▄▅▆▇█` | [🔍](https://easings.net/#easeInSine) |
| `easeOutSine` | Gentle slow finish | `█▇▆▅▄▃▂▁` | [🔍](https://easings.net/#easeOutSine) |
| `easeInOutSine` | Smooth and gentle at both ends | `▁▂▄▅▄▂▁` | [🔍](https://easings.net/#easeInOutSine) |
| **Exponential** |
| `easeInExpo` | Nearly frozen start, explosive acceleration | `▁▁▁▁▁▂▅█` | [🔍](https://easings.net/#easeInExpo) |
| `easeOutExpo` | Explosive start, nearly frozen finish | `█▅▂▁▁▁▁▁` | [🔍](https://easings.net/#easeOutExpo) |
| `easeInOutExpo` | Nearly frozen at both ends, explosive middle | `▁▁▁█▁▁▁` | [🔍](https://easings.net/#easeInOutExpo) |
| **Circular** |
| `easeInCirc` | Slow start, abrupt acceleration at end | `▁▁▂▃▄▆██` | [🔍](https://easings.net/#easeInCirc) |
| `easeOutCirc` | Abrupt deceleration at start, slow finish | `██▆▄▃▂▁▁` | [🔍](https://easings.net/#easeOutCirc) |
| `easeInOutCirc` | Abrupt transition in the middle | `▁▁▃██▃▁▁` | [🔍](https://easings.net/#easeInOutCirc) |
| **Elastic** |
| `easeInElastic` | Oscillates at start, then shoots forward | `∿▃▂▁` | [🔍](https://easings.net/#easeInElastic) |
| `easeOutElastic` | Arrives then oscillates to rest | `▁▂▃∿` | [🔍](https://easings.net/#easeOutElastic) |
| `easeInOutElastic` | Oscillates at both ends | `▁∿▁` | [🔍](https://easings.net/#easeInOutElastic) |
| **Back** |
| `easeInBack` | Slight pullback before moving forward | `▁◀▂▄▆█` | [🔍](https://easings.net/#easeInBack) |
| `easeOutBack` | Overshoots destination, then settles | `█▆▄▂▶▁` | [🔍](https://easings.net/#easeOutBack) |
| `easeInOutBack` | Pullback at start, overshoot at end | `▁◀▃▃▶▁` | [🔍](https://easings.net/#easeInOutBack) |
| **Bounce** |
| `easeInBounce` | Bounces before starting | `〰▃▂▁` | [🔍](https://easings.net/#easeInBounce) |
| `easeOutBounce` | Arrives then bounces to rest | `▁▂▃〰` | [🔍](https://easings.net/#easeOutBounce) |
| `easeInOutBounce` | Bounces at both ends | `▁〰▁` | [🔍](https://easings.net/#easeInOutBounce) |

### Common Use Cases

**Natural mouse movement:**
- `easeOutQuad` — most human-like (quick start, gentle stop)
- `easeInOutQuad` — smooth and predictable

**Playful or attention-grabbing:**
- `easeOutBounce` — fun "bounce" at destination
- `easeOutElastic` — springy effect

**Dramatic:**
- `easeInExpo` — sudden burst of speed
- `easeOutBack` — overshoots then corrects

**Precise or technical:**
- `linear` — constant speed, fully predictable

---

## Using Tweening

All pointer movement and drag functions accept a `tween` parameter (string name):

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()

# Move with natural deceleration
pag.pointer.move_to(800, 600, duration=0.5, tween="easeOutQuad")

# Relative move with easing
pag.pointer.move_rel(100, 50, duration=0.3, tween="easeInOutSine")

# Drag with smooth easing
pag.pointer.drag_to(500, 500, button="left", duration=1.0, tween="easeInOutQuad")

# Drag with elastic effect
pag.pointer.drag_rel(200, 0, button="left", duration=0.8, tween="easeOutElastic")
```

---

## Custom Easing Functions

### Function Signature

A valid easing function takes a single `float` in `[0.0, 1.0]` and returns a
`float` representing eased progress:

```python
def my_tween(n: float) -> float:
    """
    Args:
        n: Progress from 0.0 (start) to 1.0 (end).

    Returns:
        Eased value — typically 0.0 to 1.0, but can overshoot
        (e.g. elastic and back functions return values outside this range).
    """
    return n  # Linear: no easing
```

### Registering a Custom Function

Use `TweeningManager().add_tween()` to register a custom function globally:

```python
from pyautogui2 import PyAutoGUI
from pyautogui2.utils.tweening import TweeningManager

pag = PyAutoGUI()

def ease_out_cubic(n: float) -> float:
    """Cubic deceleration."""
    return 1 - (1 - n) ** 3

TweeningManager().add_tween("myEase", ease_out_cubic)

pag.pointer.move_to(500, 500, duration=1.0, tween="myEase")
```

If the name is already taken, `add_tween()` raises a `ValueError`. Pass
`force=True` to override an existing function:

```python
TweeningManager().add_tween("myEase", new_func, force=True)
```

Because `TweeningManager` is a singleton, registered tweens are available
globally for the lifetime of the process — you only need to register once.

### Example: Stepped Easing

```python
def ease_stepped(n: float) -> float:
    """Moves in discrete steps: 0%, 25%, 50%, 75%, 100%."""
    return round(n * 4) / 4

TweeningManager().add_tween("stepped", ease_stepped)

pag.pointer.move_to(500, 500, duration=1.0, tween="stepped")
```

---

## How Tweening Works Internally

When you call a movement function with `duration > 0`, PyAutoGUI2:

1. Calculates the number of steps based on distance and duration
2. Retrieves the easing function from `TweeningManager` by name
3. Generates intermediate positions using the easing function:

```python
# Simplified internal logic
tween_func = TweeningManager()(tween or "linear")

for n in range(num_steps):
    progress = n / num_steps          # Linear: 0.0 → 1.0
    eased = tween_func(progress)      # Eased: 0.0 → 1.0 (or overshoot)

    x, y = get_point_on_line(start_x, start_y, target_x, target_y, eased)
    move_to(x, y)
    sleep(step_duration)

move_to(target_x, target_y)          # Guarantee exact final position
```

The easing function transforms linear progress into eased progress, which is
then used to interpolate positions along the movement path. The final position
is always exact regardless of rounding in intermediate steps.

---

## Best Practices

**Match duration to the easing style**

- Short durations (0.1–0.3 s): simple easing (`easeOutQuad`, `easeInOutQuad`)
- Medium durations (0.5–1.0 s): more expressive effects (`easeOutBounce`, `easeOutElastic`)
- Long durations (1.0 s+): subtle easing to avoid over-animation

**Instant movement**

Pass `duration=0` (or omit it) for immediate positioning with no tweening
overhead. This is the default and the right choice for most automation scripts.

**Human-like movement**

`easeOutQuad` and `easeInOutQuad` best mimic natural hand deceleration. For
additional realism, vary the `duration` slightly between calls.

**Test custom functions visually**

```python
# Slow, visible test movement
pag.pointer.move_to(1000, 500, duration=2.0, tween="myEase")
```

---

## Related

- [Pointer guide](pointer.md) — mouse movement and clicking
- [Settings guide](settings.md) — global `PAUSE` and `FAILSAFE` configuration
