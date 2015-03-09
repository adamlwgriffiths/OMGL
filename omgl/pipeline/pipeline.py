from __future__ import absolute_import
from ..object import BindableObject, DescriptorMixin
from ..texture.texture import Texture
from ..buffer.buffer import TextureBuffer

# TODO: iterate through properties
# if texture, create a sampler
# provide list of texture properties

class Pipeline(DescriptorMixin, BindableObject):
    def __init__(self, program, **properties):
        self._program = program

        self._properties = set(properties.keys())
        for name, value in properties.items():
            setattr(self, name, value)

    def __setattr__(self, name, value):
        if name[0] is not '_':
            self._properties.add(name)
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name in self._properties:
            del self._properties[name]
        object.__delattr__(self, name)

    def bind(self):
        # set our local properties as uniforms
        # bind the textures
        uniforms = dict((name, getattr(self, name)) for name in self._properties)
        self.set_uniforms(**uniforms)

        # bind our shader
        self._program.bind()

    def unbind(self):
        # unbind the textures
        for name in self._properties:
            value = getattr(self, name)
            if isinstance(value, Texture):
                unit = getattr(self._program, name)
                if unit is not None:
                    Texture.active_unit = unit
                    value.unbind()

        # unbind the shader
        self._program.unbind()

    def set_uniforms(self, **uniforms):
        for name, value in uniforms.items():
            if hasattr(self._program, name):
                if isinstance(value, TextureBuffer):
                    value = value.texture
                if isinstance(value, Texture):
                    unit = getattr(self._program, name)
                    if unit is not None:
                        Texture.active_unit = unit
                        value.bind()
                else:
                    setattr(self._program, name, value)

    @property
    def program(self):
        return self._program

    @property
    def properties(self):
        return dict((name, getattr(self, name)) for name in self._properties)

"""
    @property
    def textures(self):
        # return properties that are textures
        pass
"""