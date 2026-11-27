"""Build one app's trust bundle in a no-network sandbox. Never edits system trust."""
import hashlib,json,re,shutil,subprocess,sys
from pathlib import Path

def run(*args):return subprocess.run(args,check=True,capture_output=True,timeout=15).stdout
def build(action,fingerprint):
    out=Path('/output');certs={}
    for path in Path('/existing').glob('*.pem'):
        if path.name=='ca-bundle.pem':continue
        if not re.fullmatch('[0-9a-f]{64}\\.pem',path.name):raise ValueError('Invalid certificate filename')
        certs[path.stem]=path.read_bytes()
    if action=='add':
        data=Path('/input.pem').read_bytes()
        if len(data)>65536 or b'PRIVATE KEY' in data or data.count(b'-----BEGIN CERTIFICATE-----')!=1:raise ValueError('One public PEM certificate required')
        der=run('/usr/bin/openssl','x509','-in','/input.pem','-outform','DER');fingerprint=hashlib.sha256(der).hexdigest()
        certs[fingerprint]=run('/usr/bin/openssl','x509','-in','/input.pem','-outform','PEM')
    elif action=='remove':
        if not re.fullmatch('[0-9a-f]{64}',fingerprint) or fingerprint not in certs:raise ValueError('Unknown certificate fingerprint')
        del certs[fingerprint]
    else:raise ValueError('Invalid trust operation')
    if len(certs)>32:raise ValueError('Per-app certificate limit')
    shutil.copyfile('/etc/ssl/certs/java/cacerts',out/'cacerts')
    bundle=Path('/etc/ssl/certs/ca-certificates.crt').read_bytes();records=[]
    for digest,data in sorted(certs.items()):
        path=out/(digest+'.pem');path.write_bytes(data);bundle+=b'\n'+data
        details=run('/usr/bin/openssl','x509','-in',str(path),'-noout','-subject','-issuer','-dates').decode()
        run('/usr/bin/keytool','-importcert','-noprompt','-alias','padtv-'+digest,'-file',str(path),'-keystore',str(out/'cacerts'),'-storepass','changeit')
        records.append({'sha256':digest,'details':details})
    (out/'ca-bundle.pem').write_bytes(bundle)
    (out/'certificates.json').write_text(json.dumps({'certificates':records,'scope':'this application only','hostname_verification':True}))
    print(json.dumps({'ok':True,'fingerprint':fingerprint,'count':len(records)}))

if __name__=='__main__':build(sys.argv[1],sys.argv[2])
