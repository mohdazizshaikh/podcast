"""Optional deterministic 16 kHz dialogue-only biquad noise filters."""
Q=1<<28
STATE=1<<16
HIGH={60:(264000152,-528000303,264000152,-527927014,259638136),80:(262538058,-525076115,262538058,-524946537,256770238),100:(261084055,-522168111,261084055,-521966747,253934019),120:(259638097,-519276193,259638097,-518987803,251129128)}
HUM={50:(268330090,-536556733,268330090,-536556733,268224724),60:(268309030,-536469111,268309030,-536469111,268182604)}
LOW={4500:(94715336,189430671,94715336,61846523,48579363),6000:(152749329,305498658,152749329,253083375,89478485)}


def settings(highpass=0,hum=0,lowpass=0):
    for value,table in ((highpass,HIGH),(hum,HUM),(lowpass,LOW)):
        if type(value) is not int or (value!=0 and value not in table):
            raise ValueError("Unsupported dialogue noise filter frequency")
    if not (highpass or hum or lowpass):return None
    return {"algorithm":"fixed_biquad_q28_q16_v1","highpass_hz":highpass,"hum_hz":hum,"lowpass_hz":lowpass}


def _round(value,den):
    return ((abs(value)+den//2)//den)*(1 if value>=0 else -1)


def _stage(values,coeff):
    b0,b1,b2,a1,a2=coeff
    x1=x2=y1=y2=0
    for x in values:
        y=_round(b0*x+b1*x1+b2*x2-a1*y1-a2*y2,Q)
        x2,x1=x1,x;y2,y1=y1,y
        yield y


def apply(samples,config):
    if config is None:return samples
    # Fresh state per master block (turn or exact zero pause); no tail leakage.
    values=(s*STATE for s in samples)
    for key,table in (("highpass_hz",HIGH),("hum_hz",HUM),("lowpass_hz",LOW)):
        if config[key]:values=_stage(values,table[config[key]])
    result=[_round(x,STATE) for x in values]
    if any(samples) and not any(result):raise ValueError("Noise filters erased a nonzero dialogue block; inspect source")
    return result
