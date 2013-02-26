# -*- coding: utf-8 -*-

import logging
from multiprocessing import Process

import nailgun.rpc as rpc
from nailgun.logger import logger
from nailgun.rpc.receiver import NailgunReceiver


class RPCProcess(Process):

    def create_receiver(self, queue_name, rec_class):
        eventlet.monkey_patch()
        self.receiver = rec_class()
        self.conn = rpc.create_connection(True)
        self.conn.create_consumer(queue_name, self.receiver)
        self.conn.consume()
        self.conn.close()

    def __init__(self, queue_name='nailgun', rec_class=NailgunReceiver):
        super(RPCProcess, self).__init__(
            target=self.create_receiver,
            args=(
                queue_name,
                rec_class
            )
        )
