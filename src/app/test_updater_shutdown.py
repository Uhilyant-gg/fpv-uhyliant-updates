import threading
import unittest

from PySide6.QtCore import QCoreApplication, QThread

import updater_engine


class _BlockingWorker(QThread):
    def __init__(self):
        super().__init__()
        self.release = threading.Event()

    def run(self):
        while not self.isInterruptionRequested() and not self.release.wait(0.01):
            pass


class UpdaterShutdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_network_disabled_check_starts_no_worker(self):
        updater = updater_engine.Updater(network=False)
        updater.check()
        self.assertIsNone(updater.w)
        self.assertEqual(updater.updateState, 'idle')
        self.assertFalse(updater.busy)

    def test_shutdown_without_worker_is_noop(self):
        self.assertTrue(updater_engine.Updater().shutdown())

    def test_shutdown_interrupts_and_waits_for_running_worker(self):
        updater = updater_engine.Updater()
        worker = _BlockingWorker()
        updater.w = worker
        worker.start()
        self.assertTrue(updater.shutdown(timeout_ms=2000))
        self.assertFalse(worker.isRunning())


if __name__ == '__main__':
    unittest.main()
