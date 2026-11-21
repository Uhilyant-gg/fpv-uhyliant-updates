import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from openipc_firmware_acquisition import OpenIPCFirmwareAcquisition
class Response:
 def __init__(self,data,url='fixture-response'):self.data=data;self.url=url;self.headers={'Content-Length':str(len(data))}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def geturl(self):return self.url
 def read(self,limit):return self.data[:limit]
class Center:
 def __init__(self):self.calls=[];self.accept=True
 def verifyImage(self,path,sha):self.calls.append((path,sha));return self.accept
class Tests(unittest.TestCase):
 def entry(self,data):return {'platform':'ssc30kq','sensor':'imx335','variant':'lite','channel':'nightly','build':'b1','url':'fixture-artifact','sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}
 def test_refresh_select_download_and_center_handoff(self):
  data=b'firmware';entry=self.entry(data);responses=[Response(json.dumps({'firmwares':[entry]}).encode()),Response(data)]
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   service=OpenIPCFirmwareAcquisition(Center(),td,opener=lambda *a,**k:responses.pop(0));self.assertTrue(service.refresh());selected=service.select('ssc30kq','imx335','nightly','b1','lite');self.assertTrue(selected['ready']);self.assertTrue(service.download(selected['artifact']));self.assertEqual(service.status['state'],'verified');self.assertTrue(Path(service.status['selection']['path']).is_file());self.assertEqual(len(service.center.calls),1)
 def test_redirect_outside_policy_is_rejected(self):
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=False):
   service=OpenIPCFirmwareAcquisition(Center(),td,opener=lambda *a,**k:Response(b'{}','outside'));self.assertFalse(service.refresh());self.assertEqual(service.status['state'],'error')
 def test_bad_download_never_reaches_center(self):
  data=b'firmware';entry=self.entry(data)
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   center=Center();service=OpenIPCFirmwareAcquisition(center,td,opener=lambda *a,**k:Response(b'wrong'));self.assertFalse(service.download(entry));self.assertEqual(center.calls,[]);self.assertEqual(list(Path(td).glob('*.part')),[])
 def test_center_rejection_remains_fail_closed(self):
  data=b'firmware';entry=self.entry(data)
  with tempfile.TemporaryDirectory() as td,patch('openipc_firmware_acquisition._official_url',return_value=True):
   center=Center();center.accept=False;service=OpenIPCFirmwareAcquisition(center,td,opener=lambda *a,**k:Response(data));self.assertFalse(service.download(entry));self.assertEqual(service.status['state'],'error')
if __name__=='__main__':unittest.main()
