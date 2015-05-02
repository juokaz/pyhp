class Reference(object):
    _immutable_fields_ = ['varmap', 'referenced']

    def __init__(self, varmap, referenced):
        self.varmap = varmap
        self.referenced = referenced

    def get_referenced_name(self, identifier=None):
        if identifier is not None:
            return identifier
        return self.referenced

    def get_value(self, identifier=None):
        from pyhp.frame import BaseVarMap
        assert isinstance(self.varmap, BaseVarMap)
        varmap = self.varmap
        name = self.get_referenced_name(identifier)
        value = varmap.load(name)

        if value is None:
            raise Exception("Variable %s is not set" % name)
        else:
            return value

    def put_value(self, value, identifier=None):
        from pyhp.frame import BaseVarMap
        assert isinstance(self.varmap, BaseVarMap)
        varmap = self.varmap
        name = self.get_referenced_name(identifier)
        varmap.store(name, value)
