import os
import re
import logging
import hashlib

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


def sha256sum(filename):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)

    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])

    return h.hexdigest()


def _filter_pkg_dists(dists, pkg_name, pkg_ver):
    # Wheels have different naming conventions: https://www.python.org/dev/peps/pep-0491/#escaping-and-unicode
    # We want to account for both sdist and wheel naming.
    wheel_name = re.sub(r"[^\w\d.]+", "_", pkg_name, re.UNICODE)
    pkg_name_candidates = (pkg_name, wheel_name)
    pkg_ver = re.escape(str(pkg_ver))
    name_re_alternation = '|'.join((re.escape(candidate) for candidate in pkg_name_candidates))
    regexp = re.compile(r'({0})-{1}[.-]'.format(name_re_alternation, pkg_ver))
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
    <a href="{{item["name"]}}#{%- if item.get("sha256") %}sha256={{item["sha256"]}}{% endif -%}">
        {{item["name"]}}
    </a>
    <br>
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
    content_hash = sha256sum(dist['path'])
    logger.info('{0} sha256: {1}'.format(dist['artifact'], content_hash))
    storage.put_contents(content_hash, dest + '.sha256', sync=True)


def update_pkg_index(storage, pkg_name):
    logger.info('Updating index for package: {0}'.format(pkg_name))
    dists = [
        {
            "name": d,
            "sha256": storage.read_contents(
                storage.join_path(pkg_name, d) + '.sha256',
                raise_if_not_exist=False
            )
        }
        for d in storage.listdir(pkg_name)
        if d != 'index.html' and not d.endswith('.sha256')
    ]
    title = 'Links for {0}'.format(pkg_name)
    index = build_index(title, dists, 'pkg')
    index_path = storage.join_path(pkg_name, 'index.html')
    storage.put_contents(index, index_path)


def update_root_index(storage):
    logger.info('Updating repository index')
    pkgs = sorted(
        [{"name": p} for p in storage.listdir('.') if p != 'index.html'],
        key=lambda x: x["name"]
    )
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
        update_pkg_index(storage, dist['normalized_name'])
        update_root_index(storage)
    else:
        logger.debug('No index update required as no new dists uploaded')
