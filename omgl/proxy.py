from __future__ import absolute_import
from OpenGL import GL
import numpy as np

# TODO: add a cache value that caches mixin that caches the result

class Proxy(object):
    """Variable Proxy for OpenGL objects.
    """
    def __init__(self,
        getter=None, getter_args=None,
        setter=None, setter_args=None,
        dtype=None, bind=False, prepend_args=None,
    ):
        self._getter = getter
        self._getter_args = getter_args or []
        if not hasattr(self._getter_args, '__iter__'):
            self._getter_args = [self._getter_args]

        self._setter = setter
        self._setter_args = setter_args or []
        if not hasattr(self._setter_args, '__iter__'):
            self._setter_args = [self._setter_args]

        self._dtype = dtype
        self._bind = bind
        self._prepend_args = prepend_args or []

    def __get__(self, obj, cls):
        if not self._getter:
            raise AttributeError('Getting value not supported')

        args = self._get_args(obj, cls)
        if self._bind:
            with obj:
                value = self._getter(*args)
        else:
            value = self._getter(*args)
        return self._get_result(value)

    def _get_args(self, obj, cls):
        return [getattr(obj, arg) for arg in self._prepend_args] + self._getter_args

    def _get_result(self, value):
        if hasattr(value, '__iter__'):
            if self._dtype:
                value = value.view(dtype=self._dtype)
            value = [v.item() for v in value]
            if len(value) == 1:
                value = value[0]
        elif hasattr(value, 'value'):
            value = value.value
            if self._dtype:
                value = self._dtype(value)
        else:
            value = value.item()
            if self._dtype:
                value = self._dtype(value)
        return value

    def __set__(self, obj, value):
        if not self._setter:
            raise AttributeError('Setting value not supported')

        data = np.array(value, dtype=self._dtype)
        args = self._set_args(obj, data)
        if self._bind:
            with obj:
                self._setter(*args)
        else:
            self._setter(*args)

    def _set_args(self, obj, value):
        return [getattr(obj, arg) for arg in self._prepend_args] + self._setter_args + [value]


class BooleanProxy(Proxy):
    def __init__(self, *args, **kwargs):
        args = [GL.glGetBooleanv] + list(args)
        super(BooleanProxy, self).__init__(*args, **kwargs)

class Integer32Proxy(Proxy):
    def __init__(self, *args, **kwargs):
        args = [GL.glGetIntegerv] + list(args)
        super(Integer32Proxy, self).__init__(*args, **kwargs)

class Integer64Proxy(Proxy):
    def __init__(self, *args, **kwargs):
        args = [GL.glGetInteger64v] + list(args)
        super(Integer64Proxy, self).__init__(*args, **kwargs)

class Float32Proxy(Proxy):
    def __init__(self, *args, **kwargs):
        args = [GL.glGetFloatv] + list(args)
        super(Float32Proxy, self).__init__(*args, **kwargs)

class EnableDisableProxy(Proxy):
    def __init__(self, arg):
        super(EnableDisableProxy, self).__init__()
        self._arg = arg

    def __get__(self, obj, cls=None):
        with obj:
            return bool(GL.glIsEnabled(self._arg))

    def __set__(self, obj, value):
        with obj:
            GL.glEnable(self._arg) if value else GL.glDisable(self._arg)

class StringProxy(Proxy):
    def __init__(self, arg, bind=False):
        super(StringProxy, self).__init__()
        self._arg = arg
        self._bind = bind

    def __get__(self, obj, cls=None):
        if self._bind:
            with obj:
                return GL.glGetString(self._arg)
