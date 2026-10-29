import random

FEATURES = ("temperature", "humidity", "sound_volume")
FAULT_MODES = ("overheat", "moisture", "noise")

FAULT_RATE = 0.05

TEMPERATURE_MEAN = 22.0
TEMPERATURE_STD = 1.5
HUMIDITY_MEAN = 45.0
HUMIDITY_STD = 5.0
SOUND_MEAN = 60.0
SOUND_STD = 4.0

OVERHEAT_OFFSET = 12.0
MOISTURE_OFFSET = 45.0
NOISE_OFFSET = 20.0

TEMPERATURE_BOUNDS = (0.0, 80.0)
HUMIDITY_BOUNDS = (0.0, 100.0)
SOUND_BOUNDS = (0.0, 140.0)


def clip_reading(temperature: float, humidity: float, sound_volume: float) -> tuple[float, float, float]:
    """Clip sensor values to physical bounds."""
    return (
        min(TEMPERATURE_BOUNDS[1], max(TEMPERATURE_BOUNDS[0], temperature)),
        min(HUMIDITY_BOUNDS[1], max(HUMIDITY_BOUNDS[0], humidity)),
        min(SOUND_BOUNDS[1], max(SOUND_BOUNDS[0], sound_volume)),
    )


def sample_normal(rng: random.Random) -> dict[str, float]:
    """Draw one in-band shop-floor reading."""
    temperature, humidity, sound_volume = clip_reading(
        rng.gauss(TEMPERATURE_MEAN, TEMPERATURE_STD),
        rng.gauss(HUMIDITY_MEAN, HUMIDITY_STD),
        rng.gauss(SOUND_MEAN, SOUND_STD),
    )
    return {
        "temperature": temperature,
        "humidity": humidity,
        "sound_volume": sound_volume,
    }


def apply_fault(reading: dict[str, float], mode: str) -> dict[str, float]:
    """Shift exactly one sensor for a named fault mode."""
    if mode not in FAULT_MODES:
        raise ValueError(f"unknown fault mode: {mode!r}")
    temperature = reading["temperature"]
    humidity = reading["humidity"]
    sound_volume = reading["sound_volume"]
    if mode == "overheat":
        temperature += OVERHEAT_OFFSET
    elif mode == "moisture":
        humidity += MOISTURE_OFFSET
    else:
        sound_volume += NOISE_OFFSET
    temperature, humidity, sound_volume = clip_reading(temperature, humidity, sound_volume)
    return {
        "temperature": temperature,
        "humidity": humidity,
        "sound_volume": sound_volume,
    }


def sample_fault(rng: random.Random, mode: str | None = None) -> tuple[dict[str, float], str]:
    """Draw a normal reading and apply one single-sensor fault."""
    chosen = mode if mode is not None else rng.choice(FAULT_MODES)
    return apply_fault(sample_normal(rng), chosen), chosen


def sample_stream_item(rng: random.Random) -> tuple[dict[str, float], bool, str | None]:
    """Draw a live item: usually normal, otherwise one fault mode."""
    if rng.random() < FAULT_RATE:
        reading, mode = sample_fault(rng)
        return reading, True, mode
    return sample_normal(rng), False, None
