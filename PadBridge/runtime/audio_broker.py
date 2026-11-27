"""Playback-only broker. Apps never receive the host Pulse/PipeWire socket.

Protocol is bounded little-endian PCM/control messages, with no path, capture,
shell, device-selection or file-descriptor passing operation. SDL talks to the
user's real Linux output server from this separate trusted process.
"""
import ctypes as C
import ctypes.util
import os
import socket
import struct
import sys
import time

class Spec(C.Structure):
    _fields_=[('freq',C.c_int),('format',C.c_uint16),('channels',C.c_uint8),('silence',C.c_uint8),('samples',C.c_uint16),('padding',C.c_uint16),('size',C.c_uint32),('callback',C.c_void_p),('userdata',C.c_void_p)]

def read_exact(conn, count):
    result=bytearray()
    while len(result)<count:
        part=conn.recv(count-len(result))
        if not part: raise ValueError('Truncated audio request')
        result.extend(part)
    return bytes(result)

class Playback:
    def __init__(self):
        self.lib=C.CDLL(ctypes.util.find_library('SDL2') or 'libSDL2-2.0.so.0')
        for name,args,ret in [('SDL_InitSubSystem',[C.c_uint32],C.c_int),('SDL_GetError',[],C.c_char_p),('SDL_OpenAudioDevice',[C.c_char_p,C.c_int,C.POINTER(Spec),C.c_void_p,C.c_int],C.c_uint32),('SDL_CloseAudioDevice',[C.c_uint32],None),('SDL_QueueAudio',[C.c_uint32,C.c_void_p,C.c_uint32],C.c_int),('SDL_GetQueuedAudioSize',[C.c_uint32],C.c_uint32),('SDL_ClearQueuedAudio',[C.c_uint32],None),('SDL_PauseAudioDevice',[C.c_uint32,C.c_int],None)]:
            f=getattr(self.lib,name);f.argtypes=args;f.restype=ret
        # Never accept a dummy audio driver as successful sound output.
        os.environ['SDL_AUDIODRIVER']='pulseaudio'
        os.environ['PULSE_LATENCY_MSEC']='40'
        if self.lib.SDL_InitSubSystem(0x10):raise RuntimeError(self.lib.SDL_GetError())
        self.devices={};self.next_id=1

    def request(self, op, handle, a, b, data):
        if op not in range(1,7):raise ValueError('Unsupported audio operation; playback only')
        if op!=2 and data:raise ValueError('Unexpected payload')
        if op==1:
            if handle!=0 or a<8000 or a>192000 or b not in (1,2) or len(self.devices)>=8:raise ValueError('Invalid PCM format or device limit')
            spec=Spec(freq=a,format=0x8010,channels=b,samples=1024)
            dev=self.lib.SDL_OpenAudioDevice(None,0,C.byref(spec),None,0)
            if not dev:raise RuntimeError(self.lib.SDL_GetError())
            handle=self.next_id;self.next_id+=1;self.devices[handle]=(dev,a*b*2,b)
            return handle
        if handle not in self.devices:raise ValueError('Unknown audio track')
        dev,bps,channels=self.devices[handle]
        if op==2:
            if len(data)%(channels*2):raise ValueError('Unaligned PCM')
            chunk=max(channels*2,(bps//10)//(channels*2)*(channels*2))
            for offset in range(0,len(data),chunk):
                deadline=time.monotonic()+3
                while self.lib.SDL_GetQueuedAudioSize(dev)>bps//5:
                    if time.monotonic()>deadline:raise TimeoutError('Audio output stalled')
                    time.sleep(.002)
                buf=data[offset:offset+chunk]
                if self.lib.SDL_QueueAudio(dev,buf,len(buf)):raise RuntimeError(self.lib.SDL_GetError())
            return len(data)
        if op==3:return self.lib.SDL_GetQueuedAudioSize(dev)*1000000//bps
        if op==4:
            if a not in (0,1):raise ValueError('Invalid drain action')
            if not a:self.lib.SDL_ClearQueuedAudio(dev)
            else:
                deadline=time.monotonic()+3
                while self.lib.SDL_GetQueuedAudioSize(dev):
                    if time.monotonic()>deadline:raise TimeoutError('Audio drain stalled')
                    time.sleep(.002)
        if op==5:
            if a not in (0,1):raise ValueError('Invalid pause action')
            self.lib.SDL_PauseAudioDevice(dev,a)
        if op==6:self.lib.SDL_CloseAudioDevice(dev);del self.devices[handle]
        return 0

def serve(path):
    playback=None
    with socket.socket(socket.AF_UNIX) as server:
        server.bind(path);os.chmod(path,0o600);server.listen(8)
        while True:
            conn,_=server.accept()
            with conn:
                conn.settimeout(6)
                try:
                    op,handle,a,b,size=struct.unpack('<IIiiI',read_exact(conn,20))
                    if size>4*1024*1024 or op not in range(1,7):raise ValueError('Invalid audio request')
                    data=read_exact(conn,size)
                    if playback is None:playback=Playback()
                    result=playback.request(op,handle,a,b,data)
                    conn.sendall(struct.pack('<iq',0,result))
                except Exception as error:
                    print('Audio broker:',str(error)[:300],file=sys.stderr,flush=True)
                    try:conn.sendall(struct.pack('<iq',-1,0))
                    except OSError:pass

if __name__=='__main__':serve(sys.argv[1])
