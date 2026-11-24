import hashlib, io, json, tempfile, unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from padtv_store.catalog import load, validate
from padtv_store.github import GitHubProvider, allowed, ReleaseRedirect

class Response(io.BytesIO):
    def geturl(self):return 'https://release-assets.githubusercontent.com/test.apk'
class Opener:
    def __init__(self,data):self.data=data
    def open(self,*args,**kwargs):return Response(self.data)

class GitHubStoreTests(unittest.TestCase):
    def setUp(self):
        self.base=next(p for p in load() if p.id=='padbridge-runtime-probe')
        self.product=replace(self.base,download_size=3,sha256=hashlib.sha256(b'apk').hexdigest())
    def test_bounded_download_hash_and_final_host(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'file.apk';GitHubProvider(Opener(b'apk')).download(self.product,target)
            self.assertEqual(target.read_bytes(),b'apk')
    def test_wrong_hash_size_truncation_rejected(self):
        for body in (b'bad',b'a',b'apk-more'):
            with self.subTest(body=body),tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(ValueError):GitHubProvider(Opener(body)).download(self.product,Path(folder)/'x.apk')
    def test_redirect_and_source_restrictions(self):
        for url in ('http://github.com/file','https://github.com.evil.test/a','https://user@github.com/a','https://github.com:8443/a','file:///etc/passwd','https://127.0.0.1/a'):
            with self.subTest(url=url),self.assertRaises(ValueError):allowed(url)
        with self.assertRaises(ValueError):validate(replace(self.product,download_url='https://github.com/owner/repo/raw/main/a.apk'))
    def test_verified_signature_precedes_install(self):
        provider=GitHubProvider(Opener(b'apk'))
        with patch.object(provider,'call',return_value={'app':{'package':self.product.target,'sha256':self.product.sha256,'signers':['wrong']}}) as call:
            with self.assertRaises(ValueError):provider.install(self.product)
            self.assertEqual(call.call_args.args[0],'inspect');self.assertEqual(call.call_count,1)
    def test_install_requires_inventory_confirmation(self):
        provider=GitHubProvider(Opener(b'apk'))
        app={'package':self.product.target,'sha256':self.product.sha256,'signers':[self.product.signer_sha256]}
        with patch.object(provider,'call',side_effect=[{'app':app},{'app':app},{'apps':[]}]):
            with self.assertRaises(RuntimeError):provider.install(self.product)
    def test_uninstall_retains_private_data(self):
        provider=GitHubProvider()
        with patch.object(provider,'call',side_effect=[{}, {'apps':[]}]) as call:
            provider.remove(self.product);self.assertEqual(call.call_args_list[0].args,('remove',self.product.target))

if __name__=='__main__':unittest.main()
