# 랭킹 릴스 배경음(자체 제작)을 만든다: python3 ranking/make_bgm.py → ranking/bgm/*.m4a (각 8초)
# 2026-11-12 2판: 1판(numpy 사인파 · 톱니파 합성)이 기계음 같다는 평에 따라, 실제 악기 녹음 샘플(FluidR3_GM 사운드폰트, MIT 라이선스)로
# MIDI 를 연주해 만든다. 박자 · 세기를 조금씩 흔들어(사람이 친 것처럼) 기계 느낌을 줄였다.
# 필요: fluidsynth, fluid-soundfont-gm(apt), pretty_midi(pip). 없으면: apt-get install -y fluidsynth fluid-soundfont-gm && pip install pretty_midi
# 01_경쾌(116 BPM 피아노 · 어쿠스틱 베이스 · 플루트 · 가벼운 드럼) · 02_웅장(84 BPM 현악 합주 · 호른 · 팀파니 · 합창)
# 03_긴장(110 BPM 피치카토 반복 · 낮은 현 · 타이코) · 04_통통(128 BPM 마림바 · 우쿨렐레 느낌 나일론 기타 · 박수 · 셰이커)
import pathlib, random, subprocess, tempfile
import pretty_midi as pm

OUT = pathlib.Path(__file__).resolve().parent / 'bgm'
SF2 = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
LEN = 8.0
DRUM = dict(kick=36, snare=38, clap=39, hat=42, ohat=46, crash=49, ride=51, shaker=70, tamb=54, wood=76, cym=57)

class Song:
    def __init__(self, bpm, seed):
        self.m = pm.PrettyMIDI(initial_tempo=bpm); self.b = 60 / bpm; self.r = random.Random(seed); self.ins = {}
    def inst(self, key, prog, drum=False):
        if key not in self.ins:
            i = pm.Instrument(program=prog, is_drum=drum, name=key); self.m.instruments.append(i); self.ins[key] = i
        return self.ins[key]
    def n(self, key, prog, pitch, beat, dur, vel, drum=False, swing=0.012, vj=8):
        i = self.inst(key, prog, drum); s = beat * self.b + self.r.uniform(-swing, swing); s = max(0, s)
        e = s + dur * self.b; v = max(1, min(127, int(vel + self.r.randint(-vj, vj))))
        if s < LEN: i.notes.append(pm.Note(velocity=v, pitch=pitch, start=s, end=min(e, LEN + 1)))
    def d(self, name, beat, vel, swing=0.008): self.n('drum', 0, DRUM[name], beat, 0.25, vel, drum=True, swing=swing)
    def beats(self): return int(LEN / self.b) + 1

def chord_tones(root, minor=False): return [root, root + (3 if minor else 4), root + 7]

def t01():  # 경쾌 3판(11/12): 통기타 · 글로켄슈필이 기계음 같다는 평 → 피아노 반주 + 어쿠스틱 베이스 + 플루트 멜로디 + 가벼운 드럼(사이드 스틱 · 셰이커)
    s = Song(116, 11); prog = [(48, False), (43, False), (45, True), (41, False)]
    for bar in range(4):
        root, mi = prog[bar]; st = bar * 4; t = chord_tones(root + 24, mi)
        s.n('pianoL', 0, root, st, 1.8, 70, swing=0.02, vj=10); s.n('pianoL', 0, root + 7, st + 2, 1.8, 62, swing=0.02, vj=10)
        for bt in (0.5, 1.5, 2.5, 3.5):
            for j, p in enumerate(t): s.n('pianoR', 0, p, st + bt + j * 0.012, 0.45, 60, swing=0.018, vj=12)
        for bt, off in ((0, 0), (1, 7), (2, 12), (3, 7)): s.n('bass', 32, root - 12 + off, st + bt, 0.9, 84, swing=0.015, vj=10)
    for b in range(16):
        if b % 2 == 0: s.d('kick', b, 70, swing=0.012)
        else: s.n('drum', 0, 37, b, 0.25, 64, drum=True, swing=0.012, vj=10)
        for h in (0, .5): s.d('shaker', b + h, 40 if h else 52, swing=0.015)
    mel = [(72, 0, 1.5), (76, 1.5, .5), (79, 2, 2), (74, 4, 1.5), (77, 5.5, .5), (79, 6, 2), (81, 8, 1.5), (79, 9.5, .5), (76, 10, 2), (77, 12, 1), (76, 13, 1), (74, 14, .5), (72, 14.5, 1.5)]
    for p, bt, du in mel: s.n('flute', 73, p, bt, du * 0.95, 76, swing=0.02, vj=10)
    return s

def t02():  # 웅장: Am F C G, 현악 합주 + 호른 + 합창 + 팀파니
    s = Song(84, 2); prog = [(45, True), (41, False), (48, False), (43, False)]; bar_beats = 3
    for bar in range(4):
        root, mi = prog[bar]; st = bar * bar_beats; tones = chord_tones(root, mi)
        for p in tones + [root + 12]: s.n('strings', 48, p + 12, st, bar_beats, 82, swing=0.004)
        s.n('lowstr', 48, root - 12, st, bar_beats, 90, swing=0.004)
        for p in chord_tones(root + 12, mi): s.n('choir', 52, p + 12, st, bar_beats, 62, swing=0.004)
        for p in tones[:2]: s.n('horn', 60, p + 12, st + 1, bar_beats - 1, 86)
        s.n('timp', 47, root, st, 1, 112); s.n('timp', 47, root, st + 2, 0.5, 86); s.n('timp', 47, root, st + 2.5, 0.5, 96)
    s.d('crash', 0, 96); s.d('cym', 9, 100)
    for k in range(6): s.n('timp', 47, 43, 10.2 + k * 0.12, 0.12, 70 + k * 8, swing=0.003)
    return s

def t03():  # 긴장: Dm 반복, 피치카토 8분음 반복 + 낮은 현 지속음 + 타이코 + 째깍
    s = Song(110, 3); bars = [(50, [62, 65, 69, 65]), (50, [62, 65, 70, 65]), (46, [62, 65, 70, 74]), (45, [61, 64, 69, 73])]
    for bar, (root, arp) in enumerate(bars):
        st = bar * 4
        for k in range(8): s.n('pizz', 45, arp[k % 4], st + k * 0.5, 0.4, 88 if k % 2 == 0 else 70)
        s.n('cello', 42, root - 12, st, 4, 84, swing=0.003); s.n('cello', 42, root, st, 4, 66, swing=0.003)
        s.n('taiko', 116, 41, st, 1, 110); s.n('taiko', 116, 41, st + 2.5, 0.5, 92); s.n('taiko', 116, 41, st + 3, 1, 100)
    for b in range(15): s.d('wood', b, 50 if b % 2 else 64, swing=0.004)
    for k, p in enumerate(range(62, 75)): s.n('rise', 49, p, 10 + k * 0.4, 0.5, 60 + k * 4, swing=0.002)
    s.d('cym', 14.6, 104)
    return s

def t04():  # 통통: C Am F G, 마림바 멜로디 + 나일론 기타 + 베이스 + 박수 · 셰이커
    s = Song(128, 4); prog = [(48, False), (45, True), (41, False), (43, False)]
    for bar in range(4):
        root, mi = prog[bar]; st = bar * 4; t = chord_tones(root + 12, mi)
        for k in range(8): s.n('nylon', 24, t[[0, 2, 1, 2][k % 4]] + 12, st + k * 0.5, 0.45, 72 if k % 2 == 0 else 58)
        for bt in (0, 1.5, 2.5, 3): s.n('bass', 32, root, st + bt, 0.4, 88)
    for b in range(17):
        if b % 2 == 0: s.d('kick', b, 90)
        if b % 2: s.d('clap', b, 80)
        for h in (0, .25, .5, .75): s.d('shaker', b + h, 46 if h else 58, swing=0.006)
    mel = [72, 76, 79, 76, 81, 79, 76, 74, 72, 74, 76, 79, 77, 76, 74, 72]
    for k, p in enumerate(mel):
        s.n('marimba', 12, p, k, 0.5, 86); s.n('marimba', 12, p + (0 if k % 4 else 12), k + 0.5, 0.4, 62)
    return s

def render(song, name):
    with tempfile.TemporaryDirectory() as tmp:
        mid = pathlib.Path(tmp) / 'a.mid'; wav = pathlib.Path(tmp) / 'a.wav'; song.m.write(str(mid))
        subprocess.run(['fluidsynth', '-ni', '-g', '0.8', '-r', '44100', '-R', '1', '-C', '1', '-F', str(wav), SF2, str(mid)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        af = f'atrim=0:{LEN},afade=t=in:d=0.05,afade=t=out:st={LEN - 0.7}:d=0.7,loudnorm=I=-16:TP=-1.5:LRA=11'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(wav), '-af', af, '-ar', '44100', '-ac', '2', '-c:a', 'aac', '-b:a', '160k',
                        str(OUT / (name + '.m4a'))], check=True)
    print(name + '.m4a')

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for f, name in [(t01, '01_경쾌'), (t02, '02_웅장'), (t03, '03_긴장'), (t04, '04_통통')]:
        render(f(), name)
