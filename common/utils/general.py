class ClsHelper:

    def list_properties(self, exclude_private=True):
        """
        去掉所有内置（非对象）属性

        exclude_private：去掉私有属性
        """
        result = dict()
        for key, value in self.__class__.__dict__.items():
            if not callable(value):
                satisfied = not key.startswith('_') if exclude_private else not key.startswith('__')
                if satisfied:
                    result[key] = value
        return result

    def all_values(self, exclude_private=True):
        dic = self.list_properties(exclude_private=exclude_private)
        values = list()
        for k, v in dic.items():
            values.append(v)
        return values

    def all_keys(self, exclude_private=True):
        dic = self.list_properties(exclude_private=exclude_private)
        values = list()
        for k, v in dic.items():
            values.append(k)
        return values

    def list_methods(self, exclude_private=True):
        result = dict()
        for key, value in self.__class__.__dict__.items():
            if callable(value):
                satisfied = not key.startswith('_') if exclude_private else not key.startswith('__')
                if satisfied:
                    result[key] = value
        return result
