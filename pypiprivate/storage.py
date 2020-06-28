import os
import errno
import shutil
import mimetypes
import logging

import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


def guess_content_type(path, default='application/octet-stream'):
    ctype = mimetypes.guess_type(path)[0] or default
    logger.debug('Guessed ctype of "{0}": "{1}"'.format(path, ctype))
    return ctype


class StorageException(Exception):
    pass


class PathNotFound(StorageException):
    pass


class Storage(object):

    def join_path(self, *args):
        raise NotImplementedError

    def listdir(self, path):
        raise NotImplementedError

    def path_exists(self, path):
        raise NotImplementedError

    def put_contents(self, contents, dest, sync=False):
        raise NotImplementedError

    def put_file(self, src, dest, sync=False):
        raise NotImplementedError


class LocalFileSystemStorage(Storage):

    def __init__(self, base_path):
        self.base_path = base_path

    @classmethod
    def from_config(cls, config):
        storage_config = config.storage_config
        return cls(storage_config['base_path'])

    def join_path(self, *args):
        return os.path.join(*args)

    def listdir(self, path):
        path = self.join_path(self.base_path, path)
        try:
            entries = os.listdir(path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise PathNotFound('Path {0} not found'.format(path))
            raise e
        return [
            ('{}/'.format(entry) if os.path.isdir(entry) else entry)
            for entry in entries]

    def path_exists(self, path):
        path = self.join_path(self.base_path, path)
        return os.path.exists(path)

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

    def put_file(self, src, dest, sync=False):
        dest_path = self.join_path(self.base_path, dest)
        self.ensure_dir(os.path.dirname(dest_path))
        shutil.copy(src, dest_path)
        return dest_path

    def __repr__(self):
        return (
            '<LocalFileSystemStorage(base_path="{0}")>'
        ).format(self.base_path)


class AWSS3Storage(Storage):

    def __init__(self, bucket, acl, creds=None, prefix=None,
                 endpoint=None, region=None):
        if creds:
            logger.info('S3 Auth: using explicitly passed credentials')
            access_key, secret_key, session_token = creds
            session = boto3.Session(aws_access_key_id=access_key,
                                    aws_secret_access_key=secret_key,
                                    aws_session_token=session_token)
        else:
            logger.info('S3 Auth: using default boto3 methods')
            session = boto3.Session()
        self.endpoint = endpoint
        self.region = region
        kwargs = dict()
        if endpoint is not None:
            kwargs['endpoint_url'] = endpoint
        if region is not None:
            kwargs['region_name'] = region
        self.s3 = s3 = session.resource('s3', **kwargs)
        self.bucket = s3.Bucket(bucket)
        self.prefix = prefix
        self.acl = acl

    @classmethod
    def from_config(cls, config):
        storage_config = config.storage_config
        env = config.env
        bucket = storage_config['bucket']
        prefix = storage_config.get('prefix')
        acl = storage_config.get('acl', 'private')
        endpoint = storage_config.get('endpoint', None)
        region = storage_config.get('region', None)
        # Following 2 are the required env vars for s3 auth. If any of
        # these are not set, we try using the default boto3 methods
        # (same as the ones that AWS CLI and other tools support)
        pp_cred_keys = ['PP_S3_ACCESS_KEY', 'PP_S3_SECRET_KEY']
        if all([(k in env) for k in pp_cred_keys]):
            logger.debug('PP_S3_* env vars found: using them for auth')
            creds = (env['PP_S3_ACCESS_KEY'],
                     env['PP_S3_SECRET_KEY'],
                     env.get('PP_S3_SESSION_TOKEN', None))
        else:
            logger.debug((
                'PP_S3_* env vars not found: '
                'Falling back to default methods supported by boto3'
            ))
            creds = None
        return cls(bucket, acl, creds=creds, prefix=prefix,
                   endpoint=endpoint, region=region)

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
        dirs = [cp['Prefix'][len(s3_prefix):] for cp in dir_objs]
        return files + dirs

    def path_exists(self, path):
        path = self.prefixed_path(path)
        logger.debug('Checking if key exists: {0}'.format(path))
        client = self.s3.meta.client
        try:
            client.head_object(Bucket=self.bucket.name, Key=path)
        except ClientError as e:
            logger.debug('Handled ClientError: {0}'.format(e))
            return False
        else:
            return True

    def put_contents(self, contents, dest, sync=False):
        dest_path = self.prefixed_path(dest)
        client = self.s3.meta.client
        logger.debug('Writing content to s3: {0}'.format(dest_path))
        client.put_object(Bucket=self.bucket.name,
                          Key=dest_path,
                          Body=contents.encode('utf-8'),
                          ContentType=guess_content_type(dest),
                          ACL=self.acl)
        if sync:
            waiter = client.get_waiter('object_exists')
            waiter.wait(Bucket=self.bucket.name, Key=dest_path)

    def put_file(self, src, dest, sync=False):
        dest_path = self.prefixed_path(dest)
        client = self.s3.meta.client
        logger.debug('Uploading file to s3: {0} -> {1}'.format(src, dest_path))
        with open(src, 'rb') as f:
            client.put_object(Bucket=self.bucket.name,
                              Key=dest_path,
                              Body=f,
                              ContentType=guess_content_type(dest),
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
        return LocalFileSystemStorage.from_config(config)
    elif config.storage == 'aws-s3':
        return AWSS3Storage.from_config(config)
    elif config.storage == 'azure':
        from pypiprivate.azure import AzureBlobStorage
        return AzureBlobStorage.from_config(config)
    else:
        raise ValueError('Unsupported storage "{0}"'.format(config.storage))
