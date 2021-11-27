import os

from flask import Blueprint
from werkzeug.middleware.dispatcher import DispatcherMiddleware

import mapadroid.utils.pluginBase
from mapadroid.madmin.functions import auth_required

from prometheus_client import make_wsgi_app
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, InfoMetricFamily, REGISTRY

class MADCollector(object):
    """Collect useful metrics to export.
    """
    def __init__(self, mad):
        self._mad = mad

    def collect(self):
        yield GaugeMetricFamily('my_gauge', 'Help text', value=7)
        c = CounterMetricFamily('my_counter_total', 'Help text', labels=['foo'])
        c.add_metric(['bar'], 1.7)
        c.add_metric(['baz'], 3.8)
        yield c
        yield InfoMetricFamily('madmin_state', str(dir(self._mad['madmin'].statistics)))
        yield InfoMetricFamily('mad_statistics_stop_quest', str(self._mad['madmin'].statistics.get_stop_quest_stats_data()))


class PrometheusExporter(mapadroid.utils.pluginBase.Plugin):
    """This plugin is just the identity function: it returns the argument
    """
    def __init__(self, mad):
        super().__init__(mad)

        self._rootdir = os.path.dirname(os.path.abspath(__file__))

        self._mad = mad

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

        REGISTRY.register(MADCollector(self._mad))

        return True

    @auth_required
    def readme_route(self):
        return 'Hello Kitty :3'
