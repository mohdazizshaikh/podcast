"""Optional deterministic peak-envelope speech compression before bed mixing."""
def settings(ratio,threshold):
    if type(ratio) is not int or not 1<=ratio<=6:raise ValueError("Compression ratio must be 1–6")
    if type(threshold) is not int or not 2000<=threshold<=20000:raise ValueError("Compression threshold must be 2000–20000 PCM units")
    if ratio==1:
        if threshold!=12000:raise ValueError("Choose a compression ratio above 1 to set a threshold")
        return None
    return {"algorithm":"instant_attack_integer_release_v1","ratio":ratio,"threshold_pcm":threshold}


def step(sample,envelope,config):
    # Immediate peak capture; approximately 100 ms integer release time constant.
    envelope=max(abs(sample),envelope-max(1,envelope//1600))
    threshold=config["threshold_pcm"]
    if envelope<=threshold:return sample,envelope
    desired=threshold+(envelope-threshold)//config["ratio"]
    return (abs(sample)*desired//envelope)*(1 if sample>=0 else -1),envelope
