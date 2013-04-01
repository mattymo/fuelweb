import logging
import time
import json
import subprocess
from devops.helpers.helpers import SSHClient, wait
from paramiko import RSAKey
from fuelweb_test.helpers import LogServer
from fuelweb_test.integration.base_test_case import BaseTestCase
from fuelweb_test.integration.decorators import snapshot_errors, debug, fetch_logs
from fuelweb_test.nailgun_client import NailgunClient
from fuelweb_test.settings import CLEAN

logging.basicConfig(
    format=':%(lineno)d: %(asctime)s %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestNode(BaseTestCase):
    def setUp(self):
        if CLEAN:
            self.ci().get_empty_state()
        self.nailgun_client = NailgunClient(self.get_admin_node_ip())


    @logwrap
    @fetch_logs()
    def _start_logserver(self, handler=None):
        def handler(self, message):
            """
            We define log message handler in such a way
            assuming that if at least one message is received
            logging works ok.
            """
            self.set_status(True)

        self.logserver = LogServer(
            address=self.ci().get_host_node_ip(),
            port=5514
        )
        self.logserver.set_status(True)
        self.logserver.set_handler(handler)

        self.logserver.start()

    @logwrap
    @fetch_logs()
    def test_release_upload(self):
        self._upload_sample_release()

    @logwrap
    @fetch_logs()
    def test_http_returns_200(self):
        resp = self.nailgun_client.get_root()
        self.assertEquals(200, resp.getcode())

    @logwrap
    @fetch_logs()
    def test_create_empty_cluster(self):
        self._create_cluster(name='empty')

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_node_deploy(self):
        self._bootstrap_nodes(['slave-01'])

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_updating_nodes_in_cluster(self):
        cluster_id = self._create_cluster(name='empty')
        nodes = self._bootstrap_nodes(['slave-01'])
        self._update_nodes_in_cluster(cluster_id, nodes)

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_one_node_provisioning(self):
        self._clean_clusters()
        self._basic_provisioning('provision', {'controller': ['slave-01']})

    @logwrap
    @fetch_logs()
    def restore_vlans_in_ebtables(self, cluster_id, devops_nodes):
        for vlan in self._get_cluster_vlans(cluster_id):
            for devops_node in devops_nodes:
                for interface in devops_node.interfaces:
                    self._restore_vlan_in_ebtables(
                        interface.target_dev,
                        vlan,
                        False
                    )

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_simple_cluster_flat(self):
        cluster_name = 'simple_flat'
        nodes = {'controller': ['slave-01'], 'compute': ['slave-02']}
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        node = self._get_slave_node_by_devops_node(self.nodes().slaves[0])
        wait(lambda: self._check_cluster_status(node['ip'], 5), timeout=300)
        self.restore_vlans_in_ebtables(cluster_id, self.nodes().slaves[:2])
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network simple flat', 60 * 2)

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_simple_cluster_vlan(self):
        cluster_name = 'simple_vlan'
        nodes = {'controller': ['slave-01'], 'compute': ['slave-02']}
        self._create_cluster(name=cluster_name, net_manager="VlanManager")
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        slave = self.nodes().slaves[0]
        node = self._get_slave_node_by_devops_node(slave)
        wait(lambda: self._check_cluster_status(node['ip'], 5, 8), timeout=300)

        logging.info("Verifying networks for simple vlan installation.")
        self.restore_vlans_in_ebtables(cluster_id, self.nodes().slaves[:2])
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network simple vlan', 60 * 2)

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_ha_cluster_flat(self):
        cluster_name = 'ha_flat'
        nodes = {
            'controller': ['slave-01', 'slave-02', 'slave-03'],
            'compute': ['slave-04', 'slave-05']
        }
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        logging.info("Checking cluster status on slave1")
        slave = self.nodes().slaves[0]
        node = self._get_slave_node_by_devops_node(slave)
        wait(lambda: self._check_cluster_status(node['ip'], 13), timeout=300)

        logging.info("Verifying networks for ha flat installation.")
        self.restore_vlans_in_ebtables(cluster_id, self.nodes().slaves[:5])
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network ha flat', 60 * 2)


    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_ha_cluster_vlan(self):
        cluster_name = 'ha_vlan'
        nodes = {
            'controller': ['slave-01', 'slave-02', 'slave-03'],
            'compute': ['slave-04', 'slave-05']
        }
        self._create_cluster(name=cluster_name, net_manager="VlanManager")
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        slave = self.nodes().slaves[0]
        node = self._get_slave_node_by_devops_node(slave)
        wait(
            lambda: self._check_cluster_status(node['ip'], 13, 8),
            timeout=300
        )

        logging.info("Verifying networks for ha vlan installation.")
        self.restore_vlans_in_ebtables(cluster_id, self.nodes().slaves[:5])
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network ha vlan', 60 * 2)

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_network_config(self):
        self._clean_clusters()
        self._basic_provisioning('network_config', {'controller': ['slave-01']})

        slave = self.nodes().slaves[0]
        node = self._get_slave_node_by_devops_node(slave)
        ctrl_ssh = SSHClient(node['ip'], username='root', password='r00tme',
                             private_keys=self.get_private_keys())
        ifaces_fail = False
        for iface in node['network_data']:
            try:
                ifname = "%s.%s@%s" % (
                    iface['dev'], iface['vlan'], iface['dev']
                )
                ifname_short = "%s.%s" % (iface['dev'], iface['vlan'])
            except KeyError:
                ifname = iface['dev']
            iface_data = ''.join(
                ctrl_ssh.execute(
                    '/sbin/ip addr show dev %s' % ifname_short
                )['stdout']
            )
            if iface_data.find(ifname) == -1:
                logging.error("Interface %s is absent" % ifname_short)
                ifaces_fail = True
            else:
                try:
                    if iface_data.find("inet %s" % iface['ip']) == -1:
                        logging.error(
                            "Interface %s does not have ip %s" % (
                                ifname_short, iface['ip']
                            )
                        )
                        ifaces_fail = True
                except KeyError:
                    if iface_data.find("inet ") != -1:
                        logging.error(
                            "Interface %s does have ip.  And it should not" %
                            ifname_short
                        )
                        ifaces_fail = True
                try:
                    if iface_data.find("brd %s" % iface['brd']) == -1:
                        logging.error(
                            "Interface %s does not have broadcast %s" % (
                                ifname_short, iface['brd']
                            )
                        )
                        ifaces_fail = True
                except KeyError:
                    pass
        self.assertEquals(ifaces_fail, False)

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_node_deletion(self):
        cluster_name = 'node_deletion'
        node_name = 'slave-01'
        nodes = {'controller': [node_name]}
        cluster_id = self._basic_provisioning(cluster_name, nodes)

        slave = self.nodes().slaves[0]
        node = self._get_slave_node_by_devops_node(slave)
        self.nailgun_client.update_node(node['id'], {'pending_deletion': True})
        task = self._launch_provisioning(cluster_id)
        self._task_wait(task, 'Node deletion')

        timer = time.time()
        timeout = 3 * 60
        while True:
            response = self.nailgun_client.list_nodes()
            nodes = json.loads(response.read())
            for n in nodes:
                if (n['mac'] == node['mac'] and n['status'] == 'discover'):
                    return
            if (time.time() - timer) > timeout:
                raise Exception("Bootstrap boot timeout expired!")
            time.sleep(5)

    @logwrap
    def block_first_vlan_in_ebtables(self, cluster_id, devops_nodes):
        vlans = self._get_cluster_vlans(cluster_id)
        for node in devops_nodes:
            for interface in node.interfaces:
                self._block_vlan_in_ebtables(interface.target_dev, vlans[0])

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_network_verify_with_blocked_vlan(self):
        cluster_name = 'net_verify'
        cluster_id = self._create_cluster(name=cluster_name)
        node_names = ['slave-01', 'slave-02']
        nailgun_slave_nodes = self._bootstrap_nodes(node_names)
        devops_nodes = self.nodes().slaves[:2]
        logging.info("Clear BROUTING table entries.")
        self.restore_vlans_in_ebtables(cluster_id, devops_nodes)
        self._update_nodes_in_cluster(cluster_id, nailgun_slave_nodes)
        self.block_first_vlan_in_ebtables(cluster_id, devops_nodes)
        task = self._run_network_verify(cluster_id)
        task = self._task_wait(task,
                               'Verify network in cluster with blocked vlan',
                               60 * 2, True)
        self.assertEquals(task['status'], 'error')

    @snapshot_errors()
    @logwrap
    @fetch_logs()
    def test_multinic_bootstrap_booting(self):
        slave = self.nodes().slaves[0]
        nodename = slave.name
        logging.info("Using node %r with %d interfaces", nodename,
                     len(slave.interfaces))
        slave.stop()
        macs = [i.mac_address for i in slave.interfaces]
        logging.info("Block all MACs: %s.",
                     ', '.join([m for m in macs]))
        for mac in macs:
            self._block_mac_in_ebtables(mac)
            self.addCleanup(self._restore_mac_in_ebtables, mac)
        for mac in macs:
            logging.info("Trying to boot node %r via interface with MAC %s...",
                         nodename, mac)
            self._restore_mac_in_ebtables(mac)
            slave.start()
            nailgun_slave = self._bootstrap_nodes([nodename])[0]
            self.assertEqual(mac.upper(), nailgun_slave['mac'].upper())
            slave.stop()
            self._block_mac_in_ebtables(mac)

    @staticmethod
    @logwrap
    def _block_mac_in_ebtables(mac):
        try:
            subprocess.check_output(
                ['sudo', 'ebtables', '-t', 'filter', '-A', 'FORWARD', '-s', mac,
                 '-j', 'DROP'],
                stderr=subprocess.STDOUT,
                shell=True
            )
            logging.debug("MAC %s blocked via ebtables.", mac)
        except subprocess.CalledProcessError as e:
            raise Exception("Can't block mac %s via ebtables: %s",
                            mac, e.output)

    @staticmethod
    @logwrap
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

    @logwrap
    def _block_vlan_in_ebtables(self, target_dev, vlan):
        try:
            subprocess.check_output(
                'sudo ebtables -t broute -A BROUTING -i %s -p 8021Q'
                ' --vlan-id %s -j DROP' % (
                    target_dev, vlan
                ),
                stderr=subprocess.STDOUT,
                shell=True
            )
            self.addCleanup(self._restore_vlan_in_ebtables,
                            target_dev, vlan)
            logging.debug("Vlan %s on interface %s blocked via ebtables.",
                          vlan, target_dev)
        except subprocess.CalledProcessError as e:
            raise Exception("Can't block vlan %s for interface %s"
                            " via ebtables: %s" %
                            (vlan, target_dev, e.output))

    @logwrap
    def _get_common_vlan(self, cluster_id):
        """Find vlan that must be at all two nodes.
        """
        resp = self.nailgun_client.list_networks()
        self.assertEquals(200, resp.getcode())
        for net in json.loads(resp.read()):
            if net['cluster_id'] == cluster_id:
                return net['vlan_start']
        raise Exception("Can't find vlan for cluster_id %s" % cluster_id)

    @logwrap
    def _get_cluster_vlans(self, cluster_id):
        resp = self.nailgun_client.get_networks(cluster_id)
        self.assertEquals(200, resp.getcode())
        cluster_vlans = []
        for n in json.loads(resp.read()):
            amount = n.get('amount', 1)
            cluster_vlans.extend(range(n['vlan_start'],
                                       n['vlan_start'] + amount))
        self.assertNotEqual(cluster_vlans, [])
        return cluster_vlans

    @staticmethod
    @logwrap
    def _restore_vlan_in_ebtables(target_dev, vlan, log=True):
        try:
            subprocess.check_output(
                'sudo ebtables -t broute -D BROUTING -i %s -p 8021Q'
                ' --vlan-id %s -j DROP' % (
                    target_dev, vlan
                ),
                stderr=subprocess.STDOUT,
                shell=True
            )
            logging.debug("Vlan %s on interface %s unblocked via ebtables.",
                          vlan, target_dev)
        except subprocess.CalledProcessError as e:
            if log:
                logging.warn("Can't restore vlan %s for interface %s"
                             " via ebtables: %s" %
                             (vlan, target_dev, e.output))

    @logwrap
    def _run_network_verify(self, cluster_id):
        logging.info(
            "Run network verify in cluster %d",
            cluster_id
        )
        resp = self.nailgun_client.get_networks(cluster_id)
        self.assertEquals(200, resp.getcode())
        networks = json.loads(resp.read())
        changes = self.nailgun_client.verify_networks(cluster_id, networks)
        self.assertEquals(200, changes.getcode())
        return json.loads(changes.read())

    @logwrap
    def _basic_provisioning(self, cluster_name, nodes_dict, port=5514):
        self._clean_clusters()
        cluster_id = self._create_cluster(name=cluster_name)

        # Here we updating cluster editable attributes
        # In particular we set extra syslog server
        response = self.nailgun_client.get_cluster_attributes(cluster_id)
        attrs = json.loads(response.read())
        attrs["editable"]["syslog"]["syslog_server"]["value"] = \
            self.ci().get_host_node_ip()
        attrs["editable"]["syslog"]["syslog_port"]["value"] = port
        self.nailgun_client.update_cluster_attributes(cluster_id, attrs)

        node_names = []
        for role in nodes_dict:
            node_names += nodes_dict[role]
        if len(node_names) > 1:
            controller_amount = len(nodes_dict.get('controller', []))
            if controller_amount == 1:
                self.nailgun_client.update_cluster(cluster_id,
                                                   {"mode": "multinode"})
            if controller_amount > 1:
                self.nailgun_client.update_cluster(cluster_id, {"mode": "ha"})

        nodes = self._bootstrap_nodes(node_names)

        for node, role in self.get_nailgun_node_roles(nodes_dict):
            self.nailgun_client.update_node(node['id'], {"role": role,
                                                         "pending_addition": True})

        self._update_nodes_in_cluster(cluster_id, nodes)
        task = self._launch_provisioning(cluster_id)

        self._task_wait(task, 'Installation')

        logging.info("Checking role files on slave nodes")
        for node, role in self.get_nailgun_node_roles(nodes_dict):
            logging.debug("Trying to connect to %s via ssh" % node['ip'])
            ctrl_ssh = SSHClient(node['ip'], username='root', password='r00tme',
                                 private_keys=self.get_private_keys())
            logging.info("Checking /tmp/%s-file on %s" % (role, node['ip']))
            ret = ctrl_ssh.execute('test -f /tmp/%s-file' % role)
            self.assertEquals(ret['exit_code'], 0)
        return cluster_id

    @logwrap
    def get_nailgun_node_roles(self, nodes_dict):
        nailgun_node_roles = []
        for role in nodes_dict:
            for n in nodes_dict[role]:
                slave = self.ci().environment().node_by_name(n)
                node = self._get_slave_node_by_devops_node(slave)
                nailgun_node_roles.append((node, role))
        return nailgun_node_roles


    @logwrap
    def _launch_provisioning(self, cluster_id):
        """Return hash with task description."""
        logging.info(
            "Launching provisioning on cluster %d",
            cluster_id
        )
        changes = self.nailgun_client.update_cluster_changes(cluster_id)
        self.assertEquals(200, changes.getcode())
        return json.loads(changes.read())

    @logwrap
    def _task_wait(self, task, task_desc, timeout=70 * 60,
                   skip_error_status=False):

        start_time = time.time()
        logtimer = start_time
        ready = False

        while not ready:
            try:
                task = json.loads(
                    self.nailgun_client.get_task(task['id']).read()
                )
            except ValueError:
                task = {'status': 'running'}

            if task['status'] == 'ready':
                logging.info("Task %r complete" % task_desc)
                ready = True
            elif task['status'] == 'error' and skip_error_status:
                logging.info("Task %r failed with message: %s",
                             task_desc, task.get('message'))
                ready = True
            elif task['status'] == 'running':
                if (time.time() - start_time) > timeout:
                    raise Exception("Task %r timeout expired!" % task_desc)
                time.sleep(5)
            else:
                raise Exception("Task %s failed with status %r and msg: %s!" %
                                (task_desc, task['status'],
                                 task.get('message')))

            if (time.time() - logtimer) > 120:
                logtimer = time.time()
                logging.debug("Task %s status: %s progress: %s timer: %s",
                              task.get('id'),
                              task.get('status'),
                              task.get('progress'),
                              (time.time() - start_time))

        return task

    @logwrap
    def _upload_sample_release(self):
        release_id = self.nailgun_client.get_folsom_release_id()
        if not release_id:
            raise Exception("Not implemented uploading of release")
        return release_id

    @logwrap
    def _create_cluster(self, name='default',
                        release_id=None, net_manager="FlatDHCPManager"):
        if not release_id:
            release_id = self._upload_sample_release()

        cluster_id = self.nailgun_client.get_cluster_id(name)
        if not cluster_id:
            resp = self.nailgun_client.create_cluster(
                data={"name": name, "release": str(release_id)}
            )
            self.assertEquals(201, resp.getcode())
            cluster_id = self.nailgun_client.get_cluster_id(name)
            self.nailgun_client.update_cluster(cluster_id,
                                               {'net_manager': net_manager})
            if net_manager == "VlanManager":
                response = self.nailgun_client.get_networks(cluster_id)
                networks = json.loads(response.read())
                flat_net = [n for n in networks if n['name'] == 'fixed']
                flat_net[0]['amount'] = 8
                flat_net[0]['network_size'] = 16
                self.nailgun_client.update_network(cluster_id, flat_net)
        if not cluster_id:
            raise Exception("Could not get cluster '%s'" % name)
        return cluster_id

    @logwrap
    def _clean_clusters(self):
        clusters = json.loads(self.nailgun_client.list_clusters(
        ).read())
        for cluster in clusters:
            self.nailgun_client.update_cluster(
                cluster["id"], {"nodes": []}
            )

    @logwrap
    def _update_nodes_in_cluster(self, cluster_id, nodes):
        node_ids = [str(node['id']) for node in nodes]
        resp = self.nailgun_client.update_cluster(cluster_id,
                                                  {"nodes": node_ids})
        self.assertEquals(200, resp.getcode())
        cluster = json.loads(self.nailgun_client.get_cluster(cluster_id).read())
        nodes_in_cluster = [str(node['id']) for node in cluster['nodes']]
        self.assertEquals(sorted(node_ids), sorted(nodes_in_cluster))

    @logwrap
    def _get_slave_node_by_devops_node(self, devops_node):
        """Returns hash with nailgun slave node description if node
        registered itself on nailgun. Otherwise return None.
        """
        response = self.nailgun_client.list_nodes()
        nodes = json.loads(response.read())

        logging.debug("get_slave_node_by_devops_node: "
                      "found nodes: %s", str([n['mac'] for n in nodes]))

        for n in nodes:
            logging.debug("get_slave_node_by_devops_node: looking for %s",
                          n['mac'])
            for i in devops_node.interfaces:
                logging.debug("get_slave_node_by_devops_node: checking: %s",
                              str(i.mac_address))

                if n['mac'].capitalize() == i.mac_address.capitalize():
                    logging.debug("get_slave_node_by_devops_node: matched")
                    logging.debug("get_slave_node_by_devops_node: %s",
                                  json.dumps(n, indent=4))

                    n['devops_name'] = devops_node.name
                    return n
        logging.debug("get_slave_node_by_devops_node: node %s not found",
                      devops_node.name)
        return None

    @logwrap
    def _bootstrap_nodes(self, devops_node_names=None, timeout=600):
        """Start devops nodes and wait while they load boodstrap image
        and register on nailgun. Returns list of hashes with registred nailgun
        slave node descpriptions.
        """
        if not devops_node_names: devops_node_names = []
        timer = time.time()

        slaves = []
        for node_name in devops_node_names:
            slave = self.ci().environment().node_by_name(node_name)
            logging.info("Starting slave node %r", node_name)
            slave.start()
            slaves.append(slave)

        nodes = []
        full_nodes_len = len(slaves)
        while True:
            for slave in list(slaves):
                node = self._get_slave_node_by_devops_node(slave)
                if node is not None:
                    nodes.append(node)
                    slaves.remove(slave)
                    logging.debug("Node %s found", node['mac'])
                else:
                    logging.debug("Node %s not bootstrapped yet", slave.name)

            logging.debug("Bootstrapped nodes: %s",
                          str([n['mac'] for n in nodes]))
            if (time.time() - timer) > timeout:
                raise Exception("Bootstrap nodes discovery failed by timeout."
                                " Nodes: %s" %
                                ', '.join([n.name for n in slaves]))

            if len(nodes) == full_nodes_len:
                break

            logging.info("Waiting bootstraping slave nodes: timer: %s",
                         (time.time() - timer))
            time.sleep(15)

        return nodes

    @logwrap
    def _check_cluster_status(self, ip, smiles_count, networks_count=1):

        logging.info("Checking cluster status: ip=%s smiles=%s networks=%s",
                     ip, smiles_count, networks_count)

        ctrl_ssh = SSHClient(ip, username='root', password='r00tme',
                             private_keys=self.get_private_keys())
        ret = ctrl_ssh.execute('/usr/bin/nova-manage service list')
        nova_status = (
            (ret['exit_code'] == 0)
            and (''.join(ret['stdout']).count(":-)") == smiles_count)
            and (''.join(ret['stdout']).count("XXX") == 0)
        )
        if not nova_status:
            logging.warn("Nova check fails:\n%s" % ret['stdout'])
        ret = ctrl_ssh.execute('. /root/openrc; glance index')
        cirros_status = (
            (ret['exit_code'] == 0)
            and (''.join(ret['stdout']).count("TestVM") == 1)
        )
        if not cirros_status:
            logging.warn("Cirros check fails:\n%s" % ret['stdout'])
        ret = ctrl_ssh.execute('/usr/bin/nova-manage network list')
        nets_status = (
            (ret['exit_code'] == 0)
            and (len(ret['stdout']) == networks_count + 1)
        )
        if not nets_status:
            logging.warn("Networks check fails:\n%s" % ret['stdout'])
        return (nova_status and
                cirros_status and
                nets_status and
                self.logserver.get_status()
        )

    @logwrap
    def get_private_keys(self):
        keys = []
        for key_string in ['/root/.ssh/id_rsa', '/root/.ssh/bootstrap.rsa']:
            with self.remote().open(key_string) as f:
                keys.append(RSAKey.from_private_key(f))
        return keys

