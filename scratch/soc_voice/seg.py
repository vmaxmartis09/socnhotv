import numpy as np, soundfile as sf
from faster_whisper import WhisperModel
y,sr=sf.read('scratch/soc_voice/a.wav')
m=WhisperModel('small',compute_type='int8')
segs,_=m.transcribe(y.astype('float32'),language='vi',vad_filter=True)
def f0(x):
    x=x-x.mean(); n=len(x)
    if n<800: return 0
    fs=[]
    for i in range(0,n-800,400):
        w=x[i:i+800]
        if np.sqrt((w**2).mean())<0.01: continue
        ac=np.correlate(w,w,'full')[799:]
        lo,hi=int(sr/500),int(sr/70)
        k=lo+np.argmax(ac[lo:hi])
        if ac[k]>0.35*ac[0]: fs.append(sr/k)
    return float(np.median(fs)) if len(fs)>3 else 0
for s in segs:
    a=y[int(s.start*sr):int(s.end*sr)]
    print(f"{s.start:6.1f} {s.end:6.1f} f0={f0(a):5.0f} {s.text.strip()}")
