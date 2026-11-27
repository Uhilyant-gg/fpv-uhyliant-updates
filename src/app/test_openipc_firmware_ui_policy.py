from pathlib import Path
import re,unittest
from PySide6.QtCore import QCoreApplication
from PySide6.QtQml import QJSEngine

_app=QCoreApplication.instance() or QCoreApplication([])
class Tests(unittest.TestCase):
 def setUp(self):
  root=Path(__file__).parent;self.qml=(root/'FirmwareCenter.qml').read_text(encoding='utf-8');self.acquisition=(root/'openipc_firmware_acquisition.py').read_text(encoding='utf-8');self.compact=re.sub(r'\s+','',self.qml)
 def has_call(self,receiver,args):self.assertIn(receiver+'('+','.join(args)+')',self.compact)
 def test_primary_flow_derives_profile_and_keeps_destructive_action_explicit(self):
  self.has_call('firmwareAcquisition.prepareRecommended',['deviceBox.currentValue']);self.has_call('firmwareCenter.prepareAutomaticUpgrade',['deviceBox.currentValue']);self.has_call('firmwareUpdateSession.execute',['deviceBox.currentValue','automaticProfile','"upgrade"']);self.assertIn('"Оновити камеру"',self.qml);self.assertNotIn('execute(deviceBox.currentValue,"ssc30kq-imx335"',self.compact)
 def test_new_automatic_check_clears_previous_plan_and_transport_first(self):
  body=self.compact.split('functionprepareAutomatic(){',1)[1].split('functionphase()',1)[0]
  self.assertIn('firmwareExecutor.busy',body)
  self.assertLess(body.index('firmwareUpdateSession.disableTransport()'),body.index('firmwareAcquisition.prepareRecommended('))
  self.assertLess(body.index('firmwareCenter.reset()'),body.index('firmwareAcquisition.prepareRecommended('))
 def test_failed_or_ambiguous_acquisition_is_explained_before_ready_plan(self):
  body=self.compact.split('functionstateText(){',1)[1].split('Component.onCompleted',1)[0]
  self.assertLess(body.index('firmwareAcquisition.status.reason'),body.index('firmwareCenter.executionPlan.ready'))
  self.assertLess(body.index('selectedFirmware.reason'),body.index('firmwareCenter.executionPlan.ready'))
 def test_failed_recheck_revokes_old_plan_and_shows_failure(self):
  engine=QJSEngine()
  setup='''var events=[], deviceBox={currentValue:"cam"}, firmwareExecutor={busy:false}, sessionResult={state:"ready"}, hw={ready:true}, automaticProfile="profile", selectedFirmware={};
var firmwareCenter={executionPlan:{ready:true},reset:function(){events.push("reset");this.executionPlan.ready=false},prepareAutomaticUpgrade:function(){events.push("plan")}};
var firmwareUpdateSession={disableTransport:function(){events.push("disable")}};
var firmwareAcquisition={status:{reason:""},prepareRecommended:function(){events.push("check");this.status.reason="Перевірте мережу";return false}};
function bindDevice(){events.push("bind")}'''
  functions='\n'.join(line.strip() for line in self.qml.splitlines() if line.strip().startswith(('function prepareAutomatic()', 'function stateText()')))
  result=engine.evaluate(setup+'\n'+functions+'\nprepareAutomatic();')
  self.assertFalse(result.isError(),result.toString())
  self.assertEqual(engine.evaluate('events.join(",")').toString(),'disable,reset,bind,check')
  self.assertFalse(engine.evaluate('firmwareCenter.executionPlan.ready').toBool())
  self.assertEqual(engine.evaluate('stateText()').toString(),'Перевірте мережу')
  engine.evaluate('firmwareAcquisition.status.reason="";selectedFirmware.reason="Оберіть варіант";firmwareCenter.executionPlan.ready=true;')
  self.assertEqual(engine.evaluate('stateText()').toString(),'Оберіть варіант')
 def test_selected_camera_is_bound_to_preflight(self):
  self.assertIn('Component.onCompleted:activeDevice()',self.compact);self.has_call('hardwareE2ERuntime.selectDevice',['deviceBox.currentValue||""']);self.assertIn('onCurrentValueChanged:root.bindDevice()',self.compact)
 def test_human_readable_camera_card_preserves_unknowns(self):
  for token in ('OpenIPC: ','Платформа / сенсор: ','Встановлена firmware: ','Доступна firmware: ','не спостережено'):self.assertIn(token,self.qml)
 def test_ambiguous_catalog_requires_explicit_advanced_choice(self):
  self.assertIn('selectRecommendedForDevice',self.acquisition);self.assertIn("resolve(self._catalog,device['platform'],device['sensor'])",self.acquisition);self.assertIn('id:variantBox',self.compact);self.assertIn('Варіант вибирається явно',self.qml)
 def test_manual_image_and_technical_controls_are_advanced(self):
  self.assertIn('visible:advanced',self.compact);self.assertIn('РУЧНИЙ ШЛЯХ ЛОКАЛЬНОГО ОБРАЗУ',self.qml);self.assertIn('Очікуваний SHA-256',self.qml)
 def test_credentials_are_masked_session_only_and_preflight_gated(self):
  self.assertIn('echoMode:TextInput.Password',self.compact);self.assertIn('Qt.ImhSensitiveData',self.compact);self.assertIn('clearSensitive()',self.compact);self.has_call('firmwareUpdateSession.enableAuthenticatedTransport',['cameraCredentials','hardwareE2ERuntime']);self.assertIn('hardwareReady.ready',self.compact)
 def test_update_requires_transport_plan_profile_and_idle_executor(self):
  update=re.search(r'Button\s*\{[^{}]*text:"Оновити камеру"[^{}]*\}',self.qml)
  self.assertIsNotNone(update);body=re.sub(r'\s+','',update.group(0))
  for gate in ('sessionResult.enabled','firmwareCenter.executionPlan.ready','automaticProfile!==""','!firmwareExecutor.busy'):self.assertIn(gate,body)
 def test_progress_and_post_reboot_verification_are_visible(self):
  for stage in ('Підготовка','Завантаження','Оновлення','Перезапуск','Перевірка'):self.assertIn(stage,self.qml)
  self.has_call('firmwareUpdateSession.verifyAfterReboot',[]);self.assertIn('Камеру успішно оновлено до ',self.qml)
if __name__=='__main__':unittest.main()
