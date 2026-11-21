from pathlib import Path
import unittest
class Tests(unittest.TestCase):
 def setUp(self):self.qml=(Path(__file__).parent/'FirmwareCenter.qml').read_text(encoding='utf-8');self.center=(Path(__file__).parent/'firmware_center.py').read_text(encoding='utf-8')
 def test_ui_wires_official_acquisition_to_center(self):
  for token in ('firmwareAcquisition.refresh()','firmwareAcquisition.select(','firmwareAcquisition.download(','firmwareCenter.artifact.verified'):
   self.assertIn(token,self.qml)
 def test_variant_and_build_are_explicit_catalog_controls(self):
  self.assertIn('id:variantBox',self.qml);self.assertIn('id:buildBox',self.qml);self.assertIn('Варіант вибирається явно',self.qml);self.assertIn('Збірка вибирається явно',self.qml)
 def test_acquisition_uses_observed_device_identity(self):
  self.assertIn('firmwareCenter.acquisitionIdentity(deviceBox.currentValue',self.qml);self.assertIn('def acquisitionIdentity',self.center);self.assertIn('identity.get("verified") is True',self.center)
 def test_busy_executor_blocks_catalog_mutations(self):
  self.assertIn('enabled:!firmwareExecutor.busy',self.qml);self.assertIn('!firmwareExecutor.busy;onClicked:firmwareAcquisition.download',self.qml)
if __name__=='__main__':unittest.main()
