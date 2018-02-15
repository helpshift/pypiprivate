import os
from ConfigParser import SafeConfigParser


class Config(object):

    def __init__(self, path, env):
        self.path = os.path.expanduser(path)
        self.env = env
        self.c = SafeConfigParser()
        with open(self.path) as f:
            self.c.readfp(f)

    @property
    def storage(self):
        return self.c.get('storage', 'type')

    @property
    def storage_config(self):
        return dict(self.c.items(self.storage))
