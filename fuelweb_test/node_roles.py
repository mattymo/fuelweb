class NodeRoles(object):
    def __init__(self,
                 controller_names=None,
                 compute_names=None,
                 storage_names=None,
                 proxy_names=None,
                 cobbler_names=None,
                 stomp_names=None,
                 quantum_names=None,
                 admin_names=None,
                 other_names=None):
        self.admin_names = admin_names or []
        self.controller_names = controller_names or []
        self.compute_names = compute_names or []
        self.storage_names = storage_names or []
        self.proxy_names = proxy_names or []
        self.cobbler_names = cobbler_names or []
        self.stomp_names = stomp_names or []
        self.quantum_names = quantum_names or []
        self.other_names = other_names or []


class Nodes(object):
    def __init__(self, environment, node_roles):
        self.controllers = []
        self.computes = []
        self.storages = []
        self.proxies = []
        self.cobblers = []
        self.stomps = []
        self.quantums = []
        self.admins = []
        self.others = []
        for node_name in node_roles.admin_names:
            self.admins.append(environment.node_by_name(node_name))
        for node_name in node_roles.controller_names:
            self.controllers.append(environment.node_by_name(node_name))
        for node_name in node_roles.compute_names:
            self.computes.append(environment.node_by_name(node_name))
        for node_name in node_roles.storage_names:
            self.storages.append(environment.node_by_name(node_name))
        for node_name in node_roles.proxy_names:
            self.proxies.append(environment.node_by_name(node_name))
        for node_name in node_roles.cobbler_names:
            self.cobblers.append(environment.node_by_name(node_name))
        for node_name in node_roles.stomp_names:
            self.stomps.append(environment.node_by_name(node_name))
        for node_name in node_roles.quantum_names:
            self.quantums.append(environment.node_by_name(node_name))
        for node_name in node_roles.other_names:
            self.others.append(environment.node_by_name(node_name))
        self.slaves = self.controllers + self.computes + self.storages + \
            self.proxies + self.cobblers + self.stomps + \
            self.quantums + self.others
        self.all = self.slaves + self.admins
        self.admin = self.admins[0]

    def __iter__(self):
        return self.all.__iter__()
