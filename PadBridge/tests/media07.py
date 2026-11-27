"""Original SDK-compiled APK → DEX → Android media APIs → real FFmpeg and audio.

Requires a real Pulse/PipeWire server. A monitored null sink makes verification
deterministic; it proves PCM reaches the server, not physical HDMI speakers.
"""
import array,hashlib,json,os,shutil,subprocess,tempfile,time,unittest,ssl,threading,http.server,contextlib
from pathlib import Path
from build_fixtures import ROOT,OUT

class Media07Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='padbridge07-');self.root=Path(self.temp.name)
        self.env={**os.environ,'PADBRIDGE_DATA_HOME':str(self.root),'PADBRIDGE_RUNTIME_DIR':str(ROOT/'build/runtime')}
        self.app=self.call('install',OUT/'media07.apk')['app'];self.data=self.root/'data'/self.app['package'];self.files=self.data/'files';self.files.mkdir()
        shutil.copyfile(OUT/'media07.mp4',self.files/'input.mp4')
        (self.files/'source.txt').write_text('/data/files/input.mp4')
    def tearDown(self):self.temp.cleanup()
    def call(self,*args,ok=True):
        p=subprocess.run([str(ROOT/'target/release/padbridge'),*map(str,args)],env=self.env,capture_output=True,text=True,timeout=150)
        r=json.loads(p.stdout);self.assertEqual(r['ok'],ok,r);return r
    def run_mode(self,mode,duration=500,ok=True):
        (self.files/'mode.txt').write_text(mode);(self.data/'test-duration-ms.txt').write_text(str(duration))
        return self.call('run',self.app['package'],'--headless',ok=ok)
    def test_original_dex_decodes_full_h264_aac_with_pts_and_eos(self):
        r=self.run_mode('decode');self.assertIn('MEDIA_DECODE_OK frames=30',r['output']);self.assertIn('first=0 last=1160000',r['output'])
        source=self.root/'packages'/self.app['package']/self.app['sha256']/'original.apk'
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(),hashlib.sha256((OUT/'media07.apk').read_bytes()).digest())
        for target,args in [('reference.rgba',['-map','0:v:0','-pix_fmt','rgba','-f','rawvideo']),('reference.pcm',['-map','0:a:0','-acodec','pcm_s16le','-f','s16le'])]:
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'media07.mp4'),*args,str(self.files/target)],check=True)
        self.assertEqual((self.files/'decoded.rgba').read_bytes(),(self.files/'reference.rgba').read_bytes())
        # FFmpeg's demuxer can mark encoder priming; compare the actual signal after priming.
        decoded=array.array('h',(self.files/'decoded.pcm').read_bytes());reference=array.array('h',(self.files/'reference.pcm').read_bytes())
        self.assertGreater(len(decoded),50000);self.assertGreater(max(abs(v) for v in decoded),2000)
        self.assertEqual(decoded[-len(reference):],reference)
    def with_capture(self,mode,duration):
        previous=subprocess.check_output(['pactl','get-default-sink'],text=True).strip()
        module=subprocess.check_output(['pactl','load-module','module-null-sink','sink_name=padbridge07_test','rate=48000','channels=2'],text=True).strip()
        capture=None
        try:
            subprocess.run(['pactl','set-default-sink','padbridge07_test'],check=True)
            path=self.root/'capture.pcm'
            with path.open('wb') as output:
                capture=subprocess.Popen(['parec','--device=padbridge07_test.monitor','--latency-msec=20','--format=s16le','--rate=48000','--channels=2'],stdout=output,stderr=subprocess.DEVNULL)
                time.sleep(.25);r=self.run_mode(mode,duration);time.sleep(.2);capture.terminate();capture.wait(timeout=5);capture=None
            pcm=array.array('h',path.read_bytes());self.assertGreater(len(pcm),48000)
            signal=[v for v in pcm[::2] if abs(v)>100]
            self.assertGreater(len(signal),24000);self.assertGreater(max(abs(v) for v in pcm),1000)
            # Count zero crossings in the non-silent 440 Hz tone (allow AAC boundary ringing).
            changes=sum((a<0)!=(b<0) for a,b in zip(signal,signal[1:]));self.assertGreater(changes,850);self.assertLess(changes,1300)
            return r
        finally:
            if capture is not None:capture.terminate();capture.wait(timeout=5)
            subprocess.run(['pactl','set-default-sink',previous],check=True)
            subprocess.run(['pactl','unload-module',module],check=True)
    def test_audio_track_reaches_linux_output_and_pause_freezes_queue(self):
        r=self.with_capture('audio',500);self.assertIn('AUDIO_OUTPUT_OK',r['output'])
    def test_media_player_pause_seek_and_replay_preserve_state(self):
        r=self.run_mode('controls',6500);self.assertIn('PLAYER_PAUSE_FROZEN',r['output']);self.assertIn('PLAYER_SEEK_CONFIRMED',r['output'])
        self.assertEqual(r['output'].count('PLAYER_COMPLETED'),2);self.assertEqual((self.files/'completed.txt').read_text(),'PAUSE_SEEK_REPLAY_COMPLETE')
    def test_media_player_renders_surface_and_plays_sound_to_completion(self):
        r=self.with_capture('player',4000);self.assertIn('PLAYER_COMPLETED',r['output']);self.assertEqual((self.files/'completed.txt').read_text(),'REAL_AV_COMPLETE')
        from PIL import Image
        images=list(self.data.glob('surface-*.png'));self.assertTrue(images)
        with Image.open(images[0]) as im:self.assertEqual(im.size,(160,90));self.assertGreater(len(set(im.getdata())),200)
    def test_media_extractor_rejects_non_media_and_never_reports_playback(self):
        (self.files/'input.mp4').write_bytes(b'not a video');r=self.run_mode('decode',ok=False);self.assertNotIn('MEDIA_DECODE_OK',r.get('output',''))
    def test_webview_executes_original_javascript_with_real_chromium(self):
        app=self.call('install',OUT/'web07.apk')['app'];data=self.root/'data'/app['package']
        (data/'test-duration-ms.txt').write_text('7000')
        r=self.call('run',app['package'],'--headless');self.assertIn('CHROMIUM_DOM_RESULT="ORIGINAL_WEBVIEW_JS:rgb(10, 200, 30)"',r['output'])
        scene=json.loads(r['output'].split('PADBRIDGE_SCENE=')[1].splitlines()[0]);self.assertTrue(any(n['image_bytes']>1000 for n in scene['nodes']))
        from PIL import Image
        with Image.open(next(data.glob('webview-*.png'))) as frame:self.assertEqual(frame.convert('RGB').getpixel((900,500)),(10,200,30))
    @contextlib.contextmanager
    def tls_server(self):
        folder=self.root/'tls';folder.mkdir()
        def openssl(*args):subprocess.run(['openssl',*args],cwd=folder,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        openssl('req','-x509','-newkey','rsa:2048','-nodes','-days','1','-keyout','ca.key','-out','ca.pem','-subj','/CN=PadBridge isolated test CA','-addext','basicConstraints=critical,CA:TRUE')
        openssl('req','-newkey','rsa:2048','-nodes','-keyout','server.key','-out','server.csr','-subj','/CN=localhost')
        (folder/'ext').write_text('subjectAltName=DNS:localhost\nbasicConstraints=CA:FALSE\nextendedKeyUsage=serverAuth\n')
        openssl('x509','-req','-in','server.csr','-CA','ca.pem','-CAkey','ca.key','-CAcreateserial','-days','1','-out','server.pem','-extfile','ext')
        clip=(OUT/'media07.mp4').read_bytes()
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                data=clip if self.path=='/video.mp4' else b'CERT_TRUST_OK'
                self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            def log_message(self,*args):pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(folder/'server.pem',folder/'server.key');server.socket=context.wrap_socket(server.socket,server_side=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:yield folder,f'https://localhost:{server.server_port}'
        finally:server.shutdown();server.server_close();thread.join()
    def test_https_permission_certificate_import_hostname_and_revocation(self):
        with self.tls_server() as (folder,url):
            (self.files/'source.txt').write_text(url)
            self.run_mode('https',ok=False)
            self.call('permissions',self.app['package'],'["android.permission.INTERNET"]')
            self.assertIn('SSLHandshakeException',self.run_mode('https',ok=False)['output'])
            trust=self.call('trust-certificate',self.app['package'],folder/'ca.pem');fingerprint=trust['result']['fingerprint']
            self.assertIn('HTTPS_BODY=CERT_TRUST_OK',self.run_mode('https')['output'])
            (self.files/'source.txt').write_text(url.replace('localhost','127.0.0.1'))
            self.assertIn('SSLHandshakeException',self.run_mode('https',ok=False)['output'])
            self.call('untrust-certificate',self.app['package'],fingerprint)
            self.assertEqual(self.call('certificates',self.app['package'])['trust']['certificates'],[])
            (self.files/'source.txt').write_text(url)
            self.assertIn('SSLHandshakeException',self.run_mode('https',ok=False)['output'])
    def test_https_media_extraction_decoding_uses_verified_app_certificate(self):
        with self.tls_server() as (folder,url):
            self.call('permissions',self.app['package'],'["android.permission.INTERNET"]')
            (self.files/'source.txt').write_text(url+'/video.mp4');self.run_mode('decode',ok=False)
            self.call('trust-certificate',self.app['package'],folder/'ca.pem')
            self.assertIn('MEDIA_DECODE_OK frames=30',self.run_mode('decode')['output'])
            (self.files/'source.txt').write_text(url.replace('localhost','127.0.0.1')+'/video.mp4')
            self.run_mode('decode',ok=False)
    def test_certificate_import_rejects_private_keys_and_invalid_input(self):
        path=self.root/'invalid.pem';path.write_text('-----BEGIN PRIVATE KEY-----\nprivate\n-----END PRIVATE KEY-----')
        self.call('trust-certificate',self.app['package'],path,ok=False)
        self.assertEqual(self.call('certificates',self.app['package'])['trust']['certificates'],[])
    def test_certificate_scope_integrity_and_explicit_data_deletion(self):
        with self.tls_server() as (folder,url):
            self.call('trust-certificate',self.app['package'],folder/'ca.pem')
            peer=self.call('install',OUT/'mediapeer07.apk')['app'];files=self.root/'data'/peer['package']/'files';files.mkdir()
            (files/'source.txt').write_text(url);(files/'mode.txt').write_text('https')
            self.call('permissions',peer['package'],'["android.permission.INTERNET"]')
            self.assertIn('SSLHandshakeException',self.call('run',peer['package'],'--headless',ok=False)['output'])
            trust=self.root/'certificates'/self.app['package'];current=json.loads((trust/'current.json').read_text());metadata=trust/current['generation']/'certificates.json';original=metadata.read_bytes();metadata.write_text('{}')
            self.call('certificates',self.app['package'],ok=False);metadata.write_bytes(original)
            self.call('remove',self.app['package']);self.call('install',OUT/'media07.apk')
            self.assertEqual(len(self.call('certificates',self.app['package'])['trust']['certificates']),1)
            self.call('remove',self.app['package'],'--delete-data');self.assertFalse(trust.exists())

if __name__=='__main__':unittest.main(verbosity=2)
