import json
# import logging
import logging
from fuelweb_test.helpers import HTTPClient
from fuelweb_test.integration.decorators import debug


logger = logging.getLogger(__name__)
logwrap = debug(logger)

class NailgunClient(object):
    def __init__(self, ip):
        self.client = HTTPClient(
            url="http://%s:8000" % ip
        )
        super(NailgunClient, self).__init__()

    @logwrap
    def get_root(self):
        return self.client.get("/")

    @logwrap
    def list_nodes(self):
        return self.client.get("/api/nodes/")

    @logwrap
    def list_networks(self):
        return self.client.get("/api/networks/")

    @logwrap
    def get_networks(self, cluster_id):
        return self.client.get("/api/networks/?cluster_id=%d" % cluster_id)

    @logwrap
    def verify_networks(self, cluster_id, networks):
        return self.client.put(
            "/api/clusters/%d/verify/networks/" % cluster_id, networks
        )

    @logwrap
    def get_cluster_attributes(self, cluster_id):
        return self.client.get(
            "/api/clusters/%s/attributes/" % cluster_id
        )

    @logwrap
    def update_cluster_attributes(self, cluster_id, attrs):
        return self.client.put(
            "/api/clusters/%s/attributes/" % cluster_id, attrs
        )

    @logwrap
    def get_cluster(self, cluster_id):
        return self.client.get(
            "/api/clusters/%s" % cluster_id)

    @logwrap
    def update_cluster(self, cluster_id, data):
        return self.client.put(
            "/api/clusters/%s/" % cluster_id,
            data
        )

    @logwrap
    def update_node(self, node_id, data):
        return self.client.put(
            "/api/nodes/%s/" % node_id, data
        )

    @logwrap
    def update_cluster_changes(self, cluster_id):
        return self.client.put(
            "/api/clusters/%d/changes/" % cluster_id
        )

    @logwrap
    def get_task(self, task_id):
        return self.client.get("/api/tasks/%s" % task_id)

    @logwrap
    def get_releases(self):
        return self.client.get("/api/releases/")

    @logwrap
    def get_folsom_release_id(self):
        for release in json.loads(self.get_releases().read()):
            if release["name"] == "Folsom":
                return release["id"]

    @logwrap
    def list_clusters(self):
        return self.client.get("/api/clusters/")

    @logwrap
    def create_cluster(self, data):
        return self.client.post(
            "/api/clusters",
            data=data
        )

    @logwrap
    def update_network(self, cluster_id, flat_net):
        return self.client.put(
            "/api/clusters/%d/save/networks/" % cluster_id, flat_net
        )

    @logwrap
    def get_cluster_id(self, name):
        clusters = json.loads(
            self.list_clusters().read()
        )
        for cluster in clusters:
            if cluster["name"] == name:
                return cluster["id"]