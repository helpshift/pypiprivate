import os
import argparse
import logging

from . import __version__
from .config import Config
from .storage import load_storage
from .publish import publish_package


logger = logging.getLogger(__name__)


LOGGING_FORMAT = '[%(asctime)s] %(levelname)s %(name)s: %(message)s'


def log_level(verbosity):
    if verbosity == 1:
        return logging.INFO
    if verbosity > 1:
        return logging.DEBUG
    return logging.WARN


def cmd_publish(args):
    config = Config(args.conf_path, os.environ)
    storage = load_storage(config)
    return publish_package(args.pkg_name,
                           args.pkg_ver,
                           storage,
                           args.project_path,
                           args.dist_dir)


def main():
    parser = argparse.ArgumentParser(description=(
        'Script for publishing python package on private pypi'
    ))
    parser.add_argument('--version', action='version',
                        version=__version__)
    parser.add_argument('-p', '--project-path', default='.',
                        help='Path to project [Default: current dir]')
    parser.add_argument('-c', '--conf-path', default='~/.pypi-private.cfg',
                        help='Path to config [Default: ~/.pypi-private.cfg]')
    parser.add_argument('-v', '--verbose', default=1, action='count')

    subparsers = parser.add_subparsers(help='subcommand help')

    publish = subparsers.add_parser('publish', help='Publish package')
    publish.add_argument('-d', '--dist-dir', default='dist',
                         help='Directory to look for built distributions')
    publish.add_argument('pkg_name')
    publish.add_argument('pkg_ver')
    publish.set_defaults(func=cmd_publish)

    args = parser.parse_args()

    logging.basicConfig(format=LOGGING_FORMAT)

    logging.getLogger('pypiprivate').setLevel(log_level(args.verbose))

    try:
        args.func(args)
    except AttributeError:
        parser.print_help()
        return 1

    return 0
