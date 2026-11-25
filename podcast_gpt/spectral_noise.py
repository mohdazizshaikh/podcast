"""Deterministic per-turn spectral subtraction, mono 16 kHz PCM."""
N=128
HOP=64
Q=32768
FLOORS={"light":21299,"medium":14746,"strong":9830}
SIN=(0, 1608, 3212, 4808, 6393, 7962, 9512, 11039, 12540, 14010, 15447, 16846, 18205, 19520, 20788, 22006, 23170, 24279, 25330, 26320, 27246, 28106, 28899, 29622, 30274, 31357, 32138, 32413, 32610, 32729, 32768)
WINDOW_HALF=(402, 1206, 2009, 2811, 3612, 4410, 5205, 5998, 6787, 7571, 8351, 9127, 9896, 10660, 11417, 12167, 12910, 13646, 14373, 15091, 15800, 16500, 17190, 17869, 18538, 19195, 19841, 20475, 21097, 21706, 22302, 22884, 23453, 24008, 24548, 25073, 25583, 26078, 26557, 27020, 27467, 27897, 28311, 28707, 29086, 29448, 29792, 30118, 30425, 30715, 30986, 31238, 31471, 31686, 31881, 32058, 32214, 32352, 32470, 32568, 32647, 32706, 32746, 32766)
WINDOW=WINDOW_HALF+WINDOW_HALF[::-1]


def settings(mode):
    if not isinstance(mode,str) or mode not in ("off",*FLOORS):raise ValueError("Choose off, light, medium or strong spectral noise reduction")
    if mode=="off":return None
    return {"algorithm":"q15_spectral_subtraction_v1","mode":mode,"fft_samples":N,"hop_samples":HOP,"minimum_gain_q15":FLOORS[mode],"profile_max_frames":64}


def _sin(k):
    k%=N
    if k<=32:return SIN[k]
    if k<=64:return SIN[64-k]
    return -_sin(k-64)


TWIDDLE=tuple((_sin(k+32),-_sin(k)) for k in range(N//2))
ORDER=tuple(int(f'{k:07b}'[::-1],2) for k in range(N))


def _fft(real,imag=None,inverse=False):
    r=[real[k] for k in ORDER];v=[imag[k] for k in ORDER] if imag is not None else [0]*N
    width=2
    while width<=N:
        half=width//2;step=N//width
        for start in range(0,N,width):
            for j in range(half):
                a=start+j;b=a+half;wr,wi=TWIDDLE[j*step]
                if inverse:wi=-wi
                tr=(r[b]*wr-v[b]*wi+Q//2)//Q;ti=(r[b]*wi+v[b]*wr+Q//2)//Q
                r[b]=r[a]-tr;v[b]=v[a]-ti;r[a]+=tr;v[a]+=ti
        width*=2
    return r,v


def _frame(samples,start):
    return [samples[i]*WINDOW[j]//Q if 0<=(i:=start+j)<len(samples) else 0 for j in range(N)]


def _profile(samples):
    frames=[(sum(x*x for x in samples[i:i+N])//N,i) for i in range(0,len(samples)-N+1,N)]
    if len(frames)<25:return None
    frames.sort();quiet=frames[:max(1,len(frames)//5)];floor=quiet[-1][0]
    if not 16**2<=floor<=2000**2 or sum(e>=9*floor for e,_ in frames)<len(frames)//5:return None
    quiet=[(e,i) for e,i in quiet if e>=floor//4 and e>0]
    if len(quiet)<4:return None
    if len(quiet)>64:quiet=[quiet[k*len(quiet)//64] for k in range(64)]
    powers=[0]*(N//2+1)
    for _,i in quiet:
        r,v=_fft(_frame(samples,i))
        for k in range(len(powers)):powers[k]+=r[k]*r[k]+v[k]*v[k]
    return [p//len(quiet) for p in powers]


def apply(samples,config):
    if config is None or len(samples)<25*N:return samples
    profile=_profile(samples)
    if profile is None:return samples
    # Overlap-add with fixed sine windows and exact local window-energy normalization.
    output=[0]*len(samples);weights=[0]*len(samples);minimum=config['minimum_gain_q15']
    for start in range(-HOP,len(samples),HOP):
        r,v=_fft(_frame(samples,start))
        for k,noise in enumerate(profile):
            power=r[k]*r[k]+v[k]*v[k]
            level=max(minimum,Q-noise*Q//max(1,power))
            for j in (k,N-k) if 0<k<N//2 else (k,):
                r[j]=r[j]*level//Q;v[j]=v[j]*level//Q
        r,_=_fft(r,v,True)
        for j,w in enumerate(WINDOW):
            i=start+j
            if 0<=i<len(samples):output[i]+=r[j]*w*Q;weights[i]+=N*w*w
    result=[(x+den//2)//den for x,den in zip(output,weights)]
    return result if any(result) else samples
