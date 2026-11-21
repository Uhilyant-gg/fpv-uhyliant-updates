import hashlib,json,tempfile,unittest
from unittest.mock import patch
from openipc_firmware_acquisition import OpenIPCFirmwareAcquisition
FIXTURE_URL=''.join(('https://','fixture.invalid','/artifact'))
class Response:
 def __init__(self,data):self.data=data;self.headers={'Content-Length':str(len(data))}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def geturl(self):return FIXTURE_URL
 def read(self,limit):return self.data[:limit]
class Devices:
 def __init__(self):self.items=[{'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335'}}]
class Center:
 def __init__(self):self.devices=Devices();self.calls=[]
 def verifyImage(self,path,sha):self.calls.append((path,sha));return True
class Tests(unittest.TestCase):
 def setUp(self):self.data=b'firmware';self.entry={'platform':'ssc30kq','sensor':'imx335','variant':'lite','channel':'nightly','build':'b1','url':FIXTURE_URL,'sha256':hashlib.sha256(self.data).hexdigest(),'size':len(self.data)}
 def service(self,td,responses=None):return OpenIPCFirmwareAcquisition(Center(),td,opener=lambda *a,**k:(responses or [Response(self.data)]).pop(0))
 def prime(self,s):s._catalog=[dict(self.entry)];s._generation=1;return s.selectForDevice('cam','nightly','b1','lite')
 def test_selection_binds_device_host_and_identity(self):
  with tempfile.TemporaryDirectory() as td:
   s=self.service(td);r=self.prime(s);self.assertTrue(r['ready']);self.assertEqual(r['device'],{'deviceId':'cam','host':'192.168.1.50','platform':'ssc30kq','sensor':'imx335'});self.assertEqual(r['source'],'official-openipc-catalog')
 def test_host_change_makes_selection_stale(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   s=self.service(td);self.prime(s);s.center.devices.items[0]['host']='192.168.1.99';self.assertFalse(s.downloadSelected('cam'));self.assertEqual(s.status['state'],'stale');self.assertEqual(s.center.calls,[])
 def test_identity_change_makes_selection_stale(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   s=self.service(td);self.prime(s);s.center.devices.items[0]['openipcIdentity']['sensor']='imx415';self.assertFalse(s.downloadSelected('cam'));self.assertEqual(s.center.calls,[])
 def test_catalog_generation_change_makes_selection_stale(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   s=self.service(td);self.prime(s);s._generation+=1;self.assertFalse(s.downloadSelected('cam'));self.assertEqual(s.center.calls,[])
 def test_forged_selection_artifact_is_rejected(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   s=self.service(td);self.prime(s);s._status['selection']['artifact']={**self.entry,'build':'evil'};self.assertFalse(s.downloadSelected('cam'));self.assertEqual(s.center.calls,[])
 def test_verified_cache_is_reused_only_after_rehash(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   s=self.service(td);self.prime(s);target=s.cache/('openipc-'+self.entry['sha256'][:16]+'.tgz');s.cache.mkdir();target.write_bytes(self.data);self.assertTrue(s.downloadSelected('cam'));self.assertEqual(len(s.center.calls),1)
if __name__=='__main__':unittest.main()
