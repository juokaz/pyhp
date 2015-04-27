class Reference(object):
    _immutable_fields_ = ['base_env', 'referenced']

    def __init__(self, base_env=None, referenced=None):
        self.base_env = base_env
        self.referenced = referenced

    def get_referenced_name(self):
        return self.referenced

    def get_value(self):
        name = self.get_referenced_name()
        return self.base_env.load(name)

    def put_value(self, value):
        name = self.get_referenced_name()
        self.base_env.store(name, value)
