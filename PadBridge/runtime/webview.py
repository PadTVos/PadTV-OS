"""Real Chromium renderer inside the app's existing bubblewrap namespace.

DevTools uses inherited pipes, never a remotely reachable debugging port. The
browser keeps its own sandbox enabled. Data and cookies stay in this app's /data.
"""
import base64,json,os,select,subprocess,sys,time

class Chromium:
    def __init__(self, directory):
        parent_read,child_write=os.pipe();child_read,parent_write=os.pipe()
        # Reserve explicit protocol descriptors without publishing a TCP listener.
        def child_setup():
            os.dup2(child_read,3);os.dup2(child_write,4)
        # Reserve 3/4 in the inherited set: they may be pipe source descriptors.
        try:
            self.proc=subprocess.Popen(['/usr/lib/chromium/chromium','--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--remote-debugging-pipe','--user-data-dir='+directory,'about:blank'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=sys.stderr,pass_fds=tuple(set((3,4,child_read,child_write))),preexec_fn=child_setup)
        except Exception:
            os.close(parent_read);os.close(parent_write);raise
        finally:
            os.close(child_read);os.close(child_write)
        self.reader=parent_read;self.writer=parent_write;self.pending=bytearray();self.next_id=1;self.session=None;self.loaded=set()
        try:self.initialize()
        except Exception:self.close();raise
    def initialize(self):
        target=self.call('Target.createTarget',{'url':'about:blank'})['targetId']
        self.session=self.call('Target.attachToTarget',{'targetId':target,'flatten':True})['sessionId']
        self.call('Page.enable');self.call('Page.setLifecycleEventsEnabled',{'enabled':True});self.call('Runtime.enable')
        self.call('Network.enable');self.call('Network.setBlockedURLs',{'urls':['file:*','ftp:*']})
        self.call('Emulation.setDeviceMetricsOverride',{'width':1280,'height':720,'deviceScaleFactor':1,'mobile':False})
        self.javascript=False;self.call('Emulation.setScriptExecutionDisabled',{'value':True})
    def message(self,deadline):
        while b'\0' not in self.pending:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([self.reader],[],[],remaining)[0]:raise TimeoutError('Chromium response timeout')
            data=os.read(self.reader,65536)
            if not data:raise RuntimeError('Chromium exited')
            self.pending.extend(data)
            if len(self.pending)>12*1024*1024:raise ValueError('Chromium response size limit')
        raw,_,tail=self.pending.partition(b'\0');self.pending=bytearray(tail);result=json.loads(raw)
        if result.get('method')=='Page.lifecycleEvent' and result.get('params',{}).get('name')=='load':
            self.loaded.add(result['params']['loaderId'])
        return result
    def call(self,method,params=None):
        ident=self.next_id;self.next_id+=1
        message={'id':ident,'method':method,'params':params or {}}
        if self.session:message['sessionId']=self.session
        data=json.dumps(message).encode()+b'\0'
        while data:n=os.write(self.writer,data);data=data[n:]
        deadline=time.monotonic()+10
        while True:
            result=self.message(deadline)
            if result.get('id')!=ident:continue
            if 'error' in result:raise RuntimeError(result['error'])
            return result.get('result',{})
    def navigate(self,url):
        if not url.startswith(('https://','http://','data:text/html')):raise ValueError('WebView only accepts HTTP(S) or HTML data')
        self.loaded.clear();result=self.call('Page.navigate',{'url':url})
        if 'errorText' in result:raise RuntimeError(result['errorText'])
        # Wait for this navigation's loader, not the previous page's readyState.
        deadline=time.monotonic()+8
        loader=result.get('loaderId')
        if not loader:return # same-document fragment navigation
        while loader not in self.loaded:self.message(deadline)
    def dispatch(self,op,arg):
        if op=='S':self.javascript=arg=='1';self.call('Emulation.setScriptExecutionDisabled',{'value':not self.javascript});return ''
        if op=='L':self.navigate(arg);return ''
        if op=='H':self.navigate('data:text/html;charset=utf-8;base64,'+base64.b64encode(arg.encode()).decode());return ''
        if op=='J':
            if not self.javascript:raise RuntimeError('JavaScript is disabled')
            value=self.call('Runtime.evaluate',{'expression':arg,'returnByValue':True,'awaitPromise':True})
            if 'exceptionDetails' in value:raise RuntimeError(value['exceptionDetails'].get('text','JavaScript exception'))
            return json.dumps(value.get('result',{}).get('value'),ensure_ascii=True)
        if op=='P':return self.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})['data']
        if op=='K':
            code=int(arg);keys={19:('ArrowUp',38),20:('ArrowDown',40),21:('ArrowLeft',37),22:('ArrowRight',39),23:('Enter',13),66:('Enter',13),61:('Tab',9)}
            if code not in keys:raise ValueError('Unsupported WebView key')
            key,windows=keys[code]
            for event in ('keyDown','keyUp'):self.call('Input.dispatchKeyEvent',{'type':event,'key':key,'code':key,'windowsVirtualKeyCode':windows})
            return ''
        raise ValueError('Unsupported WebView command')
    def close(self):
        self.proc.terminate()
        try:self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
        os.close(self.reader);os.close(self.writer)

def main():
    browser=None
    try:
        for line in sys.stdin:
            if len(line)>4*1024*1024:raise ValueError('WebView request size limit')
            try:
                op,encoded=line.strip().split('|',1)
                if op=='Q':break
                if browser is None:browser=Chromium(sys.argv[1])
                result=browser.dispatch(op,base64.b64decode(encoded,validate=True).decode('utf-8'))
                print('OK|'+base64.b64encode(result.encode()).decode(),flush=True)
            except Exception as error:print('ERR|'+base64.b64encode(str(error).encode()).decode(),flush=True)
    finally:
        if browser:browser.close()

if __name__=='__main__':main()
