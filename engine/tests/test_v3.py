import sys,unittest, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from harmony3 import normalize_key, section_chords, degree_chord, voice_lead, MODES
from fretboard3 import chord_shape, TUNING
from rhythm3 import ENGINES,render_bar
from midilab3 import ComposerV3
from analyze3 import analyze

class TestHarmony(unittest.TestCase):
    def test_12_keys_and_four_modes(self):
        for tonic in ('C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B'):
            for mode in MODES:
                with self.subTest(tonic=tonic,mode=mode):
                    prev=None
                    for c in section_chords(normalize_key(tonic),mode,'tender'):
                        v=voice_lead(c,prev)
                        self.assertEqual(len(v),4)
                        self.assertEqual(len(set(v)),4)
                        self.assertTrue(all(49<=n<=77 for n in v))
                        self.assertEqual({n%12 for n in v},set(c.pcs))
                        prev=v

    def test_modes_actually_change_pitch_classes(self):
        c=normalize_key('D')
        self.assertNotEqual(section_chords(c,'major')[0].pcs,section_chords(c,'minor')[0].pcs)
        self.assertNotEqual(degree_chord(c,'minor',4).pcs,degree_chord(c,'dorian',4).pcs)

class TestRhythms(unittest.TestCase):
    def test_patterns_distinct(self):
        sigs=[]
        for engine in ENGINES:
            notes=render_bar(engine,3,.8,6,True,.12)
            self.assertGreaterEqual(len(notes),6)
            self.assertTrue(all(0<=p<4 and 0<n<128 and 0<v<128 and d>0 for p,n,v,d in notes))
            sigs.append(tuple((p,n) for p,n,v,d in notes))
        self.assertEqual(len(set(sigs)),len(ENGINES))

    def test_ukg_swing_changes_hat_positions(self):
        a=[p for p,n,v,d in render_bar('ukg',0,.9,5,False,0) if n==42]
        b=[p for p,n,v,d in render_bar('ukg',0,.9,5,False,.12) if n==42]
        self.assertNotEqual(a,b)

class TestGuitar(unittest.TestCase):
    def test_chord_grips_plausible(self):
        for pcs in ((0,4,7,11),(2,5,9,0),(6,10,1,4),(1,5,8,11)):
            grip=chord_shape(pcs)
            self.assertIsNotNone(grip)
            self.assertGreaterEqual(len(grip),3)
            self.assertEqual(len({x[0] for x in grip}),len(grip))
            self.assertTrue(all(p==TUNING[s]+f and 0<=f<=12 for s,f,p in grip))
            f=[x[1] for x in grip if x[1]>0]
            self.assertLessEqual(max(f)-min(f) if f else 0,4)

class TestComposition(unittest.TestCase):
    def test_clean_midi_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.mid'
            c=ComposerV3(bpm=128,minutes=1.2,key='F#',mode='minor',
                         profile='no_technique_balearic',seed=1234,feel='none').compose()
            midi,man=c.write(path)
            rep=analyze(midi,man)
            self.assertTrue(rep['technical_pass'],rep['validation'])
            self.assertTrue(c.use_sub)
            self.assertGreater(len(c.events['Sub Sequence']),0)
            self.assertGreater(len(c.motif_log),0)
            self.assertTrue(any(x['borrowed'] for x in c.chord_log))
            self.assertEqual(rep['ppq'],480)

    def test_same_seed_has_same_hook(self):
        a=ComposerV3(profile='yl_tender_nocturne',seed=99)
        b=ComposerV3(profile='yl_tender_nocturne',seed=99,variant='strange')
        self.assertEqual(a.motif['pitches'],b.motif['pitches'])

    def test_tempo_duration_near_target(self):
        for bpm,minutes in ((76,4.),(124,3.6),(136,2.6)):
            c=ComposerV3(bpm=bpm,minutes=minutes)
            self.assertLess(abs((c.total_bars*4/bpm)-minutes),4/bpm)

if __name__=='__main__':unittest.main()
