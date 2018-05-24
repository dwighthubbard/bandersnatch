"""
Blacklist management
"""
import logging
import pkg_resources
from collections import defaultdict
from .configuration import BandersnatchConfig


logger = logging.getLogger(__name__)
loaded_filter_plugins = defaultdict(list)


class Filter(object):
    """
    Base Filter class
    """
    name = 'filter'

    def __init__(self, *args, **kwargs):
        self.configuration = BandersnatchConfig().config
        self.initialize_plugin()

    def initialize_plugin(self):
        """
        Code to initialize the plugin
        """
        pass

    def check_match(self, **kwargs):
        """
        Check if the plugin matches based on the arguments provides.

        Returns
        =======
        bool:
            True if the values match a filter rule, False otherwise
        """
        return False


class FilterProjectPlugin(Filter):
    """
    Plugin that blocks sync operations for an entire project
    """
    name = 'project_plugin'


class FilterReleasePlugin(Filter):
    """
    Plugin that blocks the download of specific release files
    """
    name = 'release_plugin'


def load_filter_plugins(entrypoint_group):
    """
    Load all blacklist plugins that are registered with pkg_resources

    Parameters
    ==========
    entrypoint_group: str
        The entrypoint group name to load plugins from

    Returns
    =======
    List of Blacklist:
        A list of objects derived from the Blacklist class
    """
    global loaded_filter_plugins
    enabled_plugins = ['all']
    config = BandersnatchConfig().config
    try:
        config_blacklist_plugins = config['blacklist']['plugins']
    except KeyError:
        config_blacklist_plugins = None
    if config_blacklist_plugins:
        config_plugins = []
        for plugin in config_blacklist_plugins.split('\n'):
            plugin = plugin.strip()
            if plugin:
                config_plugins.append(plugin)
        if config_plugins:
            enabled_plugins = config_plugins

    # If the plugins for the entrypoint_group have been loaded return them
    cached_plugins = loaded_filter_plugins.get(entrypoint_group)
    if cached_plugins:
        return cached_plugins

    plugins = set()  # Use a set to prevent possible duplicates
    for entry_point in pkg_resources.iter_entry_points(group=entrypoint_group):
        plugin_class = entry_point.load()
        plugin_instance = plugin_class()
        if 'all' in enabled_plugins or plugin_instance.name in enabled_plugins:
            plugins.add(plugin_instance)

    loaded_filter_plugins[entrypoint_group] = list(plugins)

    return plugins


def filter_project_plugins():
    """
    Load and return the release filtering plugin objects

    Returns
    -------
    list of bandersnatch.filter.Filter:
        List of objects drived from the bandersnatch.filter.Filter class
    """
    return load_filter_plugins('bandersnatch_filter_plugins.project')


def filter_release_plugins():
    """
    Load and return the release filtering plugin objects

    Returns
    -------
    list of bandersnatch.filter.Filter:
        List of objects drived from the bandersnatch.filter.Filter class
    """
    return load_filter_plugins('bandersnatch_filter_plugins.release')


def is_project_filtered(name: str) -> bool:
    """
    Check if a project/package name is filtered

    Parameters
    ----------
    name: str
        The normalized name of the package to check for filtering

    Returns
    -------
    bool:
        True if the package should be filtered False otherwise

    """
    for plugin in filter_project_plugins():
        if plugin.check_match(name=name):
            logger.debug(f'MATCH: Project {name!r} is filtered')
            return True
    return False