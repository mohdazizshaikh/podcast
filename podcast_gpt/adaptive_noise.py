"""Conservative per-turn adaptive low-level broadband attenuation (16 kHz)."""
FRAME=320
RAMP=80
SCALE=10000
FLOORS={"light":7000,"medium":5000,"strong":3500}


def settings(mode):
    if not isinstance(mode,str) or mode not in ("off",*FLOORS):
        raise ValueError("Choose off, light, medium or strong adaptive noise reduction")
    if mode=="off":return None
    return {"algorithm":"adaptive_quiet_floor_v1","mode":mode,"frame_samples":FRAME,
            "ramp_samples":RAMP,"minimum_gain_bp":FLOORS[mode]}


def _energy(values):
    return sum(x*x for x in values)//len(values) if values else 0


def _floor(energies):
    if len(energies)<10:return None
    floor=sorted(energies)[(len(energies)-1)//5]
    if not 16**2<=floor<=2000**2:return None
    if sum(e>=9*floor for e in energies)<max(2,len(energies)//5):return None
    return floor


def _gain(energy,floor,minimum):
    if energy<=2*floor:return minimum
    if energy>=9*floor:return SCALE
    return minimum+(SCALE-minimum)*(energy-2*floor)//(7*floor)


def apply(samples,config):
    if config is None or len(samples)<10*FRAME:return samples
    energies=[_energy(samples[i:i+FRAME]) for i in range(0,len(samples)-FRAME+1,FRAME)]
    floor=_floor(energies)
    if floor is None:return samples
    result=[];previous=None
    for start in range(0,len(samples),FRAME):
        part=samples[start:start+FRAME]
        target=_gain(_energy(part),floor,config["minimum_gain_bp"])
        if previous is None:previous=target
        for j,x in enumerate(part):
            level=(previous*(RAMP-j)+target*j)//RAMP if j<RAMP else target
            result.append(abs(x)*level//SCALE*(1 if x>=0 else -1))
        previous=target
    return result if any(result) else samples
