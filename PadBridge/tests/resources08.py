"""Resource map boundary checks and preservation of original binary value types."""
import base64,struct,unittest
from resources07 import pool,r,table

def bag(count=2,duplicate=False):
    global_pool=pool(['false']);types=pool(['style']);keys=pool(['Original'])
    maps=struct.pack('<IHBBI',0x7f020001,8,0,3,0)+struct.pack('<IHBBI',0x7f020001 if duplicate else 0x7f020002,8,0,2,0x7f020003)
    entry=struct.pack('<HHIII',16,1,0,0x01030005,count)+maps
    body=struct.pack('<HHIBBHIII',0x201,24,28+len(entry),1,0,0,1,28,4)+struct.pack('<I',0)+entry
    pkg=bytearray(288);struct.pack_into('<HHII',pkg,0,0x200,288,288+len(types)+len(keys)+len(body),0x7f);struct.pack_into('<I',pkg,268,288);struct.pack_into('<I',pkg,276,288+len(types))
    payload=global_pool+pkg+types+keys+body
    return struct.pack('<HHII',2,12,12+len(payload),1)+payload

class Resources08Tests(unittest.TestCase):
    def test_style_parent_and_attribute_reference_survive_binary_decoding(self):
        value=r.table(bag(),typed=True)[0x7f010000][2].split('|')
        self.assertEqual(value[:2],['!bag',str(0x01030005)])
        entries={int(item.split(',')[0]):base64.b64decode(item.split(',')[1]).decode() for item in value[2:]}
        self.assertEqual(entries[0x7f020001],'!typed|3|0|ZmFsc2U=')
        self.assertEqual(entries[0x7f020002].split('|')[:3],['!typed','2',str(0x7f020003)])
    def test_truncated_oversized_and_duplicate_style_maps_are_rejected(self):
        for data in [bag(3),bag(16385),bag(2,True)]:
            with self.subTest(size=len(data)),self.assertRaises(ValueError):r.table(data,typed=True)
    def test_original_string_type_is_preserved_for_compact_and_normal_entries(self):
        for compact in [False,True]:
            entry=r.table(table(1,compact),typed=True)[0x7f010007]
            self.assertEqual(entry,('string','title','!typed|3|0|dmFsdWU='))

if __name__=='__main__':unittest.main(verbosity=2)
