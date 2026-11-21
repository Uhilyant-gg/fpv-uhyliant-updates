from pathlib import Path
import re
import unittest
class Tests(unittest.TestCase):
 def setUp(self):self.qml=(Path(__file__).parent/'FirmwareCenter.qml').read_text(encoding='utf-8');self.center=(Path(__file__).parent/'firmware_center.py').read_text(encoding='utf-8')
 def test_ui_wires_bound_official_acquisition_to_center(self):
  for token in ('firmwareAcquisition.refresh()','firmwareAcquisition.selectForDevice(','firmwareAcquisition.downloadSelected(','firmwareCenter.artifact.verified'):
   self.assertIn(token,self.qml)
 def test_variant_and_build_are_explicit_catalog_controls(self):self.assertIn('id:variantBox',self.qml);self.assertIn('id:buildBox',self.qml);self.assertIn('Варіант вибирається явно',self.qml);self.assertIn('Збірка вибирається явно',self.qml)
 def test_acquisition_uses_observed_device_identity(self):self.assertIn('firmwareCenter.acquisitionIdentity(deviceBox.currentValue',self.qml);self.assertIn('deviceBox.currentValue,channelBox.currentText',self.qml)
 def test_busy_executor_blocks_catalog_mutations(self):self.assertRegex(self.qml,r'Оновити каталог";enabled:!firmwareExecutor\.busy');self.assertRegex(self.qml,r'Завантажити і перевірити";enabled:[^\n}]*!firmwareExecutor\.busy')
 def test_update_requires_explicit_authenticated_transport(self):
  self.assertIn('firmwareUpdateSession.enableAuthenticatedTransport(cameraCredentials)',self.qml);self.assertIn('known_hosts',self.qml);self.assertIn('sessionResult.enabled&&firmwareCenter.executionPlan.ready&&!firmwareExecutor.busy&&modeBox.currentText==="upgrade"',self.qml)
 def test_reboot_pending_has_explicit_verification_action(self):self.assertIn('firmwareUpdateSession.verifyAfterReboot()',self.qml);self.assertIn('firmwareExecutor.status.state==="reboot-pending"',self.qml)
 def test_close_and_reset_drop_transport_and_credentials(self):self.assertIn('firmwareUpdateSession.disableTransport()',self.qml);self.assertIn('clearSensitive()',self.qml)
if __name__=='__main__':unittest.main()
