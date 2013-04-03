# -*- coding: utf-8 -*-

import json
from datetime import datetime

import web

from nailgun.notifier import notifier
from nailgun.logger import logger

from nailgun.api.models import Node, NodeAttributes
from nailgun.api.handlers.base import JSONHandler, content_json


class NodeHandler(JSONHandler):
    fields = ('id', 'name', 'meta', 'network_data', 'role', 'progress',
              'status', 'mac', 'fqdn', 'ip', 'manufacturer', 'platform_name',
              'pending_addition', 'pending_deletion', 'os_platform',
              'error_type', 'online')
    model = Node

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        return self.render(node)

    @content_json
    def PUT(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        data = Node.validate_update(web.data())
        for key, value in data.iteritems():
            setattr(node, key, value)
        self.db.commit()
        return self.render(node)

    def DELETE(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        self.db.delete(node)
        self.db.commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )


class NodeCollectionHandler(JSONHandler):

    @content_json
    def GET(self):
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id == '':
            nodes = self.db.query(Node).filter_by(
                cluster_id=None).all()
        elif user_data.cluster_id:
            nodes = self.db.query(Node).filter_by(
                cluster_id=user_data.cluster_id).all()
        else:
            nodes = self.db.query(Node).all()
        return map(NodeHandler.render, nodes)

    @content_json
    def POST(self):
        data = Node.validate(web.data())
        node = Node()
        for key, value in data.iteritems():
            setattr(node, key, value)
        node.name = "Untitled (%s)" % data['mac'][-5:]
        node.timestamp = datetime.now()
        self.db.add(node)
        self.db.commit()
        node.attributes = node.create_default_attrs()
        try:
            node.attributes.generate_volumes_info()
        except Exception as exc:
            logger.warning(
                "Failed to get volumes info for node '{0}': '{1}'".format(
                    data.get("mac"),
                    str(exc)
                )
            )
            raise web.badrequest(str(exc))
        self.db.add(node)
        self.db.commit()

        try:
            ram = str(round(float(
                node.meta['memory']['total']) / 1073741824, 1))
        except (KeyError, TypeError, ValueError):
            ram = "unknown"
        cores = str(node.meta.get('cpu', {}).get('total', "unknown"))
        notifier.notify("discover",
                        "New node with %s CPU core(s) "
                        "and %s GB memory is discovered" %
                        (cores, ram), node_id=node.id)
        raise web.webapi.created(json.dumps(
            NodeHandler.render(node),
            indent=4
        ))

    @content_json
    def PUT(self):
        data = Node.validate_collection_update(web.data())
        q = self.db.query(Node)
        nodes_updated = []
        for nd in data:
            is_agent = nd.pop("is_agent") if "is_agent" in nd else False
            node = None
            if "mac" in nd:
                node = q.filter_by(mac=nd["mac"]).first() \
                    or Node.validate_existent_node_mac(nd)
            else:
                node = q.get(nd["id"])
            for key, value in nd.iteritems():
                if is_agent and (key, value) == ("status", "discover") \
                        and node.status == "provisioning":
                    # We don't update provisioning back to discover
                    logger.debug(
                        "Node is already provisioning - "
                        "status not updated by agent"
                    )
                    continue
                setattr(node, key, value)
            if is_agent:
                if not node.attributes.volumes:
                    node.attributes.generate_volumes_info()
                node.timestamp = datetime.now()
                if not node.online:
                    node.online = True
                    msg = u"Node '{0}' is back online".format(
                        node.name or node.mac
                    )
                    logger.info(msg)
                    notifier.notify(
                        "discover",
                        msg,
                        node_id=node.id
                    )
            nodes_updated.append(node)
            self.db.add(node)
            self.db.commit()
        return map(NodeHandler.render, nodes_updated)


class NodeAttributesHandler(JSONHandler):
    fields = ('node_id', 'volumes')

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        node_attrs = node.attributes
        if not node_attrs:
            return web.notfound()
        return self.render(node_attrs)

    @content_json
    def PUT(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        node_attrs = node.attributes
        if not node_attrs:
            return web.notfound()
        # NO data validation yet
        for key, value in json.loads(web.data()).iteritems():
            setattr(node_attrs, key, value)
        self.db.commit()
        return self.render(node_attrs)


class NodeAttributesByNameHandler(JSONHandler):

    @content_json
    def GET(self, node_id, attr_name):
        attr_params = web.input()
        node = self.get_object_or_404(Node, node_id)
        node_attrs = node.attributes
        if not node_attrs or not hasattr(node_attrs, attr_name):
            raise web.notfound()
        attr = getattr(node_attrs, attr_name)
        if hasattr(attr_params, "type"):
            attr = filter(lambda a: a["type"] == attr_params.type, attr)
        return attr

    @content_json
    def PUT(self, node_id, attr_name):
        node = self.get_object_or_404(Node, node_id)
        node_attrs = node.attributes
        if not node_attrs or not hasattr(node_attrs, attr_name):
            raise web.notfound()
        # WARNING: all attributes will be updated now, not those by type
        # NO data validation yet
        setattr(node_attrs, attr_name, json.loads(web.data()))
        attr = getattr(node_attrs, attr_name)
        attr_params = web.input()
        if hasattr(attr_params, "type"):
            attr = filter(lambda a: a["type"] == attr_params.type, attr)
        return attr
