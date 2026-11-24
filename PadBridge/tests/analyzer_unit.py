import importlib.util,struct,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('analyzer',Path(__file__).resolve().parents[1]/'runtime/analyze.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class AnalyzerTests(unittest.TestCase):
    def code(self,words):return bytes(12)+struct.pack('<I',len(words))+struct.pack('<'+'H'*len(words),*words)
    def test_modern_opcodes_and_payload_boundaries(self):
        code=self.code([0xfa,0,0,0,0x100,1,0,0,0xff,0,0x0e])
        self.assertEqual(list(a.instructions(code,0)),[(0,250),(4,0),(10,14)])
    def test_truncated_instruction_rejected(self):
        with self.assertRaises(ValueError):list(a.instructions(self.code([0xfa,0]),0))
    def test_malformed_dex_rejected(self):
        for size in range(112):
            with self.assertRaises(ValueError):a.Dex(bytes(size))
    def test_leb_overflow_rejected(self):
        with self.assertRaises(ValueError):a.Reader(b'\xff'*5).leb()
    def test_reserved_instruction_is_not_silently_accepted(self):
        with self.assertRaises(ValueError):list(a.instructions(self.code([0x73]),0))

if __name__=='__main__':unittest.main(verbosity=2)
