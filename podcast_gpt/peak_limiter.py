"""Deterministic sample-peak limiter for an optional separate mix."""
SCALE = 1_000_000
RELEASE_FRAMES = 800


def settings(ceiling):
    if type(ceiling) is not int or (ceiling != 0 and not 8000 <= ceiling <= 28000):
        raise ValueError("Limiter ceiling must be 0 (disabled) or 8000–28000 PCM units")
    if ceiling == 0:
        return None
    return {"algorithm": "instant_attack_linear_release_v1", "ceiling_pcm": ceiling}


def step(sample, gain, config):
    """Immediate gain reduction; bounded 50 ms linear return to unity."""
    peak = abs(sample)
    ceiling = config["ceiling_pcm"]
    allowed = SCALE if peak <= ceiling else ceiling * SCALE // peak
    gain = min(allowed, gain + SCALE // RELEASE_FRAMES, SCALE)
    value = abs(sample) * gain // SCALE
    return (value if sample >= 0 else -value), gain


def blocks(raw_blocks, config, decode, encode):
    if config is None:
        yield from raw_blocks
        return
    gain = SCALE
    for block in raw_blocks:
        values = []
        for sample in decode(block):
            value, gain = step(sample, gain, config)
            values.append(value)
        yield encode(values)
