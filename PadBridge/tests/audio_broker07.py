"""The app-facing protocol cannot select devices, request recording or send paths."""
import socket,struct,subprocess,sys,tempfile,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class AudioBroker07Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'audio.sock'
        self.process=subprocess.Popen([sys.executable,str(ROOT/'runtime/audio_broker.py'),str(self.path)],stderr=subprocess.DEVNULL)
        deadline=time.monotonic()+3
        while not self.path.exists():
            if self.process.poll() is not None or time.monotonic()>deadline:raise AssertionError('Broker did not start')
            time.sleep(.01)
    def tearDown(self):self.process.terminate();self.process.wait(timeout=3);self.temp.cleanup()
    def request(self,op,size=0):
        with socket.socket(socket.AF_UNIX) as conn:
            conn.settimeout(2);conn.connect(str(self.path));conn.sendall(struct.pack('<IIiiI',op,0,0,0,size));data=conn.recv(12)
        self.assertEqual(struct.unpack('<iq',data)[0],-1);self.assertIsNone(self.process.poll())
    def test_unknown_capture_or_device_operations_are_rejected(self):
        for op in [0,7,100,0xffffffff]:self.request(op)
    def test_oversize_audio_is_rejected_before_read_or_allocation(self):self.request(2,4*1024*1024+1)
if __name__=='__main__':unittest.main(verbosity=2)
