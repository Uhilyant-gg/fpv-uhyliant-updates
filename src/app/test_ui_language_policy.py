from pathlib import Path
import re
import unittest
class UiLanguagePolicyTests(unittest.TestCase):
 def setUp(self):
  here=Path(__file__).parent;self.firmware=(here/'FirmwareCenter.qml').read_text(encoding='utf-8');self.update=(here/'UpdatePanel.qml').read_text(encoding='utf-8')
 def visible(self,source):return '\n'.join(re.findall(r'(?:text|placeholderText)\s*:\s*"([^"]*)"',source))
 def test_firmware_surface_is_ukrainian(self):
  visible=self.visible(self.firmware)
  for text in ('ЦЕНТР ПРОШИВКИ','Попередня перевірка','Підготувати план виконання','ПРЕСЕТ КАМЕРИ'):self.assertIn(text,visible)
  for obsolete in ('FIRMWARE CENTER','IMAGE VERIFIED','PRE-CHECK APPROVED','EXECUTION PLAN READY','Expected SHA-256','Flash layout verified','Recovery path verified'):self.assertNotIn(obsolete,visible)
 def test_update_surface_has_delayed_help(self):self.assertGreaterEqual(self.update.count('HoverHint{'),3)
 def test_firmware_surface_has_delayed_help(self):self.assertGreaterEqual(self.firmware.count('HoverHint{'),8)
if __name__=='__main__':unittest.main()
