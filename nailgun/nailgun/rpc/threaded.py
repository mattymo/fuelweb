# -*- coding: utf-8 -*-

import logging
import threading

import nailgun.rpc as rpc
from nailgun.logger import logger
from nailgun.rpc.receiver import NailgunReceiver


class RPCThread(threading.Thread):
    def __init__(self, rec_class=NailgunReceiver):
        super(RPCThread, self).__init__()
        self.stoprequest = threading.Event()
        self.receiver = rec_class()

    def join(self, timeout=None):
        self.stoprequest.set()
        super(RPCThread, self).join(timeout)

    def run(self):
        logger.info("Starting RPC thread...")
        self.conn = rpc.create_connection(True)
        self.conn.create_consumer('nailgun', self.receiver)
        it = self.conn.iterconsume(limit=None, stopevent=self.stoprequest)
        while not self.stoprequest.isSet():
            try:
                it.next()
            except StopIteration:
                return
        self.conn.close()
