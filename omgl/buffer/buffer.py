from __future__ import absolute_import
import ctypes
from copy import copy
import numpy as np
from numpy.core.multiarray import int_asbuffer
from OpenGL import GL
from ..object import ManagedObject, BindableObject
from .buffer_pointer import BufferPointer
from ..texture.texture import BufferTexture
from .. import dtypes


class Buffer(BindableObject, ManagedObject):
    _create_func = GL.glGenBuffers
    _delete_func = GL.glDeleteBuffers
    _bind_func = GL.glBindBuffer
    _target = None
    _usage = GL.GL_STATIC_DRAW

    def __init__(self, data=None, shape=None, dtype=None, buffer=None, offset=0, usage=None):
        super(Buffer, self).__init__(handle=buffer.handle if buffer else None)
        if data is not None:
            data = np.array(data, dtype=dtype)
            self._nbytes = data.nbytes
            self._shape = shape or data.shape
            self._dtype = dtype or data.dtype
        else:
            if shape is None or dtype is None:
                raise ValueError('Invalid parameters')

            self._shape = shape
            self._dtype = dtype
            self._nbytes = self.size * np.dtype(dtype).itemsize

        self._offset = offset
        self._usage = usage or self._usage
        self._mapped_buffer = None

        if not self._nbytes:
            raise ValueError('Invalid parameters')

        if not buffer:
            with self:
                GL.glBufferData(self._target, self._nbytes, data, self._usage)
        elif data is not None:
            self.set_data(data)

    def get_data(self, offset=0, nbytes=None):
        nbytes = nbytes or (self._nbytes - offset)
        offset = offset + self._offset

        with self:
            data = GL.glGetBufferSubData(self._target, offset, nbytes)
        data = data.view(dtype=self._dtype)
        data.shape = self._shape
        return data

    def set_data(self, data, offset=0):
        offset = offset + self._offset
        with self:
            GL.glBufferSubData(self._target, offset, data.nbytes, data)

    def _ptr_to_np(self, ptr, access):
        func = ctypes.pythonapi.PyBuffer_FromMemory
        func.restype = ctypes.py_object

        buf = int_asbuffer(ptr, self._nbytes)
        buf = np.frombuffer(buf, self._dtype)

        buf.shape = self._shape
        mapped_buffer = MappedBuffer(buf, access=access)
        return mapped_buffer

    def map(self, access=GL.GL_READ_WRITE):
        if self._mapped_buffer is not None:
            raise ValueError('Buffer is already mapped')

        with self:
            ptr = GL.glMapBuffer(self._target, access)

        self._mapped_buffer = self._ptr_to_np(ptr, access)
        return self._mapped_buffer

    def unmap(self):
        if self._mapped_buffer is None:
            raise ValueError('Buffer not mapped')

        with self:
            GL.glUnmapBuffer(self._target)

        self._mapped_buffer = None

    @property
    def mapped_buffer(self):
        return self._mapped_buffer

    @property
    def target(self):
        return self._target

    @property
    def nbytes(self):
        return self._nbytes

    @property
    def usage(self):
        return self._usage

    @property
    def dtype(self):
        return self._dtype

    @property
    def shape(self):
        return self._shape

    @property
    def size(self):
        return reduce(lambda x,y: x*y, self._shape, 1)

    @property
    def itemsize(self):
        return np.dtype(self._format).itemsize

    @property
    def names(self):
        return np.dtype(self._dtype).names


class MappedBuffer(np.ndarray):
    def __new__(cls, input_array, access=None):
        obj = np.asarray(input_array)
        obj = obj.view(cls)
        obj.access = access
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.access = getattr(obj, 'access', None)

    def __setitem__(self, index, value):
        if self.access not in (GL.GL_WRITE_ONLY, GL.GL_READ_WRITE):
            raise ValueError("Mapped buffer is read only")
        super(MappedBuffer, self).__setitem__(index, value)

    def __setslice__(self, start, stop, value):
        if self.access not in (GL.GL_WRITE_ONLY, GL.GL_READ_WRITE):
            raise ValueError("Mapped buffer is read only")
        super(MappedBuffer, self).__setslice__(start, stop, value)

    def unmap(self):
        # TODO: somehow mark this buffer as unusable
        #self.data = None
        pass


class ArrayBufferMixin(object):
    _target = GL.GL_ARRAY_BUFFER

class ElementBufferMixin(object):
    _target = GL.GL_ELEMENT_ARRAY_BUFFER

class AtomicCounterBufferMixin(object):
    _target = GL.GL_ATOMIC_COUNTER_BUFFER

class CopyReadBufferMixin(object):
    _target = GL.GL_COPY_READ_BUFFER

class CopyWriteBufferMixin(object):
    _target = GL.GL_COPY_WRITE_BUFFER

class DrawIndirectBufferMixin(object):
    _target = GL.GL_DRAW_INDIRECT_BUFFER

class PixelPackBufferMixin(object):
    _target = GL.GL_PIXEL_PACK_BUFFER

class PixelUnpackBufferMixin(object):
    _target = GL.GL_PIXEL_UNPACK_BUFFER

class TextureBufferMixin(object):
    _target = GL.GL_TEXTURE_BUFFER

class TransformFeedbackBufferMixin(object):
    _target = GL.GL_TRANSFORM_FEEDBACK_BUFFER

class UniformBufferMixin(object):
    _target = GL.GL_UNIFORM_BUFFER


class ArrayBuffer(ArrayBufferMixin, Buffer):
    # TODO: add a bind method that binds the current buffer based on dtype size
    # TODO: add a bind method that binds sub-sections of the buffer based on complex dtypes
    def __init__(self, data=None, shape=None, dtype=None, buffer=None, offset=0, usage=None):
        super(ArrayBuffer, self).__init__(data=data, shape=shape, dtype=dtype, buffer=buffer, offset=offset, usage=usage)

        # create a list of pointers
        dtype = np.dtype(self._dtype)
        if dtype.names:
            # complex dtype
            self._pointers = dict(
                (name, BufferPointer.for_np_buffer(self, name))
                for name in dtype.names
            )
        else:
            # basic dtype
            self._pointers = [BufferPointer.for_np_buffer(self)]

    @property
    def pointers(self):
        return copy(self._pointers)

class ElementBuffer(ElementBufferMixin, Buffer):
    def render(self, primitive=GL.GL_TRIANGLES, start=None, count=None):
        count = count or self.size
        dtype = dtypes.for_dtype(self.dtype)
        gl_enum = dtype.gl_enum
        offset = (start or 0) * np.dtype(dtype.dtype).itemsize
        # convert to ctypes void pointer
        offset = ctypes.c_void_p(offset)
        with self:
            GL.glDrawElements(primitive, count, gl_enum, offset)

class AtomicCounterBuffer(AtomicCounterBufferMixin, Buffer):
    pass

class CopyReadBuffer(CopyReadBufferMixin, Buffer):
    pass

class CopyWriteBuffer(CopyWriteBufferMixin, Buffer):
    pass

class DrawIndirectBuffer(DrawIndirectBufferMixin, Buffer):
    pass

class PixelPackBuffer(PixelPackBufferMixin, Buffer):
    pass

class PixelUnpackBuffer(PixelUnpackBufferMixin, Buffer):
    pass

class TextureBuffer(TextureBufferMixin, Buffer):
    def __init__(self, data=None, shape=None, dtype=None, buffer=None, offset=0, usage=None, internal_format=None):
        super(TextureBuffer, self).__init__(data=data, shape=shape, dtype=dtype, buffer=buffer, offset=offset, usage=usage)

        # create the texture
        self._texture = BufferTexture(self, internal_format)

    @property
    def texture(self):
        return self._texture

class TransformFeedbackBuffer(TransformFeedbackBufferMixin, Buffer):
    pass

class UniformBuffer(UniformBufferMixin, Buffer):
    _usage = GL.GL_DYNAMIC_DRAW

class VertexBuffer(ArrayBuffer):
    pass

class IndexBuffer(ElementBuffer):
    pass
