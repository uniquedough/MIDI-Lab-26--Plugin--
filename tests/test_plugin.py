import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / 'server' / 'mcp_server.py'

spec = importlib.util.spec_from_file_location('midi_lab_mcp', SERVER)
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

class PluginTests(unittest.TestCase):
    def test_manifest(self):
        manifest=json.loads((ROOT/'plugin.json').read_text())
        self.assertEqual(manifest['name'], 'midi-lab')
        self.assertEqual(manifest['version'], '1.0.0')
        self.assertLessEqual(len(manifest['extensions']['com.openai']['interface']['shortDescription']), 30)
        mcp=json.loads((ROOT/'mcp.json').read_text())
        self.assertEqual(mcp['mcpServers']['midi-lab-local']['type'], 'stdio')

    def test_list_profiles(self):
        result=server.handle('list_profiles', {})
        self.assertGreaterEqual(len(result['profiles']), 27)
        self.assertIn('tape_bliss', result['effects'])

    def test_bad_path(self):
        with self.assertRaises(server.ToolError):
            server.input_path('/definitely/not/an/actual/song.mid')

    def test_rpc_protocol(self):
        lines=[json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}}),
               json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'}),
               json.dumps({'jsonrpc':'2.0','id':2,'method':'tools/list'}),
               json.dumps({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'list_profiles','arguments':{}}})]
        p=subprocess.run([sys.executable, str(SERVER)], input='\n'.join(lines)+'\n', text=True, capture_output=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        msgs=[json.loads(s) for s in p.stdout.splitlines()]
        self.assertEqual(len(msgs), 3)
        self.assertEqual(msgs[0]['result']['serverInfo']['name'],'midi-lab')
        self.assertEqual(len(msgs[1]['result']['tools']),5)
        self.assertFalse(msgs[2]['result']['isError'])

    def test_cook_v41_with_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            old=server.OUTPUT
            server.OUTPUT=Path(directory)
            try:
                result=server.handle('cook_midi', {'title':'Test Morning After','engine':'v4.1','bpm':116,
                      'minutes':0.8,'key':'F#','mode':'minor','style':'bliss',
                      'repetition':'microevolution','production_style':'tape_bliss','seed':99})
                self.assertTrue(Path(result['midi_file']).is_file())
                self.assertTrue(Path(result['effects_file']).is_file())
                self.assertEqual(result['audit']['midi_type'],1)
                self.assertEqual(result['audit']['ppq'],480)
                self.assertEqual(result['audit']['forbidden_events'],0)
            finally:
                server.OUTPUT=old

    def test_effects_non_destructive(self):
        from mido import MidiFile
        p=ROOT/'engine/examples/late_train_home.mid'
        before=p.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            old=server.OUTPUT
            server.OUTPUT=Path(td)
            try:
                effects=server.make_effects(p, 'tape_bliss')
                self.assertTrue(Path(effects).is_file())
            finally:
                server.OUTPUT=old
        self.assertEqual(before,p.read_bytes())

if __name__ == '__main__':
    unittest.main()
