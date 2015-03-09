from __future__ import absolute_import
from OpenGL import GL
import numpy as np
from .variables import ProgramVariable, Attribute, Uniform
from ..object import ManagedObject, BindableObject, DescriptorMixin
from ..proxy import Integer32Proxy
from ..proxy import Proxy

"""
TODO: https://www.opengl.org/registry/specs/ARB/separate_shader_objects.txt
TODO: https://www.opengl.org/registry/specs/ARB/shading_language_include.txt
TODO: https://www.opengl.org/registry/specs/ARB/sampler_objects.txt
"""

class ProgramProxy(Proxy):
    def __init__(self, property, dtype=None):
        super(ProgramProxy, self).__init__(
            getter=GL.glGetProgramiv, getter_args=[property],
            dtype=dtype, prepend_args=['_handle'],
        )


class VariableStore(DescriptorMixin, dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, name, value):
        self[name] = value

    def __setitem__(self, index, value):
        if not isinstance(value, ProgramVariable):
            raise ValueError('Attempted to set to a non-ProgramVariable, use the ProgramVariable.data setter instead')
        super(VariableStore, self).__setitem__(index, value)


class Program(DescriptorMixin, BindableObject, ManagedObject):
    _create_func = GL.glCreateProgram
    _delete_func = GL.glDeleteProgram
    _bind_func = GL.glUseProgram
    _current_program = Integer32Proxy(GL.GL_CURRENT_PROGRAM, bind=False)

    active_attribute_max_length = ProgramProxy(GL.GL_ACTIVE_ATTRIBUTE_MAX_LENGTH)
    active_attributes = ProgramProxy(GL.GL_ACTIVE_ATTRIBUTES)
    active_uniform_max_length = ProgramProxy(GL.GL_ACTIVE_UNIFORM_MAX_LENGTH)
    active_uniforms = ProgramProxy(GL.GL_ACTIVE_UNIFORMS)
    link_status = ProgramProxy(GL.GL_LINK_STATUS, dtype=np.bool)
    delete_status = ProgramProxy(GL.GL_DELETE_STATUS, dtype=np.bool)

    def __init__(self, shaders, frag_locations=None, **attributes):
        super(Program, self).__init__()
        self._loaded = False
        self._attributes = None
        self._uniforms = None

        for shader in shaders:
            self._attach(shader)

        if frag_locations:
            if isinstance(frag_locations, basestring):
                frag_locations = ((frag_locations, 0),)
            for name, number in frag_locations:
                self._set_frag_location(name, number)

        # set our attributes before link time
        for name, location in list(attributes.items()):
            GL.glBindAttribLocation(self._handle, location, name)

        self._link()

        # detach shaders so they can be free'ed by opengl
        for shader in shaders:
            self._detach(shader)

        # mark the program as loaded
        # from now onwards, any calls to unknown variables or assignments
        # will the program variables to load if they aren't already
        # we do this, because loading the variables now will stall the pipeline
        # until the gpu finishes linking, it's better to link programs in parallel
        # and then query only when initially needed
        self._loaded = True

    def __getattr__(self, name):
        # only load variables if the program is loaded and the attribute is unknown
        try:
            if self._loaded:
                if not self._uniforms or not self._attributes:
                    self._load_variables()
                stores = [self.__dict__['_uniforms'], self.__dict__['_attributes']]
                for store in stores:
                    if name in store:
                        return store[name].__get__(store, store.__class__)
        except:
            pass
        raise AttributeError

    def __setattr__(self, name, value):
        try:
            if self._loaded:
                if name not in self.__dict__:
                    if not self._uniforms or not self._attributes:
                        self._load_variables()
        except:
            pass
        return super(Program, self).__setattr__(name, value)

    def _attach(self, shader):
        GL.glAttachShader(self._handle, shader.handle)

    def _detach(self, shader):
        GL.glDetachShader(self._handle, shader.handle)

    def _link(self):
        GL.glLinkProgram(self._handle)

        if not self.link_status:
            log = self.log
            # TODO: parse the log?
            raise ValueError(log)

        # linking sets the program as active
        # ensure we unbind the program
        self.unbind()

    def _load_active_attributes(self):
        # this is called by __getattr__ and __setattribute__
        # it cannot make any assignments to self
        # it MUST use self.__dict__ instead
        store = VariableStore()
        self.__dict__['_attributes'] = store
        max_length = self.active_attribute_max_length
        for index in range(self.active_attributes):
            attribute = Attribute(self, index, max_length)
            store[attribute.name] = attribute
            self.__dict__[attribute.name] = attribute

    def _load_active_uniforms(self):
        # this is called by __getattr__ and __setattribute__
        # it cannot make any assignments to self
        # it MUST use self.__dict__ instead
        store = VariableStore()
        self.__dict__['_uniforms'] = store
        max_length = self.active_uniform_max_length
        for index in range(self.active_uniforms):
            uniform = Uniform(self, index, max_length)
            store[uniform.name] = uniform
            self.__dict__[uniform.name] = uniform

    def _load_variables(self):
        self._load_active_attributes()
        self._load_active_uniforms()

    def _set_frag_location(self, name, number):
        GL.glBindFragDataLocation(self._handle, number, name)

    @property
    def attributes(self):
        if not self._attributes:
            self._load_variables()
        return self._attributes

    @property
    def uniforms(self):
        if not self._uniforms:
            self._load_variables()
        return self._uniforms

    @property
    def valid(self):
        return bool(GL.glValidateProgram(self._handle))

    @property
    def log(self):
        return GL.glGetProgramInfoLog(self._handle)
