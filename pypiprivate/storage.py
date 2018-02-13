import os
import errno
import shutil
import mimetypes
import logging

import boto3


logger = logging.getLogger(__name__)


class StorageException(Exception):
    pass


class PathNotFound(StorageException):
    pass


class Storage(object):

    def join_path(self, *args):
        raise NotImplementedError

    def listdir(self, path):
        raise NotImplementedError

    def put_contents(self, contents, dest, sync=False):
        raise NotImplementedError

    def put_file(self, src, dest, sync=False):
        raise NotImplementedError


class LocalFileSystemStorage(Storage):

    def __init__(self, config):
        self.base_path = config['base_path']

    def join_path(self, *args):
        return os.path.join(*args)

    def listdir(self, path):
        path = self.join_path(self.base_path, path)
        try:
            return os.listdir(path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise PathNotFound('Path {0} not found'.format(path))
            raise e

    def ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def put_contents(self, contents, dest, sync=False):
        dest_path = self.join_path(self.base_path, dest)
        self.ensure_dir(os.path.dirname(dest_path))
        with open(dest_path, 'w') as f:
            f.write(contents)
        # In LocalFileSystemStorage sync makes no sense
        return dest_path

    def put_file(self, src, dest):
        dest_path = self.join_path(self.base_path, dest)
        self.ensure_dir(os.path.dirname(dest_path))
        shutil.copy(src, dest_path)
        return dest_path

    def __repr__(self):
        return (
            '<LocalFileSystemStorage(base_path="{0}")>'
        ).format(self.base_path)


class AWSS3Storage(Storage):

    def __init__(self, config):
        self._config = config
        session = boto3.Session(aws_access_key_id=config['access_key'],
                                aws_secret_access_key=config['secret_key'])
        self.s3 = s3 = session.resource('s3')
        self.bucket = s3.Bucket(config['bucket'])
        self.prefix = config.get('prefix')
        self.acl = config.get('acl', 'private')

    def join_path(self, *args):
        return '/'.join(args)

    def prefixed_path(self, path):
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        if path != '.':
            parts.append(path)
        return self.join_path(*parts)

    def listdir(self, path):
        path = self.prefixed_path(path)
        if path != '' and not path.endswith('/'):
            s3_prefix = '{0}/'.format(path)
        else:
            s3_prefix = path
        logger.debug('Listing objects prefixed with: {0}'.format(s3_prefix))
        client = self.s3.meta.client
        paginator = client.get_paginator('list_objects')
        response = paginator.paginate(Bucket=self.bucket.name,
                                      Prefix=s3_prefix,
                                      Delimiter='/')
        file_objs = [c for c in response.search('Contents') if c]
        dir_objs = [cp for cp in response.search('CommonPrefixes') if cp]
        # If no objs found, it means the path doesn't exist
        if len(file_objs) == len(dir_objs) == 0:
            raise PathNotFound('Path {0} not found'.format(s3_prefix))
        files = (c['Key'][len(s3_prefix):] for c in file_objs)
        files = [f for f in files if f != '']
        dirs = [cp['Prefix'][len(s3_prefix):].rstrip('/') for cp in dir_objs]
        return files + dirs

    @staticmethod
    def _guess_content_type(path, default='application/octet-stream'):
        ctype = mimetypes.guess_type(path)[0] or default
        logger.debug('Guessed ctype of "{0}": "{1}"'.format(path, ctype))
        return ctype

    def put_contents(self, contents, dest, sync=False):
        dest_path = self.prefixed_path(dest)
        client = self.s3.meta.client
        logger.debug('Writing content to s3: {0}'.format(dest_path))
        client.put_object(Bucket=self.bucket.name,
                          Key=dest_path,
                          Body=contents.encode('utf-8'),
                          ContentType=self._guess_content_type(dest),
                          ACL=self.acl)
        if sync:
            waiter = client.get_waiter('object_exists')
            waiter.wait(Bucket=self.bucket.name, Key=dest_path)

    def put_file(self, src, dest, sync=False):
        dest_path = self.prefixed_path(dest)
        client = self.s3.meta.client
        logger.debug('Uploading file to s3: {0} -> {1}'.format(src, dest_path))
        with open(src) as f:
            client.put_object(Bucket=self.bucket.name,
                              Key=dest_path,
                              Body=f,
                              ContentType=self._guess_content_type(dest),
                              ACL=self.acl)
        if sync:
            waiter = client.get_waiter('object_exists')
            waiter.wait(Bucket=self.bucket.name, Key=dest_path)

    def __repr__(self):
        return (
            '<AWSS3Storage(bucket="{0}", prefix="{1}")>'
        ).format(self.bucket.name, self.prefix)


def load_storage(config):
    if config.storage == 'local-filesystem':
        return LocalFileSystemStorage(config.storage_config)
    elif config.storage == 'aws-s3':
        return AWSS3Storage(config.storage_config)
    else:
        raise ValueError('Unsupported storage "{0}"'.format(config.storage))
