from __future__ import absolute_import
from OpenGL import GL
from ..object import DescriptorMixin
from ..buffer.vertex_array import VertexArray
from ..buffer.buffer_pointer import BufferPointer


class Mesh(DescriptorMixin):
    def __init__(self, pipeline, indices=None, primitive=GL.GL_TRIANGLES, **pointers):
        self._pointers = pointers
        self._pipeline = pipeline
        self.primitive = primitive
        self.indices = indices

        for pointer in pointers.values():
            if not isinstance(pointer, BufferPointer):
                raise ValueError('Must be of type BufferPointer')

        self._vertex_array = VertexArray()
        self._bind_pointers()

    def _bind_pointers(self):
        # TODO: make this more efficient, don't just clear all pointers
        self._vertex_array.clear()

        # assign our pointers to the vertex array
        for name, pointer in self._pointers.items():
            if not isinstance(pointer, BufferPointer):
                raise ValueError('Must be a buffer pointer')

            attribute = self._pipeline.program.attributes.get(name)
            if attribute:
                self._vertex_array[attribute.location] = pointer

    def render(self, **uniforms):
        # set our uniforms
        self._pipeline.set_uniforms(**uniforms)

        # render
        with self._pipeline:
            if self.indices is not None:
                self._vertex_array.render_indices(self.indices, self.primitive)
            else:
                self._vertex_array.render(self.primitive)

    @property
    def pipeline(self):
        return self._pipeline

    @pipeline.setter
    def pipeline(self, pipeline):
        self._pipeline = pipeline
        self._bind_pointers()

    @property
    def vertex_array(self):
        return self._vertex_array
