import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from openipc_firmware_acquisition import OpenIPCFirmwareAcquisition
FIXTURE_URL=''.join(('https://','fixture.invalid','/artifact'))
class Response:
 def __init__(self,data,url=FIXTURE_URL):self.data=data;self.url=url;self.headers={'Content-Length':str(len(data))}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def geturl(self):return self.url
 def read(self,limit):return self.data[:limit]
class Devices:
 def __init__(self):self.items=[{'id':'cam','host':'192.168.1.50','openipcIdentity':{'verified':True,'platform':'ssc30kq','sensor':'imx335'}}]
class Center:
 def __init__(self):self.devices=Devices();self.calls=[];self.accept=True
 def verifyImage(self,path,sha):self.calls.append((path,sha));return self.accept
class Tests(unittest.TestCase):
 def entry(self,data):return {'platform':'ssc30kq','sensor':'imx335','variant':'lite','channel':'nightly','build':'b1','url':FIXTURE_URL,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}
 def selected_service(self,td,data,opener):
  center=Center();service=OpenIPCFirmwareAcquisition(center,td,opener=opener);service._catalog=[self.entry(data)];service._generation=1;self.assertTrue(service.selectForDevice('cam','nightly','b1','lite')['ready']);return service,center
 def test_refresh_select_download_and_center_handoff(self):
  data=b'firmware';entry=self.entry(data);responses=[Response(json.dumps({'firmwares':[entry]}).encode()),Response(data)]
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   center=Center();service=OpenIPCFirmwareAcquisition(center,td,opener=lambda *a,**k:responses.pop(0));self.assertTrue(service.refresh());selected=service.selectForDevice('cam','nightly','b1','lite');self.assertTrue(selected['ready']);self.assertTrue(service.downloadSelected('cam'));self.assertEqual(service.status['state'],'verified');self.assertTrue(Path(service.status['selection']['path']).is_file());self.assertEqual(len(center.calls),1)
 def test_redirect_outside_policy_is_rejected(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=False):
   service=OpenIPCFirmwareAcquisition(Center(),td,opener=lambda *a,**k:Response(b'{}'));self.assertFalse(service.refresh());self.assertEqual(service.status['state'],'error')
 def test_bad_download_never_reaches_center(self):
  data=b'firmware'
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   service,center=self.selected_service(td,data,lambda *a,**k:Response(b'wrong'));self.assertFalse(service.downloadSelected('cam'));self.assertEqual(center.calls,[]);self.assertEqual(list(Path(td).glob('*.part')),[])
 def test_corrupt_cache_is_discarded_and_replaced_only_by_verified_download(self):
  data=b'firmware';calls=[]
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   def opener(*a,**k):calls.append(1);return Response(data)
   service,center=self.selected_service(td,data,opener);target=Path(td)/('openipc-'+hashlib.sha256(data).hexdigest()[:16]+'.tgz');target.write_bytes(b'corrupt');self.assertTrue(service.downloadSelected('cam'));self.assertEqual(target.read_bytes(),data);self.assertEqual(calls,[1]);self.assertEqual(len(center.calls),1);self.assertEqual(list(Path(td).glob('*.part')),[])
 def test_center_rejection_remains_fail_closed(self):
  data=b'firmware'
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   service,center=self.selected_service(td,data,lambda *a,**k:Response(data));center.accept=False;self.assertFalse(service.downloadSelected('cam'));self.assertEqual(service.status['state'],'error')
 def test_cache_directory_failure_is_reported_without_network_or_center_handoff(self):
  data=b'firmware'
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   cache=Path(td)/'cache';cache.write_bytes(b'not-a-directory');calls=[];service,center=self.selected_service(cache,data,lambda *a,**k:calls.append(1));self.assertFalse(service.downloadSelected('cam'));self.assertEqual(service.status['state'],'error');self.assertIn('кеш прошивки',service.status['reason']);self.assertEqual(calls,[]);self.assertEqual(center.calls,[])
 def test_temp_file_failure_is_reported_without_network_or_center_handoff(self):
  data=b'firmware'
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True),patch('openipc_firmware_acquisition.tempfile.mkstemp',side_effect=OSError('denied')):
   calls=[];service,center=self.selected_service(td,data,lambda *a,**k:calls.append(1));self.assertFalse(service.downloadSelected('cam'));self.assertEqual(service.status['state'],'error');self.assertIn('тимчасовий файл',service.status['reason']);self.assertEqual(calls,[]);self.assertEqual(center.calls,[])
if __name__=='__main__':unittest.main()
