import unittest,tempfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from midilab41 import patch,build_layers,ROLES,get_track_name
from midilab4 import ComposerV4,exact_loop_test
from mido import MidiFile

class PatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name)
        comp=ComposerV4(bpm=120,minutes=1,key='F#',mode='minor',seed=11).compose()
        cls.base,_=comp.write_v4(cls.folder/'base.mid')
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_modes_and_locks(self):
        for style in ('minimal','bliss','fracture','hybrid'):
            result=patch(self.base,self.folder/f'{style}.mid',style=style)
            self.assertTrue(result['technical_pass']);self.assertTrue(all(result['anchors_preserved'].values()))
    def test_replace_drums(self):
        result=patch(self.base,self.folder/'replace.mid',style='fracture',drum_mode='replace')
        names=[get_track_name(x) for x in MidiFile(result['midi']).tracks]
        self.assertIn('Fracture Drums',names);self.assertNotIn('Loop Drums',names)
        self.assertTrue(result['anchors_preserved']['Immutable Pulse'])
    def test_determinism(self):
        a=patch(self.base,self.folder/'a.mid',seed=27)
        b=patch(self.base,self.folder/'b.mid',seed=27)
        self.assertEqual(Path(a['midi']).read_bytes(),Path(b['midi']).read_bytes())
    def test_idempotence(self):
        first=patch(self.base,self.folder/'first.mid')
        again=patch(first['midi'],self.folder/'again.mid')
        self.assertEqual(Path(first['midi']).read_bytes(),Path(again['midi']).read_bytes())
    def test_no_forbidden_messages(self):
        a=patch(self.base,self.folder/'forbidden.mid',style='fracture',drum_mode='replace')
        for tr in MidiFile(a['midi']).tracks:
            for m in tr:
                self.assertNotEqual(m.type,'program_change')
                if m.type=='control_change':self.assertNotIn(m.control,(0,32))
    def test_distinct_complexity(self):
        a=build_layers(32,'F#','minor','bliss',.8,.8,41,'keep')
        b=build_layers(32,'F#','minor','fracture',.8,.8,41,'keep')
        self.assertGreater(sum(map(len,b.values())),sum(map(len,a.values())))
        self.assertTrue(b['Altered Harmony'])
if __name__=='__main__':unittest.main()
