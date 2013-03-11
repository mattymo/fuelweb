# -*- coding: utf-8 -*-

import time
import logging
import threading
from datetime import datetime
from itertools import repeat

from sqlalchemy.sql import not_

from nailgun.notifier import notifier
from nailgun.db import orm
from nailgun.settings import settings
from nailgun.api.models import Node
from nailgun.logger import logger


class KeepAliveThread(threading.Thread):

    def __init__(self, interval=None, timeout=None):
        super(KeepAliveThread, self).__init__()
        self.stoprequest = threading.Event()
        self.interval = interval or settings.KEEPALIVE['interval']
        self.timeout = timeout or settings.KEEPALIVE['timeout']
        self.db = orm()
        self.reset_nodes_timestamp()

    def reset_nodes_timestamp(self):
        for node_db in self.db.query(Node).all():
            node_db.timestamp = datetime.now()
            self.db.add(node_db)
        self.db.commit()

    def join(self, timeout=None):
        self.stoprequest.set()
        super(KeepAliveThread, self).join(timeout)

    def sleep(self, interval=None):
        map(
            lambda i: not self.stoprequest.isSet() and time.sleep(i),
            repeat(1, interval or self.interval)
        )

    def run(self):
        while not self.stoprequest.isSet():
            self.db.expire_all()
            for node_db in self.db.query(Node).filter(
                # nodes may become unresponsive while provisioning
                not_(Node.status == 'provisioning')
            ):
                timedelta = (datetime.now() - node_db.timestamp).seconds
                if timedelta > self.timeout:
                    logger.warning(
                        u"Node '{0}' seems to be offline "
                        "for {1} seconds...".format(
                            node_db.name,
                            timedelta
                        )
                    )
                    if node_db.online:
                        node_db.online = False
                        self.db.add(node_db)
                        self.db.commit()
                        notifier.notify(
                            "error",
                            u"Node '{0}' has gone away".format(
                                node_db.name or node_db.mac
                            ),
                            node_id=node_db.id
                        )
            self.sleep()
