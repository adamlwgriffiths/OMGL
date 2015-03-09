from __future__ import absolute_import
import ctypes
from OpenGL import GL
import numpy as np
from .. import dtypes


class BufferPointer(object):
    @classmethod
    def for_np_buffer(cls, buffer, name=None):
        # create a list of pointers
        dtype = np.dtype(buffer.dtype)
        if name:
            # complex dtype
            offset = dtype.fields[name][1]
            count = reduce(lambda x,y: x*y, dtype[name].shape, 1)
            pointer = BufferPointer(buffer=buffer, count=count, stride=dtype.itemsize, offset=offset, dtype=dtype[name].base)
            return pointer
        else:
            pointer = BufferPointer(buffer=buffer, count=buffer.shape[-1], stride=dtype.itemsize, offset=0, dtype=dtype.base)
            return pointer

    def __init__(self, buffer, count=3, stride=0, offset=0, dtype=np.float32, normalize=False):
        self._buffer = buffer
        self.count = count
        self.stride = stride or (count * np.dtype(dtype).itemsize)
        self.offset = ctypes.c_void_p(offset) if offset else None
        self.dtype = dtype
        self.normalize = normalize

    def enable(self, location):
        dtype = dtypes.for_dtype(self.dtype)
        with self._buffer:
            GL.glEnableVertexAttribArray(location)
            if dtype.dtype == np.float64:
                # GL 4.1
                # doubles
                GL.glVertexAttribLPointer(location, self.count, dtype.gl_enum, self.stride, self.offset)
            elif np.issubdtype(dtype.dtype, np.integer):
                # GL 3.0
                # integrals
                GL.glVertexAttribIPointer(location, self.count, dtype.gl_enum, self.stride, self.offset)
            else:
                # all others
                GL.glVertexAttribPointer(location, self.count, dtype.gl_enum, self.normalize, self.stride, self.offset)

    def disable(self, location):
        GL.glDisableVertexAttribArray(location)

    @property
    def size(self):
        offset = 0
        if self.offset:
            offset = self.offset.value
        offset = offset - (offset % self.stride)
        return (self._buffer.nbytes - offset) / self.stride

    @property
    def buffer(self):
        return self._buffer

    def __str__(self):
        return '<{cls} {id} {count}, {stride}, {offset}, {dtype}, {normalize}>'.format(
            cls=self.__class__.__name__,
            id=self._buffer.handle,
            **self.__dict__
        )
