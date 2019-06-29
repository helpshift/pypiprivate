import os
import re
import logging

from pkg_resources import packaging
from jinja2 import Environment


logger = logging.getLogger(__name__)


class DistNotFound(Exception):
    pass


def normalized_name(name):
    """Convert the project name to normalized form as per PEP-0503

    Refer: https://www.python.org/dev/peps/pep-0503/#id4
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def _filter_pkg_dists(dists, pkg_name, pkg_ver):
    regexp = re.compile(r'{0}-{1}[.-]'.format(pkg_name, pkg_ver))
    return filter(regexp.match, dists)


def find_pkg_dists(project_path, dist_dir, pkg_name, pkg_ver):
    dist_dir = os.path.join(project_path, dist_dir)
    logger.info('Looking for package dists in {0}'.format(dist_dir))
    dists = _filter_pkg_dists(os.listdir(dist_dir), pkg_name, pkg_ver)
    dists = [{'pkg': pkg_name,
              'normalized_name': normalized_name(pkg_name),
              'artifact': f,
              'path': os.path.join(dist_dir, f)}
             for f in dists]
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


def is_dist_published(storage, dist):
    path = storage.join_path(dist['normalized_name'], dist['artifact'])
    logger.info('Ensuring dist is not already published: {0}'.format(path))
    return storage.path_exists(path)


def upload_dist(storage, dist):
    logger.info('Uploading dist: {0}'.format(dist['artifact']))
    dest = storage.join_path(dist['normalized_name'], dist['artifact'])
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
    version = packaging.version.Version(version)
    dists = find_pkg_dists(project_path, dist_dir, name, version)
    if not dists:
        raise DistNotFound((
            'No package distribution found in path {0}'
        ).format(dist_dir))
    rebuild_index = False
    for dist in dists:
        if not is_dist_published(storage, dist):
            logger.info('Trying to publish dist: {0}'.format(dist['artifact']))
            upload_dist(storage, dist)
            rebuild_index = True
        else:
            logger.debug((
                'Dist already published: {0} [skipping]'
            ).format(dist['artifact']))
    if rebuild_index:
        logger.info('Updating index')
        update_pkg_index(storage, name)
        update_root_index(storage)
    else:
        logger.debug('No index update required as no new dists uploaded')
