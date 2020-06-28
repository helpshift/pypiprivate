import logging
import os

from azure.storage.blob import BlobServiceClient, ContentSettings

from pypiprivate.storage import Storage, guess_content_type

logger = logging.getLogger(__name__)


class AzureBlobClientMixin(object):

    def __init__(self, connection_string, container):
        super().__init__()
        self._connection_string = connection_string
        self._container = container
        self._blob_service_client = None
        self._container_client = None

    @property
    def container(self):
        return self._container

    @property
    def blob_service_client(self):
        if self._blob_service_client:
            return self._blob_service_client
        self._blob_service_client = BlobServiceClient.from_connection_string(self._connection_string)
        return self._blob_service_client

    @property
    def container_client(self):
        if self._container_client:
            return self._container_client
        self._container_client = self.get_container_client(self._container)
        return self._container_client

    def get_container_client(self, container_name):
        return self.blob_service_client.get_container_client(container_name)


class AzureBlobStorage(Storage, AzureBlobClientMixin):

    def __init__(self, connection_string, container, prefix=None):
        super().__init__(connection_string, container)
        self.prefix = prefix

    @classmethod
    def from_config(cls, config):
        storage_config = config.storage_config
        container = storage_config['container']
        conn_str = config.env['PP_AZURE_CONN_STR']
        prefix = storage_config.get('prefix')
        return cls(conn_str, container, prefix=prefix)

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
            prefix = '{0}/'.format(path)
        else:
            prefix = path
        logger.debug('Listing objects prefixed with: {0}'.format(prefix))
        blobs = self.container_client.list_blobs(name_starts_with=prefix)
        files = [b.name[len(prefix):] for b in blobs]
        dirs = list({os.path.dirname(f) for f in files})
        return files + dirs

    def path_exists(self, path):
        path = self.prefixed_path(path)
        logger.debug('Checking if key exists: {0}'.format(path))
        return bool(list(self.container_client.list_blobs(name_starts_with=path)))

    def put_contents(self, contents, dest, sync=False):
        dest_path = self.prefixed_path(dest)
        logger.debug('Writing content to azure: {0}'.format(dest_path))
        content_settings = ContentSettings(content_type=guess_content_type(dest))
        self.container_client.upload_blob(name=dest_path, data=contents.encode('utf-8'),
                                          overwrite=True, content_settings=content_settings)

    def put_file(self, src, dest, sync=False):
        dest_path = self.prefixed_path(dest)
        logger.debug('Writing content to azure: {0}'.format(dest_path))
        content_settings = ContentSettings(content_type=guess_content_type(dest))
        with open(src, "rb") as data:
            self.container_client.upload_blob(name=dest_path, data=data,
                                              overwrite=True, content_settings=content_settings)

