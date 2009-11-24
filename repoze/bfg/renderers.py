import os
import pkg_resources

from repoze.bfg.interfaces import ITemplateRenderer

from repoze.bfg.compat import json
from repoze.bfg.path import caller_package
from repoze.bfg.settings import get_settings
from repoze.bfg.threadlocal import get_current_registry

# concrete renderer factory implementations

def json_renderer_factory(name):
    def _render(value, system):
        return json.dumps(value)
    return _render

def string_renderer_factory(name):
    def _render(value, system):
        if not isinstance(value, basestring):
            value = str(value)
        return value
    return _render

# utility functions

def template_renderer_factory(spec, impl):
    reg = get_current_registry()
    if os.path.isabs(spec):
        # 'spec' is an absolute filename
        if not os.path.exists(spec):
            raise ValueError('Missing template file: %s' % spec)
        renderer = reg.queryUtility(ITemplateRenderer, name=spec)
        if renderer is None:
            renderer = impl(spec)
            reg.registerUtility(renderer, ITemplateRenderer, name=spec)
    else:
        # spec is a package:relpath resource spec
        renderer = reg.queryUtility(ITemplateRenderer, name=spec)
        if renderer is None:
            # service unit tests by trying the relative path string as
            # the utility name directly
            renderer = reg.queryUtility(ITemplateRenderer, name=spec)
        if renderer is None:
            try:
                package_name, filename = spec.split(':', 1)
            except ValueError:
                # unit test or someone passing a relative pathname
                package_name = caller_package(4).__name__
                filename = spec
            if not pkg_resources.resource_exists(package_name, filename):
                raise ValueError('Missing template resource: %s' % spec)
            abspath = pkg_resources.resource_filename(package_name, filename)
            renderer = impl(abspath)
            if not _reload_resources():
                # cache the template
                reg.registerUtility(renderer, ITemplateRenderer, name=spec)
        
    return renderer

def renderer_from_name(path):
    from repoze.bfg.configuration import Configurator
    reg = get_current_registry()
    config = Configurator(reg)
    return config._renderer_from_name(path)

def _reload_resources():
    settings = get_settings()
    return settings and settings.get('reload_resources')
