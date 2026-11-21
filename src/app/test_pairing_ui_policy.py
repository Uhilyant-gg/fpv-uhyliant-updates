from pathlib import Path
import unittest
class PairingUiPolicyTests(unittest.TestCase):
 def setUp(self):self.source=(Path(__file__).with_name('PairingPanel.qml')).read_text(encoding='utf-8')
 def test_ui_does_not_start_or_confirm_peer_pairing_without_protocol(self):
  self.assertNotIn('pairingRegistry.begin(',self.source);self.assertNotIn('pairingRegistry.confirm(',self.source)
 def test_ui_does_not_expose_secret_reference(self):self.assertNotIn('secretRef',self.source)
 def test_ui_only_exposes_existing_trust_management(self):
  self.assertIn('pairingRegistry.trusted',self.source);self.assertIn('pairingRegistry.revoke(modelData.id)',self.source)
 def test_ui_states_peer_protocol_boundary(self):self.assertIn('Peer proof/exchange protocol ще не реалізований',self.source)
if __name__=='__main__':unittest.main()
