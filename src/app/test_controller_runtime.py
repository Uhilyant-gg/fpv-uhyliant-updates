import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from controller_onboarding import ControllerOnboarding
from controller_profile_store import JsonControllerProfileStore
from controller_runtime import ControllerRuntime, human_step_error, human_summary


class Radio:
    def __init__(self):
        self.frame = [1500, 1500, 1000, 1500]
        self.present = True

    def poll(self):
        if not self.present:
            return []
        return [{"vendorId": 0x1209, "productId": 0x4F54, "name": "EdgeTX Radio", "channels": list(self.frame)}]


class Clock:
    now = 5.0

    def __call__(self):
        return self.now


class ControllerRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.radio = Radio()
        store = JsonControllerProfileStore(Path(self.tmp.name) / "controllers.json")
        self.runtime = ControllerRuntime(ControllerOnboarding(self.radio, store, Clock()))

    def tearDown(self):
        self.runtime.deactivate()
        self.tmp.cleanup()

    def hold(self, frame):
        self.radio.frame = frame
        self.runtime._tick()

    def test_new_radio_offers_configuration(self):
        self.runtime.activate()
        self.assertEqual(self.runtime.health, "attention")
        self.assertTrue(self.runtime.canConfigure)
        self.assertEqual(self.runtime.controllerName, "EdgeTX Radio")
        self.assertIn("Налаштуйте", self.runtime.summary)

    def test_wizard_walkthrough_saves_and_restores(self):
        self.runtime.activate()
        self.runtime.startWizard()
        self.assertTrue(self.runtime.wizardActive)
        self.assertEqual(self.runtime.wizardStep, "center")
        steps = [
            [1500, 1500, 1000, 1500],
            [1900, 1500, 1000, 1500],
            [1500, 1100, 1000, 1500],
            [1500, 1500, 1000, 1100],
            [1500, 1500, 2000, 1500],
        ]
        for frame in steps:
            self.hold(frame)
            self.runtime.nextStep()
            self.assertEqual(self.runtime.stepError, "")
        self.assertEqual(self.runtime.wizardStep, "sweep")
        for frame in ([1000, 1000, 1000, 1000], [2000, 2000, 2000, 2000], [1500, 1500, 1000, 1500]):
            self.hold(frame)
        self.runtime.nextStep()
        self.assertFalse(self.runtime.wizardActive)
        self.assertTrue(self.runtime.restored, self.runtime.summary)
        self.assertEqual(self.runtime.health, "ready")
        self.assertEqual(self.runtime.controls["throttle"], 0.0)
        self.assertTrue(self.runtime.canForget)

    def test_ambiguous_step_shows_human_error_and_stays_on_step(self):
        self.runtime.activate()
        self.runtime.startWizard()
        self.hold([1500, 1500, 1000, 1500])
        self.runtime.nextStep()
        self.hold([1900, 1900, 1000, 1500])
        self.runtime.nextStep()
        self.assertEqual(self.runtime.wizardStep, "roll")
        self.assertIn("кілька каналів", self.runtime.stepError)

    def test_unplug_during_wizard_aborts(self):
        self.runtime.activate()
        self.runtime.startWizard()
        self.radio.present = False
        self.runtime._tick()
        self.assertFalse(self.runtime.wizardActive)
        self.assertIn("від'єднано", self.runtime.stepError)

    def test_no_radio_is_unknown(self):
        self.radio.present = False
        self.runtime.activate()
        self.assertEqual(self.runtime.health, "unknown")
        self.assertFalse(self.runtime.canConfigure)
        self.runtime.startWizard()
        self.assertFalse(self.runtime.wizardActive)

    def test_observe_takes_one_reading_without_polling(self):
        self.runtime.observe()
        self.assertEqual(self.runtime.health, "attention")
        self.assertFalse(self.runtime.active)
        self.radio.present = False
        self.runtime.observe()
        self.assertEqual(self.runtime.health, "unknown")

    def test_every_message_is_human(self):
        self.assertEqual(human_summary("something-new"), "Стан пульта невідомий.")
        self.assertNotIn("controller-", human_step_error("controller-unexpected"))


if __name__ == "__main__":
    unittest.main()
