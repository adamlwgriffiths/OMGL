from __future__ import absolute_import


class DescriptorMixin(object):
    """Mixin to enable runtime-added descriptors."""
    def __getattribute__(self, name):
        attr = super(DescriptorMixin, self).__getattribute__(name)
        if hasattr(attr, "__get__") and not callable(attr):
            return attr.__get__(self, self.__class__)
        else:
            return attr

    def __setattr__(self, name, value):
        try:
            attr = super(DescriptorMixin, self).__getattribute__(name)
            return attr.__set__(self, value)
        except AttributeError:
            return super(DescriptorMixin, self).__setattr__(name, value)


class GL_Object(object):
    def __init__(self, **kwargs):
        super(GL_Object, self).__init__()


class ManagedObject(GL_Object):
    _create_func = None
    _delete_func = None

    def __init__(self, handle=None, **kwargs):
        super(ManagedObject, self).__init__(handle=handle, **kwargs)
        self._create(handle)

    def _create(self, handle):
        if handle:
            self._handle = handle
        else:
            func = self._create_func
            if hasattr(self._create_func, 'wrappedOperation'):
                func = self._create_func.wrappedOperation

            if len(func.argNames) == 2:
                self._handle = self._create_func(1)
            elif len(func.argNames) == 1:
                self._handle = self._create_func(self._type)
            else:
                self._handle = self._create_func()

    def __del__(self):
        self._destroy()

    def _destroy(self):
        try:
            func = self._delete_func
            if hasattr(self._delete_func, 'wrappedOperation'):
                func = self._delete_func.wrappedOperation

            if len(func.argNames) > 2:
                self._delete_func(1, [self._handle])
            else:
                self._delete_func(self._handle)
            self._handle = None
        except:
            pass

    @property
    def handle(self):
        return self._handle


class BindableObject(GL_Object):
    _bind_function = None
    _target = None

    def __init__(self, **kwargs):
        super(BindableObject, self).__init__(**kwargs)

    def bind(self):
        func = self._bind_func
        if hasattr(self._bind_func, 'wrappedOperation'):
            func = self._bind_func.wrappedOperation

        if len(func.argNames) == 2:
            self._bind_func(self._target, self._handle)
        else:
            self._bind_func(self._handle)

    def unbind(self):
        func = self._bind_func
        if hasattr(self._bind_func, 'wrappedOperation'):
            func = self._bind_func.wrappedOperation

        if len(func.argNames) == 2:
            self._bind_func(self._target, 0)
        else:
            self._bind_func(0)

    def __enter__(self):
        self.bind()

    def __exit__(self, exc_type, exc_value, traceback):
        self.unbind()
