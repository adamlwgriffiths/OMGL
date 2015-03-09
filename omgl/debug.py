from __future__ import absolute_import, print_function
from OpenGL import GL

class FunctionPrinter(object):
    def __init__(self, fn):
        self._original = fn

    def __call__(self, *args, **kwargs):
        # convert PyOpenGL constants from ints to strings for visualization
        pargs = map(lambda arg: repr(arg) if isinstance(arg, GL.constants.Constant) else arg, args)
        print('{}({}, {})'.format(self._original.__name__, pargs, kwargs))
        return self._original(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._original, name)

def function_printer(fn):
    func = FunctionPrinter(fn)
    for name in dir(fn):
        attr = getattr(fn, name)
        if name.startswith('__'):
            continue
        setattr(func, name, attr)
    return func

def print_gl_calls(enable=True):
    for name in dir(GL):
        # ignore normal module values
        if not name.startswith('gl'):
            continue

        func = getattr(GL, name)

        if enable:
            # already patched
            if hasattr(func, '_orig'):
                continue

            func = function_printer(func)
        else:
            if hasattr(func, '_orig'):
                continue
            func = func._orig
        setattr(GL, name, func)
