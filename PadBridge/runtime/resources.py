"""Bounded Android binary XML / basic resource table decoder.

Format: AOSP frameworks/base/libs/androidfw/include/androidfw/ResourceTypes.h.
Independent implementation. Complex bags/styles remain explicit unsupported data.
"""
import base64
import struct
import xml.etree.ElementTree as ET

def u16(b,p): return struct.unpack_from('<H',b,p)[0]
def u32(b,p): return struct.unpack_from('<I',b,p)[0]
def chunks(b,start=0,end=None):
    end=len(b) if end is None else end
    while start<end:
        if start+8>end: raise ValueError('Truncated Android resource chunk')
        kind,head,size=struct.unpack_from('<HHI',b,start)
        if head<8 or size<head or start+size>end: raise ValueError('Invalid Android resource chunk')
        yield kind,head,b[start:start+size]
        start+=size

def strings(b):
    count=u32(b,8); flags=u32(b,16);start=u32(b,20);head=u16(b,2)
    if count>200000 or head+count*4>len(b): raise ValueError('Resource string pool exceeds bounds')
    def length(p,utf8):
        v=b[p] if utf8 else u16(b,p);p+=1 if utf8 else 2
        mask=0x80 if utf8 else 0x8000
        if v&mask:
            v=((v&~mask)<<(8 if utf8 else 16))+(b[p] if utf8 else u16(b,p));p+=1 if utf8 else 2
        return v,p
    result=[]
    for i in range(count):
        p=start+u32(b,head+i*4);utf8=bool(flags&256)
        size,p=length(p,utf8)
        if utf8:size,p=length(p,True)
        else:size*=2
        if size>1024*1024 or p+size>len(b): raise ValueError('Resource string exceeds bounds')
        raw=b[p:p+size]
        if utf8:
            # Android string pools can contain CESU-8 surrogate pairs and MUTF-8 NUL.
            # Combine valid pairs, retaining strict rejection of malformed strings.
            text=raw.replace(b'\xc0\x80',b'\x00').decode('utf-8',errors='surrogatepass')
            text=text.encode('utf-16le',errors='surrogatepass').decode('utf-16le')
        else:text=raw.decode('utf-16le')
        result.append(text)
    return result

def value(kind,data,pool):
    if kind==3:return pool[data]
    if kind in (1,2):return '@0x%08x'%data
    if kind==0x12:return 'true' if data else 'false'
    if 0x1c<=kind<=0x1f:return '#%08x'%data
    if kind==5:
        mantissa=(data&0xffffff00);mantissa=mantissa if mantissa<2**31 else mantissa-2**32
        return str(mantissa*[1/256,1/32768,1/8388608,1/2147483648][(data>>4)&3])+['px','dp','sp','pt','in','mm','?','?'][data&7]
    if kind in (0x10,0x11):return str(data if data<2**31 else data-2**32)
    if kind==0:return ''
    return '!unsupported-value-type:%s'%kind

def xml(data):
    if len(data)>8*1024*1024:raise ValueError('XML exceeds bounds')
    if data.lstrip().startswith(b'<'):return data
    pool=[];stack=[];root=None;nodes=0
    for kind,head,b in chunks(data,8):
        if kind==1:pool=strings(b)
        elif kind==0x102:
            tag=pool[u32(b,20)];node=ET.Element(tag);nodes+=1
            if nodes>20000 or len(stack)>64:raise ValueError('XML complexity exceeds bounds')
            start=16+u16(b,24);size=u16(b,26);count=u16(b,28)
            if size<20 or start+size*count>len(b):raise ValueError('Invalid XML attributes')
            for i in range(count):
                p=start+i*size;name=pool[u32(b,p+4)];raw=u32(b,p+8)
                node.set(name,pool[raw] if raw!=0xffffffff else value(b[p+15],u32(b,p+16),pool))
            if stack:stack[-1].append(node)
            else:root=node
            stack.append(node)
        elif kind==0x103:
            if not stack:raise ValueError('Unbalanced XML')
            stack.pop()
    if root is None or stack:raise ValueError('Incomplete XML')
    return ET.tostring(root,encoding='utf-8')

def table(data):
    if len(data)<12 or u16(data,0)!=2 or u16(data,2)!=12 or u32(data,4)!=len(data):raise ValueError('Invalid Android resource table header')
    global_pool=[];result={}
    for kind,head,b in chunks(data,12):
        if kind==1:global_pool=strings(b)
        if kind!=0x200:continue
        package=u32(b,8);type_offset=u32(b,268);key_offset=u32(b,276)
        types=strings(b[type_offset:]);keys=strings(b[key_offset:])
        for ck,ch,c in chunks(b,head):
            if ck!=0x201:continue
            typ=c[8];flags=c[9];count=u32(c,12);start=u32(c,16)
            if flags&~3 or flags==3:raise ValueError('Unsupported resource index flags')
            stride=2 if flags&2 else 4
            if count>200000 or ch+count*stride>len(c):raise ValueError('Invalid resource entries')
            config_size=u32(c,20)
            default=not any(c[24:20+config_size])
            for i in range(count):
                if flags&1:index=u16(c,ch+i*4);off=u16(c,ch+i*4+2)*4
                elif flags&2:
                    index=i;off=u16(c,ch+i*2)
                    if off==0xffff:continue
                    off*=4
                else:
                    index=i;off=u32(c,ch+i*4)
                    if off==0xffffffff:continue
                p=start+off;size=u16(c,p);entry_flags=u16(c,p+2);key=u32(c,p+4)
                rid=(package<<24)|((typ+(u32(b,284) if head>=288 else 0))<<16)|index
                if rid in result and not default:continue
                if entry_flags&8:key=size;val=value(entry_flags>>8,u32(c,p+4),global_pool)
                else:val='!unsupported-complex-resource' if entry_flags&1 else value(c[p+size+3],u32(c,p+size+4),global_pool)
                result[rid]=(types[typ-1],keys[key],val)
    return result

def write(sources,output):
    resources={};seen=set()
    for source in sources:
        if 'resources.arsc' in source.namelist():
            for key,val in table(source.read('resources.arsc')).items():
                # Base wins for configuration splits; dynamic feature IDs can add entries.
                resources.setdefault(key,val)
        for name in source.namelist():
            if name=='AndroidManifest.xml' or (name.startswith('res/') and name.endswith('.xml')):
                dest='padbridge/xml/'+name
                if dest not in seen:
                    try:output.writestr(dest,xml(source.read(name)))
                    except (ValueError,IndexError,struct.error) as error:
                        output.writestr(dest+'.unsupported',str(error))
                    seen.add(dest)
    rows=[]
    for key,items in sorted(resources.items()):
        rows.append(str(key)+'\t'+'\t'.join(base64.b64encode(s.encode()).decode() for s in items))
    output.writestr('padbridge/resources.tsv','\n'.join(rows))
