import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from openipc_firmware_acquisition import parse_catalog,resolve,verify_download
class Tests(unittest.TestCase):
 def entry(self,**extra):
  item={'platform':'ssc30kq','sensor':'imx335','variant':'lite','channel':'nightly','build':'b1','url':'https://<scrubbed-url-domain>/firmware/openipc.ssc30kq-lite.tgz','sha256':'a'*64,'size':123};item.update(extra);return item
 def test_catalog_requires_complete_official_metadata(self):
  good=self.entry();bad=[self.entry(url='http://<scrubbed-url-domain>/a.tgz'),self.entry(url='https://<scrubbed-url-domain>/a.tgz'),self.entry(sha256='bad'),self.entry(size=0),self.entry(variant='')]
  def official(url):return url.startswith('https://<scrubbed-url-domain>')
  with patch('openipc_firmware_acquisition._official_url',side_effect=official):self.assertEqual(parse_catalog(json.dumps({'firmwares':[good]+bad})),[good])
 def test_unknown_manifest_shape_fails_closed(self):self.assertEqual(parse_catalog(json.dumps({'unexpected':[self.entry()]})),[])
 def test_variant_is_never_inferred(self):
  catalog=[self.entry(variant='lite'),self.entry(variant='ultimate',url='https://<scrubbed-url-domain>/firmware/u.tgz')];r=resolve(catalog,'ssc30kq','imx335','nightly','b1');self.assertFalse(r['ready']);self.assertEqual(r['variants'],['lite','ultimate'])
 def test_build_is_never_guessed(self):
  catalog=[self.entry(build='b1'),self.entry(build='b2',url='https://<scrubbed-url-domain>/firmware/b2.tgz')];r=resolve(catalog,'ssc30kq','imx335','nightly',variant='lite');self.assertFalse(r['ready']);self.assertEqual(r['builds'],['b1','b2'])
 def test_exact_hardware_variant_channel_build_resolves(self):
  item=self.entry();r=resolve([item],'SSC30KQ','IMX335','nightly','b1','lite');self.assertTrue(r['ready']);self.assertEqual(r['artifact'],item)
 def test_download_requires_exact_size_and_sha256(self):
  data=b'firmware';sha=hashlib.sha256(data).hexdigest();artifact={'sha256':sha,'size':len(data)}
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'fw.tgz';p.write_bytes(data);self.assertTrue(verify_download(p,artifact));p.write_bytes(data+b'x');self.assertFalse(verify_download(p,artifact))
if __name__=='__main__':unittest.main()
