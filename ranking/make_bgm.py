# 랭킹 릴스 배경음(자체 제작, 저작권 문제 없음)을 만든다. 한 번 만들어 bgm.m4a 로 저장해 두고 make_reel.sh 가 쓴다
# 120 BPM, 4마디(8초): 킥 · 스네어 · 하이햇 + 베이스 + 화음 뜯기(C - G - Am - F)
import numpy as np, subprocess, wave
SR=44100; BPM=120; beat=60/BPM; L=int(SR*8)
t=np.arange(L)/SR; out=np.zeros(L)
def env(n, a=0.005, d=0.25):
    x=np.arange(n)/SR; return np.minimum(1, x/a)*np.exp(-x/d)
def add(sig, start):
    s=int(start*SR); e=min(L, s+len(sig)); out[s:e]+=sig[:e-s]
def note(f): return 440*2**((f-69)/12)
for b in range(16):
    st=b*beat
    k=np.arange(int(0.35*SR))/SR; add(0.9*np.sin(2*np.pi*(50+90*np.exp(-k*30))*k)*np.exp(-k*8), st)          # 킥
    if b%2==1: add(0.35*np.random.default_rng(b).standard_normal(int(0.2*SR))*env(int(0.2*SR),0.001,0.06), st)  # 스네어
    for h in (0, 0.5):
        add(0.08*np.random.default_rng(100+b*2+int(h*2)).standard_normal(int(0.05*SR))*env(int(0.05*SR),0.001,0.015), st+h*beat)  # 하이햇
chords=[(48,[60,64,67]),(43,[59,62,67]),(45,[60,64,69]),(41,[60,65,69])]  # C G Am F
for bar,(bass,ch) in enumerate(chords):
    for b in range(4):
        st=(bar*4+b)*beat
        n=int(beat*SR); x=np.arange(n)/SR
        add(0.35*np.sign(np.sin(2*np.pi*note(bass)*x))*0.5*env(n,0.005,0.18), st)   # 베이스(사각파)
        for j,m in enumerate(ch):
            for h in (0,0.5):
                nn=int(0.3*SR); xx=np.arange(nn)/SR
                tri=2/np.pi*np.arcsin(np.sin(2*np.pi*note(m+12)*xx))
                add(0.12*tri*env(nn,0.002,0.12), st+h*beat+j*0.012)            # 화음 뜯기
out=out/np.max(np.abs(out))*0.8
fade=int(0.6*SR); out[-fade:]*=np.linspace(1,0,fade)
pcm=(out*32767).astype(np.int16)
with wave.open('/tmp/bgm.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
subprocess.run(['ffmpeg','-y','-loglevel','error','-i','/tmp/bgm.wav','-ac','2','-c:a','aac','-b:a','160k','bgm.m4a'],check=True)
print('bgm.m4a')
