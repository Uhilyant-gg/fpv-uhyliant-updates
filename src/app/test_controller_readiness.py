import unittest
from controller_readiness import controller_readiness

class ControllerReadinessTests(unittest.TestCase):
    def test_missing_controller_is_unknown(self):
        result=controller_readiness(None);self.assertEqual(result["health"],"unknown");self.assertEqual(result["action"],"connect-controller")
    def test_connected_without_observed_inputs_is_unknown(self):
        result=controller_readiness({"connected":True});self.assertEqual(result["health"],"unknown")
    def test_invalid_observed_input_blocks_readiness(self):
        result=controller_readiness({"connected":True,"channels":[float("nan")],"calibrated":True,"mappingValid":True})
        self.assertEqual(result["health"],"problem");self.assertEqual(result["action"],"diagnose")
    def test_uncalibrated_observed_controller_requires_calibration(self):
        result=controller_readiness({"connected":True,"channels":[1500],"calibrated":False});self.assertEqual(result["action"],"calibrate-controller")
    def test_missing_mapping_has_a_recovery_action(self):
        result=controller_readiness({"connected":True,"channels":[1500],"calibrated":True})
        self.assertEqual(result["action"],"map-controller-inputs")
    def test_ready_requires_observed_inputs_calibration_and_mapping(self):
        result=controller_readiness({"connected":True,"channels":[1500],"calibrated":True,"mappingValid":True});self.assertEqual(result["health"],"ready")

if __name__=="__main__":unittest.main()
