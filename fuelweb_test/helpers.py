import socket
import subprocess
import urllib2
import logging
import json
import threading
import select


logger = logging.getLogger(__name__)

"""
Integration test helpers
"""


class HTTPClient(object):
    def __init__(self, url=""):
        self.url = url
        self.opener = urllib2.build_opener(urllib2.HTTPHandler)

    def get(self, endpoint):
        req = urllib2.Request(self.url + endpoint)
        return self._open(req)

    def post(self, endpoint, data=None, content_type="application/json"):
        if not data: data = {}
        req = urllib2.Request(self.url + endpoint, data=json.dumps(data))
        req.add_header('Content-Type', content_type)
        return self._open(req)

    def put(self, endpoint, data=None, content_type="application/json"):
        if not data: data = {}
        req = urllib2.Request(self.url + endpoint, data=json.dumps(data))
        req.add_header('Content-Type', content_type)
        req.get_method = lambda: 'PUT'
        return self._open(req)

    def _open(self, req):
        try:
            res = self.opener.open(req)
        except urllib2.HTTPError as err:
            res = type(
                'HTTPError',
                (object,),
                {
                    'read': lambda s: str(err),
                    'getcode': lambda s: err.code
                }
            )()
        return res


class LogServer(threading.Thread):
    def __init__(self, address="localhost", port=5514):
        logger.debug("Initializing LogServer: %s:%s",
                     str(address), str(port))
        super(LogServer, self).__init__()
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        )
        self.socket.bind((str(address), port))
        self.rlist = [self.socket]
        self._stop = threading.Event()
        self._handler = self.default_handler
        self._status = False

    @classmethod
    def default_handler(cls, message):
        pass

    def set_status(self, status):
        self._status = status

    def get_status(self):
        return self._status

    def set_handler(self, handler):
        self._handler = handler

    def stop(self):
        logger.debug("LogServer is stopping ...")
        self.socket.close()
        self._stop.set()

    def started(self):
        return not self._stop.is_set()

    def rude_join(self, timeout=None):
        self._stop.set()
        super(LogServer, self).join(timeout)

    def join(self, timeout=None):
        self.rude_join(timeout)

    def run(self):
        logger.debug("LogServer is listening for messages ...")
        while self.started():
            r, w, e = select.select(self.rlist, [], [], 1)
            if self.socket in r:
                message, addr = self.socket.recvfrom(2048)
                self._handler(message)


def _block_mac_in_ebtables(mac):
    try:
        subprocess.check_output(
            'sudo ebtables -t filter -A FORWARD -s %s -j DROP' % mac,
            stderr=subprocess.STDOUT,
            shell=True
        )
        logging.debug("MAC %s blocked via ebtables.", mac)
    except subprocess.CalledProcessError as e:
        raise Exception("Can't block mac %s via ebtables: %s",
                        mac, e.output)


def _restore_mac_in_ebtables(mac):
    try:
        subprocess.check_output(
            'sudo ebtables -t filter -D FORWARD -s %s -j DROP' % mac,
            stderr=subprocess.STDOUT,
            shell=True
        )
        logging.debug("MAC %s unblocked via ebtables.", mac)
    except subprocess.CalledProcessError as e:
        logging.warn("Can't restore mac %s via ebtables: %s",
                     mac, e.output)
