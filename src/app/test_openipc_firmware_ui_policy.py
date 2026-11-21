from pathlib import Path
import unittest
class Tests(unittest.TestCase):
 def setUp(self):self.qml=(Path(__file__).parent/'FirmwareCenter.qml').read_text(encoding='utf-8');self.acquisition=(Path(__file__).parent/'openipc_firmware_acquisition.py').read_text(encoding='utf-8')
 def test_primary_flow_is_automatic_and_destructive_action_is_explicit(self):
  self.assertIn('firmwareAcquisition.prepareRecommended(deviceBox.currentValue)',self.qml);self.assertIn('firmwareCenter.prepareAutomaticUpgrade(deviceBox.currentValue)',self.qml);self.assertIn('text:"Оновити камеру"',self.qml);self.assertIn('firmwareUpdateSession.execute(deviceBox.currentValue,automaticProfile,"upgrade")',self.qml);self.assertNotIn('firmwareUpdateSession.execute(deviceBox.currentValue,"ssc30kq-imx335","upgrade")',self.qml)
 def test_active_camera_is_preferred(self):self.assertIn('if(items[i].active===true)',self.qml);self.assertIn('Component.onCompleted:activeDevice()',self.qml)
 def test_human_readable_camera_card_preserves_unknowns(self):
  for token in ('OpenIPC: ','Платформа / сенсор: ','Встановлена firmware: ','Доступна firmware: ','не спостережено'):self.assertIn(token,self.qml)
 def test_ambiguous_catalog_requires_explicit_advanced_choice(self):
  self.assertIn('selectRecommendedForDevice',self.acquisition);self.assertIn("resolve(self._catalog,device['platform'],device['sensor'])",self.acquisition);self.assertIn('id:variantBox',self.qml);self.assertIn('Варіант вибирається явно',self.qml)
 def test_manual_image_and_technical_controls_are_advanced(self):self.assertIn('visible:advanced',self.qml);self.assertIn('РУЧНИЙ ШЛЯХ ЛОКАЛЬНОГО ОБРАЗУ',self.qml);self.assertIn('Очікуваний SHA-256',self.qml)
 def test_credentials_are_conditional_masked_and_session_only(self):
  self.assertIn('visible:firmwareCenter.executionPlan.ready||hardwareReady.checks.credentialsPresent',self.qml);self.assertIn('echoMode:TextInput.Password',self.qml);self.assertIn('Дані потрібні лише для цього сеансу й не зберігаються.',self.qml);self.assertIn('clearSensitive()',self.qml)
 def test_update_requires_authenticated_transport_plan_and_observed_profile(self):self.assertIn('enabled:sessionResult.enabled&&firmwareCenter.executionPlan.ready&&automaticProfile!==""&&!firmwareExecutor.busy',self.qml);self.assertIn('firmwareUpdateSession.enableAuthenticatedTransport(cameraCredentials,hardwareE2ERuntime)',self.qml);self.assertIn('firmwareCenter.compatibleProfile(deviceBox.currentValue||"")',self.qml)
 def test_progress_and_post_reboot_verification_are_visible(self):
  for stage in ('Підготовка','Завантаження','Оновлення','Перезапуск','Перевірка'):self.assertIn(stage,self.qml)
  self.assertIn('firmwareUpdateSession.verifyAfterReboot()',self.qml);self.assertIn('Камеру успішно оновлено до ',self.qml)
if __name__=='__main__':unittest.main()
