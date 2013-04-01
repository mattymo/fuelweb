import logging
from unittest.case import TestCase
import time

from fuelweb_test.integration.ci_fuel_web import CiFuelWeb

logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s',
                    level=logging.DEBUG)


class BaseTestCase(TestCase):
    def ci(self):
        if not hasattr(self, '_ci'):
            self._ci = CiFuelWeb()
        return self._ci

    def environment(self):
        return self.ci().environment()

    def nodes(self):
        return self.ci().nodes()

    def remote(self):
        """
        :rtype : SSHClient
        """
        return self.nodes().admin.remote(
            'internal',
            login='root',
            password='r00tme')

    def get_admin_node_ip(self):
        return str(
            self.nodes().admin.get_ip_address_by_network_name('internal'))

    def _wait_for_threads(self):
        import threading

        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                if hasattr(thread, "rude_join"):
                    timer = time.time()
                    timeout = 25
                    thread.rude_join(timeout)
                    if time.time() - timer > timeout:
                        raise Exception("Thread stopping timed out")
