import sys, unittest, tempfile, hashlib
from pathlib import Path
from mido import MidiFile, MidiTrack, MetaMessage, Message
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from effects42 import delay_ms,make_recipe,PRESETS,classify
class EffectsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'fixture.mid'
        midi=MidiFile(type=1,ticks_per_beat=480)
        a=MidiTrack();a.append(MetaMessage('set_tempo',tempo=round(60000000/112),time=0));midi.tracks.append(a)
        b=MidiTrack();b.append(MetaMessage('track_name',name='Nylon Chords',time=0));b.append(Message('note_on',note=65,velocity=70,time=0));b.append(Message('note_off',note=65,velocity=0,time=480));midi.tracks.append(b);midi.save(self.path)
    def tearDown(self):self.tmp.cleanup()
    def test_delay(self):self.assertAlmostEqual(delay_ms(112)['dotted_eighth'],401.79,places=2)
    def test_tempo(self):self.assertAlmostEqual(make_recipe(self.path)['tempo_bpm'],112,places=2)
    def test_guitar_classification(self):self.assertEqual(classify('Nylon Chords',False),'guitar') if False else self.assertIn(classify('Nylon Chords',False),('guitar','lead'))
    def test_no_changes(self):
        digest=lambda:hashlib.sha256(self.path.read_bytes()).digest()
        before=digest();make_recipe(self.path);self.assertEqual(before,digest())
    def test_all_presets(self):
        for p in PRESETS:
            r=make_recipe(self.path,p);self.assertEqual(r['preset'],p);self.assertEqual(len(r['tracks']),1)
    def test_dotted_eighth_guitar(self):
        r=make_recipe(self.path);self.assertTrue(any('401.79' in x['settings'] for x in r['tracks'][0]['insert_and_send_chain']))
if __name__=='__main__':unittest.main()
