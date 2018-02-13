import os
import re
import logging

from .storage import PathNotFound

from jinja2 import Environment


logger = logging.getLogger(__name__)


class PackageAlreadyExists(Exception):
    pass


def _filter_pkg_dists(dists, pkg_name, pkg_ver):
    pkg_ver_str = re.sub('-', '_', pkg_ver)
    prefix = '{0}-{1}'.format(pkg_name, pkg_ver_str)
    return (d for d in dists if d.startswith(prefix))


def find_pkg_dists(project_path, dist_dir, pkg_name, pkg_ver):
    dist_dir = os.path.join(project_path, dist_dir)
    dists = _filter_pkg_dists(os.listdir(dist_dir), pkg_name, pkg_ver)
    dists = ({'pkg': pkg_name,
             'artifact': f,
              'path': os.path.join(dist_dir, f)}
             for f in dists)
    return dists


def build_index(title, items, index_type='root'):
    tmpl = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
</head>
<body>
    {%- if index_type != 'root' %}
    <h1>{{title}}</h1>
    {% endif -%}
    {% for item in items %}
    <a href="{{item}}">{{item}}</a><br>
    {% endfor %}
</body>
</html>
"""
    env = Environment()
    template = env.from_string(tmpl)
    return template.render(title=title, items=items,
                           index_type=index_type)


def is_already_published(storage, pkg_name, pkg_ver):
    logger.info('Ensuring that the package is not already published..')
    try:
        dists = storage.listdir(pkg_name)
    except PathNotFound:
        return False
    else:
        return any(_filter_pkg_dists(dists, pkg_name, pkg_ver))


def upload_dist(storage, dist):
    logger.info('Uploading dist: {0}'.format(dist['artifact']))
    dest = storage.join_path(dist['pkg'], dist['artifact'])
    storage.put_file(dist['path'], dest, sync=True)


def update_pkg_index(storage, pkg_name):
    logger.info('Updating index for package: {0}'.format(pkg_name))
    dists = [d for d in storage.listdir(pkg_name) if d != 'index.html']
    title = 'Links for {0}'.format(pkg_name)
    index = build_index(title, dists, 'pkg')
    index_path = storage.join_path(pkg_name, 'index.html')
    storage.put_contents(index, index_path)


def update_root_index(storage):
    logger.info('Updating repository index')
    pkgs = sorted([p for p in storage.listdir('.') if p != 'index.html'])
    title = 'Private Index'
    index = build_index(title, pkgs, 'root')
    index_path = storage.join_path('index.html')
    storage.put_contents(index, index_path)


def publish_package(name, version, storage, project_path, dist_dir):
    if is_already_published(storage, name, version):
        raise PackageAlreadyExists((
            'Package already published: {0}=={1}'
        ).format(name, version))
    dists = find_pkg_dists(project_path, dist_dir, name, version)
    for dist in dists:
        upload_dist(storage, dist)
    update_pkg_index(storage, name)
    update_root_index(storage)
