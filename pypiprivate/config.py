import os
from ConfigParser import SafeConfigParser


class Config(object):

    def __init__(self, path):
        self.path = os.path.expanduser(path)
        self.c = SafeConfigParser()
        with open(self.path) as f:
            self.c.readfp(f)

    @property
    def storage(self):
        return self.c.get('storage', 'key')

    @property
    def storage_config(self):
        return {k: v for k, v in self.c.items(self.storage)}
