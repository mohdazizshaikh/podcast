"""Optional deterministic DC correction and low-level attenuation.

Not noise identification, spectral denoising or speech enhancement.
"""
def settings(remove_dc,gate_threshold):
    if type(remove_dc) is not bool:raise ValueError("DC correction must be boolean")
    if type(gate_threshold) is not int or not 0<=gate_threshold<=1000:
        raise ValueError("Gate threshold must be 0–1000 normalized PCM units")
    if not remove_dc and not gate_threshold:return None
    return {"algorithm":"dc_mean_and_soft_gate_v1","remove_dc":remove_dc,"gate_threshold_pcm":gate_threshold}


def centered(samples):
    if not samples:return samples
    total=sum(samples)
    offset=(abs(total)//len(samples))*(1 if total>=0 else -1)
    if not offset:return samples
    # Python integers preserve full difference range before peak normalization.
    corrected=[s-offset for s in samples]
    if not any(corrected) and any(samples):
        raise ValueError("DC correction would erase a complete nonzero dialogue block; inspect the source")
    return corrected


def step(sample,envelope,level,threshold):
    # Peak envelope releases over about 100 ms. Smooth gate opens over about
    # 10 ms and closes over about 150 ms. Floor is 20% amplitude, not silence.
    envelope=max(abs(sample),envelope-max(1,envelope//1600))
    if envelope>=threshold:level=min(10000,level+50)
    else:level=max(2000,level-4)
    return (abs(sample)*level//10000)*(1 if sample>=0 else -1),envelope,level
