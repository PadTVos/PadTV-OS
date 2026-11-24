"""Bounded static DEX / JVM signature analysis. Does not execute APK code.

DEX format: https://source.android.com/docs/core/runtime/dex-format
Instructions: https://source.android.com/docs/core/runtime/dalvik-bytecode
References are potential requirements, never proof that a path executes.
"""
import json
import struct
import sys
import zipfile
from pathlib import Path


class Reader:
    def __init__(self, data, pos=0, endian='<'):
        self.data, self.pos, self.endian = data, pos, endian

    def take(self, size):
        if size < 0 or self.pos < 0 or self.pos + size > len(self.data):
            raise ValueError('Truncated or oversized binary structure')
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def u1(self): return self.take(1)[0]
    def u2(self): return struct.unpack(self.endian+'H', self.take(2))[0]
    def u4(self): return struct.unpack(self.endian+'I', self.take(4))[0]

    def leb(self):
        value = 0
        for shift in range(0, 35, 7):
            b = self.u1()
            value |= (b & 127) << shift
            if b < 128:
                if value > 0xffffffff: raise ValueError('ULEB128 overflow')
                return value
        raise ValueError('Invalid ULEB128')


def class_info(data):
    r = Reader(data, endian='>')
    if r.u4() != 0xcafebabe: raise ValueError('Invalid JVM class')
    r.take(4)
    pool = [None] * r.u2()
    i = 1
    while i < len(pool):
        tag = r.u1()
        if tag == 1: pool[i] = r.take(r.u2()).decode('utf-8', 'replace')
        elif tag in (7, 8, 16, 19, 20): pool[i] = r.u2()
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18): r.take(4)
        elif tag in (5, 6): r.take(8); i += 1
        elif tag == 15: r.take(3)
        else: raise ValueError('Unknown constant pool tag')
        i += 1
    r.u2()
    name = pool[pool[r.u2()]]
    parent = r.u2()
    parents = [pool[pool[parent]]] if parent else []
    parents += [pool[pool[r.u2()]] for _ in range(r.u2())]
    def attrs():
        for _ in range(r.u2()): r.u2(); r.take(r.u4())
    for _ in range(r.u2()): r.take(6); attrs()
    methods = set()
    for _ in range(r.u2()):
        r.u2(); method, desc = pool[r.u2()], pool[r.u2()]
        methods.add(method+desc); attrs()
    return name, {'parents': parents, 'methods': methods}


WIDTH = [0]*256
for op in [0,1,4,7,*range(10,19),29,30,33,39,40,*range(123,144),*range(176,208)]: WIDTH[op]=1
for op in [2,5,8,19,21,22,25,26,28,31,32,34,35,41,*range(45,62),*range(68,110),*range(144,176),*range(208,227),254,255]: WIDTH[op]=2
for op in [3,6,9,20,23,27,36,37,38,42,43,44,*range(110,115),*range(116,121),252,253]: WIDTH[op]=3
WIDTH[24]=5
WIDTH[250]=WIDTH[251]=4
MODERN={250:'invoke-polymorphic',251:'invoke-polymorphic/range',252:'invoke-custom',253:'invoke-custom/range',254:'const-method-handle',255:'const-method-type'}


def instructions(data, offset):
    r = Reader(data, offset)
    r.take(12); count = r.u4()
    if count > 32*1024*1024: raise ValueError('Code item exceeds limit')
    words = r.take(count*2)
    at=0
    while at < count:
        word=struct.unpack_from('<H',words,at*2)[0]; op=word&255
        size=WIDTH[op]
        if op == 0 and word:
            p=Reader(words,at*2+2)
            if word == 0x100: size=4+2*p.u2()
            elif word == 0x200: size=2+4*p.u2()
            elif word == 0x300:
                width=p.u2(); length=p.u4(); size=4+(width*length+1)//2
            else: raise ValueError('Unknown instruction payload')
        if not size: raise ValueError('Reserved DEX opcode 0x%02x at code unit %d'%(op,at))
        if at+size > count: raise ValueError('Truncated DEX instruction')
        yield at, op
        at+=size


class Dex:
    def __init__(self,data):
        self.data=data
        if len(data)<112 or data[:4]!=b'dex\n' or data[4:8] not in [v+b'\0' for v in [b'035',b'037',b'038',b'039',b'040']]:
            raise ValueError('Unsupported DEX header; container 041 is unavailable')
        if self.u4(32)!=len(data) or self.u4(36)!=112 or self.u4(40)!=0x12345678: raise ValueError('Invalid DEX header')
        self.strings=[]
        for r in self.table(56,4,1_000_000):
            s=Reader(data,r.u4());s.leb();end=data.find(b'\0',s.pos,min(len(data),s.pos+1048576))
            if end<0: raise ValueError('Unterminated DEX string')
            self.strings.append(data[s.pos:end].decode('utf-8','replace'))
        self.types=[self.strings[r.u4()] for r in self.table(64,4,65536)]
        self.protos=[]
        for r in self.table(72,12,65536):
            r.u4(); result=self.types[r.u4()]; offset=r.u4()
            self.protos.append('('+''.join(self.type_list(offset))+')'+result)
        self.methods=[]
        for r in self.table(88,8,65536):
            cls,proto,name=r.u2(),r.u2(),r.u4()
            self.methods.append((self.types[cls][1:-1], self.strings[name]+self.protos[proto]))
        self.classes={}; self.unsupported=[]; self.code_errors=[]
        for r in self.table(96,32,65536):
            cls=self.types[r.u4()][1:-1];r.u4();superidx=r.u4();interfaces=r.u4();r.take(8);off=r.u4();r.u4()
            parents=([self.types[superidx][1:-1]] if superidx!=0xffffffff else [])+[s[1:-1] for s in self.type_list(interfaces)]
            methods=set()
            if off:
                c=Reader(data,off);sf,inf,dm,vm=[c.leb() for _ in range(4)]
                if sf+inf+dm+vm>200000: raise ValueError('Class data limit')
                for _ in range(sf+inf):c.leb();c.leb()
                for count in (dm,vm):
                    idx=0
                    for _ in range(count):
                        idx+=c.leb();c.leb();code=c.leb();owner,method=self.methods[idx];methods.add(method)
                        if code:
                            try:
                                for at,op in instructions(data,code):
                                    if op in MODERN:self.unsupported.append({'method':owner+'.'+method,'code_unit':at,'opcode':hex(op),'name':MODERN[op]})
                            except (ValueError,IndexError) as e:self.code_errors.append({'method':owner+'.'+method,'error':str(e)})
            self.classes[cls]={'parents':parents,'methods':methods}

    def u4(self,offset):return Reader(self.data,offset).u4()
    def table(self,header,width,limit):
        n,off=self.u4(header),self.u4(header+4)
        if n>limit or off+n*width>len(self.data):raise ValueError('Invalid DEX table')
        return [Reader(self.data,off+i*width) for i in range(n)]
    def type_list(self,offset):
        if not offset:return []
        r=Reader(self.data,offset);n=r.u4()
        if n>65536:raise ValueError('Type list limit')
        return [self.types[r.u2()] for _ in range(n)]


def analyze(paths,framework):
    base_api=Path(framework).with_name('host-api.json')
    registry=json.loads(base_api.read_text()) if base_api.exists() else {}
    defined={}; dexes=[]; errors=[]
    with zipfile.ZipFile(framework) as z:
        for name in z.namelist():
            if name.endswith('.class'):
                key,value=class_info(z.read(name));registry[key]=value
    for path in paths:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.endswith('.dex') and '/' not in name:
                    try:
                        if z.getinfo(name).file_size>64*1024**2:raise ValueError('DEX exceeds 64 MiB analysis limit')
                        dex=Dex(z.read(name));dexes.append((Path(path).name+':'+name,dex));defined.update(dex.classes)
                    except (ValueError,IndexError,struct.error) as e:errors.append({'dex':name,'error':str(e)})
    combined={**registry,**defined}
    def has_method(cls,signature,visited=None):
        visited=set() if visited is None else visited
        if cls in visited or cls not in combined:return False
        visited.add(cls);info=combined[cls]
        return signature in info['methods'] or (not signature.startswith('<init>') and any(has_method(p,signature,visited) for p in info['parents']))
    missing=set(); methods=set(); opcodes=[]; gms=set();drm=set()
    for origin,dex in dexes:
        for desc in dex.types:
            cls=desc.lstrip('[').removeprefix('L').removesuffix(';')
            if cls.startswith('com/google/android/gms/'):gms.add(cls)
            if cls.startswith(('android/media/MediaDrm','android/media/MediaCrypto')) or 'widevine' in cls.lower():drm.add(cls)
            if cls.startswith(('android/','androidx/','com/google/android/gms/')) and cls not in combined:missing.add(cls)
        for cls,signature in dex.methods:
            if cls in combined and not has_method(cls,signature):methods.add(cls+'.'+signature)
        opcodes.extend(dict(item,dex=origin) for item in dex.unsupported)
        errors.extend(dict(item,dex=origin) for item in dex.code_errors)
    return {'assessment':'Static references only, including bundled dormant libraries. Reflection/dynamic loading and behavioral equivalence are not proven. Missing signatures are checked against implemented host classes; absent-class methods are covered by missing_classes.',
        'missing_classes':sorted(missing),'missing_methods':sorted(methods),'unsupported_instructions':opcodes,
        'analysis_errors':errors,'google_play_services_references':sorted(gms),'drm_references':sorted(drm),
        'defined_classes':len(defined),'dex_files':len(dexes)}


if __name__=='__main__':
    import resource
    resource.setrlimit(resource.RLIMIT_AS,(1536*1024**2,1536*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(80,85))
    try:print(json.dumps({'ok':True,**analyze(sys.argv[1:],Path(__file__).with_name('framework.jar'))}))
    except Exception as error:
        print(json.dumps({'ok':False,'error':str(error)}));sys.exit(1)
