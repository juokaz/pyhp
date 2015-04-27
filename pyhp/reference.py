class Reference(object):
    _immutable_fields_ = ['varmap', 'referenced']

    def __init__(self, varmap, referenced):
        from pyhp.frame import BaseVarMap
        assert isinstance(varmap, BaseVarMap)
        self.varmap = varmap
        self.referenced = referenced

    def get_referenced_name(self):
        return self.referenced

    def get_value(self):
        name = self.get_referenced_name()
        varmap = self.varmap
        return varmap.load(name)

    def put_value(self, value):
        name = self.get_referenced_name()
        varmap = self.varmap
        varmap.store(name, value)
