import os

from flask import Blueprint
from werkzeug.middleware.dispatcher import DispatcherMiddleware

import mapadroid.utils.pluginBase
from mapadroid.madmin.functions import get_geofences, generate_coords_from_geofence

from prometheus_client import make_wsgi_app
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, InfoMetricFamily, REGISTRY

class MADCollector(object):
    """Collect useful metrics to export via a Prometheus /metrics endpoint.
    """
    def __init__(self, mad, devmode):
        self.metrics = {}
        self.devmode = devmode

        self._mad = mad
        self._logger = mad['logger']
        self._db = mad['db_wrapper']
        self._mapping_manager = mad['mapping_manager']
        self._mitm_mapper = mad['mitm_mapper']
        self._data_manager = mad['data_manager']
        self._madmin = mad['madmin']
        self._ws_server = mad['ws_server']
        self._jobstatus = mad['jobstatus']


    def get_pokestop_metrics(self):
        if not self._mapping_manager or not self._data_manager or not self._db:
            return

        self.metrics['area_count'] = GaugeMetricFamily('mad_area_count', 'Number of areas defined', labels=['type'])
        self.metrics['area_pokestop_count'] = GaugeMetricFamily('mad_area_pokestop_count', 'Number of pokestops', labels=['area'])
        self.metrics['area_quest_count'] = GaugeMetricFamily('mad_area_quest_count', 'Number of quests', labels=['area'])

        pokestop_areas = get_geofences(self._mapping_manager, self._data_manager, fence_type="pokestops")
        processed_fences = []
        self.metrics['area_count'].add_metric(['pokestops'], len(pokestop_areas))

        for possible_fence in pokestop_areas:
            for subfence in pokestop_areas[possible_fence]['include']:
                if subfence in processed_fences:
                    continue
                processed_fences.append(subfence)
                fence = generate_coords_from_geofence(self._mapping_manager, self._data_manager, subfence)

                self.metrics['area_pokestop_count'].add_metric([subfence], len(self._db.stops_from_db(fence=fence)))
                self.metrics['area_quest_count'].add_metric([subfence], len(self._db.quests_from_db(fence=fence)))

    def get_device_metrics(self):
        if not self._mapping_manager or not self._mitm_mapper:
            return

        self.metrics['device_count'] = GaugeMetricFamily('mad_device_count', 'Number of defined device origins')
        self.metrics['device_injection_status'] = GaugeMetricFamily('mad_device_injection_status', 'Boolean for whether injection is active', labels=['origin', 'scanmode'])
        self.metrics['device_latest_data_timestamp'] = GaugeMetricFamily('mad_device_latest_data_timestamp', 'Timestamp of latest data received from device', labels=['origin', 'scanmode'])

        devices = self._mapping_manager.get_all_devicemappings()
        self.metrics['device_count'].add_metric(value=len(devices), labels=[])
        for origin in devices.keys():
            settings = self._mitm_mapper.request_latest(origin, 'injected_settings')['values']['scanmode']
            scanmode = settings['values']['scanmode']

            self.metrics['device_injection_status'].add_metric([origin, scanmode], int(self.__mitm_mapper.get_injection_status(origin)))
            self.metrics['device_latest_data_timestamp'].add_metric([origin, scanmode], self.__mitm_mapper.request_latest(origin, 'timestamp_last_data'))
            # origin_return[origin][
            #     'last_possibly_moved'] = self.__mitm_mapper.get_last_timestamp_possible_moved(origin)

    def collect(self):
        """Run every time the endpoint is queried. All metrics are yielded.
        """
        # reset metrics to avoid stale data
        self.metrics = {}

        # Run sub-processing functions that will populate the metrics with current values
        self.get_pokestop_metrics()
        self.get_device_metrics()

        # yield all the metrics
        for metric in self.metrics:
            yield self.metrics[metric]

        # When in devmode, export dummy metrics for exploring available internal objects
        if self.devmode:
            objs = []
            for name, obj in self._mad.items():
                if obj:
                    objs.append((name, obj))
            for name, obj in objs:
                value = str(dir(obj))
                yield InfoMetricFamily(f'mad_dev_{name}_dir', value)


class PrometheusExporter(mapadroid.utils.pluginBase.Plugin):
    """This plugin is just the identity function: it returns the argument
    """
    def __init__(self, mad):
        super().__init__(mad)

        self._rootdir = os.path.dirname(os.path.abspath(__file__))

        self._mad = mad
        self._logger = mad['logger']

        self._pluginconfig.read(self._rootdir + "/plugin.ini")
        self._versionconfig.read(self._rootdir + "/version.mpl")
        self.author = self._versionconfig.get("plugin", "author", fallback="unknown")
        self.url = self._versionconfig.get("plugin", "url", fallback="https://www.maddev.eu")
        self.description = self._versionconfig.get("plugin", "description", fallback="unknown")
        self.version = self._versionconfig.get("plugin", "version", fallback="unknown")
        self.pluginname = self._versionconfig.get("plugin", "pluginname", fallback="https://www.maddev.eu")
        self.staticpath = self._rootdir + "/static/"
        self.templatepath = self._rootdir + "/template/"

        self._routes = [
            # We only expose documentation here.
            # /metrics also exists but is handled via middleware instead of as a static route.
            ("/metrics_readme", self.readme_route),
        ]

        self._hotlink = [
            ("Metrics README", "metrics_readme", "Documentation on using available metrics"),
        ]

        if self._pluginconfig.getboolean("plugin", "active", fallback=False):
            self._plugin = Blueprint(str(self.pluginname), __name__, static_folder=self.staticpath,
                                     template_folder=self.templatepath)

            for route, view_func in self._routes:
                self._plugin.add_url_rule(route, route.replace("/", ""), view_func=view_func)

            for name, link, description in self._hotlink:
                self._mad['madmin'].add_plugin_hotlink(name, self._plugin.name + "." + link.replace("/", ""),
                                                       self.pluginname, self.description, self.author, self.url,
                                                       description, self.version)

            # register separate wsgi app to handle the metrics endpoint
            app = self._mad['madmin']._app
            app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
                '/metrics': make_wsgi_app()
            })


    def perform_operation(self):
        """The actual implementation of the identity plugin is to just return the
        argument
        """

        # do not change this part ▽▽▽▽▽▽▽▽▽▽▽▽▽▽▽
        if not self._pluginconfig.getboolean("plugin", "active", fallback=False):
            return False
        self._mad['madmin'].register_plugin(self._plugin)
        # do not change this part △△△△△△△△△△△△△△△

        # Since most of the work is done during endpoint requests, we just register the
        # custom collector class to the Prometheus client library here.
        # TODO(artanicus): Certain errors can cause this to hang and kill MAD startup without any logs being emitted. -_-
        self._logger.info('Registering Prometheus metrics..')
        devmode = self._pluginconfig.getboolean("plugin", "devmode", fallback=False)
        REGISTRY.register(MADCollector(mad=self._mad, devmode=devmode))

        return 'Registration great success.'

    def readme_route(self):
        return 'Hello Kitty :3'
