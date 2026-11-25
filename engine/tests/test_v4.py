import sys, unittest, tempfile, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from midilab4 import ComposerV4, exact_loop_test, EMOTIONS
from mido import MidiFile

class TestV4(unittest.TestCase):
    def test_immutable_2bar_cycles(self):
        with tempfile.TemporaryDirectory() as temp:
            x=ComposerV4(bpm=94,minutes=1,key='B',mode='minor',repetition='immutable',instrument_detail='expressive').compose()
            p,_=x.write_v4(Path(temp)/'test.mid')
            self.assertTrue(exact_loop_test(p,'Loop Drums',x.total_bars//2)['identical'])
            self.assertTrue(exact_loop_test(p,'Immutable Pulse',x.total_bars//2)['identical'])
    def test_emotion_changes_harmonic_notes_not_locked_notes(self):
        with tempfile.TemporaryDirectory() as temp:
            a=ComposerV4(bpm=120,minutes=1.0,emotional_arc='regret,numbness',seed=7).compose()
            b=ComposerV4(bpm=120,minutes=1.0,emotional_arc='acceptance,triumph',seed=7).compose()
            self.assertEqual(a.events['Loop Drums'],b.events['Loop Drums'])
            self.assertEqual(a.events['Immutable Pulse'],b.events['Immutable Pulse'])
            self.assertNotEqual(a.events['Slow Upper Voices'],b.events['Slow Upper Voices'])
    def test_machine_and_expressive(self):
        a=ComposerV4(minutes=1,bpm=120, instrument_detail='machine').compose()
        b=ComposerV4(minutes=1,bpm=120, instrument_detail='expressive').compose()
        orig=a.events['Memory Plucks'][:]
        a._expressive_performance();b._expressive_performance()
        self.assertEqual(a.events['Memory Plucks'],orig)
        self.assertNotEqual(a.events['Memory Plucks'],b.events['Memory Plucks'])
        self.assertEqual(a.events['Loop Drums'],b.events['Loop Drums'])
    def test_legacy_unchanged(self):
        from midilab3 import ComposerV3
        self.assertTrue(ComposerV3(bpm=123,minutes=1).compose().events['Drum Engine'])
    def test_odd_bar_rounding(self):
        a=ComposerV4(bpm=136,minutes=2.5)
        self.assertEqual(a.total_bars%2,0)
    def test_phase_differs(self):
        a=ComposerV4(bpm=120,minutes=1,repetition='phase').compose()
        b=ComposerV4(bpm=120,minutes=1,repetition='immutable').compose()
        self.assertNotEqual(a.events['Memory Plucks'],b.events['Memory Plucks'])
if __name__=='__main__':unittest.main()
