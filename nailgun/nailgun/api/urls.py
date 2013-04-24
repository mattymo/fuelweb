# -*- coding: utf-8 -*-

import web

from nailgun.api.handlers.cluster import ClusterHandler
from nailgun.api.handlers.cluster import ClusterCollectionHandler
from nailgun.api.handlers.cluster import ClusterChangesHandler
from nailgun.api.handlers.cluster import ClusterVerifyNetworksHandler
from nailgun.api.handlers.cluster import ClusterSaveNetworksHandler
from nailgun.api.handlers.cluster import ClusterAttributesHandler
from nailgun.api.handlers.cluster import ClusterAttributesDefaultsHandler

from nailgun.api.handlers.release import ReleaseHandler
from nailgun.api.handlers.release import ReleaseCollectionHandler

from nailgun.api.handlers.node import NodeHandler
from nailgun.api.handlers.node import NodeCollectionHandler
from nailgun.api.handlers.node import NodeAttributesHandler
from nailgun.api.handlers.node import NodeAttributesDefaultsHandler
from nailgun.api.handlers.node import NodeAttributesByNameHandler

from nailgun.api.handlers.networks import NetworkCollectionHandler
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.api.handlers.tasks import TaskCollectionHandler

from nailgun.api.handlers.notifications import NotificationHandler
from nailgun.api.handlers.notifications import NotificationCollectionHandler

from nailgun.api.handlers.logs import LogEntryCollectionHandler
from nailgun.api.handlers.logs import LogPackageHandler
from nailgun.api.handlers.logs import LogSourceCollectionHandler
from nailgun.api.handlers.logs import LogSourceByNodeCollectionHandler

from nailgun.api.handlers.version import VersionHandler

urls = (
    r'/releases/?$',
    'ReleaseCollectionHandler',
    r'/releases/(?P<release_id>\d+)/?$',
    'ReleaseHandler',
    r'/clusters/?$',
    'ClusterCollectionHandler',
    r'/clusters/(?P<cluster_id>\d+)/?$',
    'ClusterHandler',
    r'/clusters/(?P<cluster_id>\d+)/changes/?$',
    'ClusterChangesHandler',
    r'/clusters/(?P<cluster_id>\d+)/attributes/?$',
    'ClusterAttributesHandler',
    r'/clusters/(?P<cluster_id>\d+)/attributes/defaults/?$',
    'ClusterAttributesDefaultsHandler',
    r'/clusters/(?P<cluster_id>\d+)/verify/networks/?$',
    'ClusterVerifyNetworksHandler',
    r'/clusters/(?P<cluster_id>\d+)/save/networks/?$',
    'ClusterSaveNetworksHandler',
    r'/nodes/?$',
    'NodeCollectionHandler',
    r'/nodes/(?P<node_id>\d+)/?$',
    'NodeHandler',
    r'/nodes/(?P<node_id>\d+)/attributes/?$',
    'NodeAttributesHandler',
    r'/nodes/(?P<node_id>\d+)/attributes/defaults/?$',
    'NodeAttributesDefaultsHandler',
    r'/nodes/(?P<node_id>\d+)/attributes/(?P<attr_name>[-\w]+)/?$',
    'NodeAttributesByNameHandler',
    r'/networks/?$',
    'NetworkCollectionHandler',
    r'/tasks/?$',
    'TaskCollectionHandler',
    r'/tasks/(?P<task_id>\d+)/?$',
    'TaskHandler',
    r'/notifications/?$',
    'NotificationCollectionHandler',
    r'/notifications/(?P<notification_id>\d+)/?$',
    'NotificationHandler',
    r'/logs/?$',
    'LogEntryCollectionHandler',
    r'/logs/package/?$',
    'LogPackageHandler',
    r'/logs/sources/?$',
    'LogSourceCollectionHandler',
    r'/logs/sources/nodes/(?P<node_id>\d+)/?$',
    'LogSourceByNodeCollectionHandler',
    r'/version/?$',
    'VersionHandler'
)

api_app = web.application(urls, locals())
