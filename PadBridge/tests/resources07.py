"""Real Android string-pool and sparse/compact resource-table regressions."""
import importlib.util,struct,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('resources',Path(__file__).resolve().parents[1]/'runtime/resources.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def pool(values):
    data=bytearray();offsets=[]
    for value in values:
        offsets.append(len(data));raw=value if isinstance(value,bytes) else value.encode();data.extend(bytes([len(raw),len(raw)]));data.extend(raw+b'\0')
    head=28;start=head+4*len(values);size=start+len(data)
    return struct.pack('<HHIIIIII',1,head,size,len(values),0,256,start,0)+b''.join(struct.pack('<I',o) for o in offsets)+data

def table(flags,compact=False):
    global_pool=pool(['value']);types=pool(['string']);keys=pool(['title'])
    head=24;start=head+(2 if flags==2 else 4)
    indices=struct.pack('<HH',7,0) if flags==1 else struct.pack('<H',0) if flags==2 else struct.pack('<I',0)
    entry=struct.pack('<HHI',0,8|(3<<8),0) if compact else struct.pack('<HHIHBBI',8,0,0,8,0,3,0)
    body=struct.pack('<HHIBBHIII',0x201,head,start+len(entry),1,flags,0,1,start,4)+indices+entry
    pkg=bytearray(288);struct.pack_into('<HHII',pkg,0,0x200,288,288+len(types)+len(keys)+len(body),0x7f);struct.pack_into('<I',pkg,268,288);struct.pack_into('<I',pkg,276,288+len(types))
    payload=global_pool+pkg+types+keys+body
    return struct.pack('<HHII',2,12,12+len(payload),1)+payload

class Resources07Tests(unittest.TestCase):
    def test_android_cesu8_surrogate_pair_and_modified_nul(self):self.assertEqual(r.strings(pool([b'\xed\xa0\xbd\xed\xb3\xba',b'a\xc0\x80b'])),['📺','a\0b'])
    def test_invalid_utf8_and_unpaired_surrogate_remain_errors(self):
        for raw in [b'\xff',b'\xed\xa0\xbd']:
            with self.assertRaises(UnicodeError):r.strings(pool([raw]))
    def test_sparse_16bit_and_compact_resource_entries(self):
        for flags,compact in [(0,False),(1,False),(2,False),(1,True),(2,True)]:
            with self.subTest(flags=flags,compact=compact):self.assertEqual(r.table(table(flags,compact)),{0x7f010007 if flags==1 else 0x7f010000:('string','title','value')})
    def test_truncated_resources_are_not_accepted(self):
        data=table(1,True)
        for cut in [1,7,12,len(data)-1]:
            with self.assertRaises((ValueError,struct.error,IndexError)):r.table(data[:cut])

if __name__=='__main__':unittest.main(verbosity=2)
