from __future__ import absolute_import
import re
from OpenGL import GL
from OpenGL.raw.GL.VERSION import GL_2_0
import numpy as np
from . import enumerations
from .. import dtypes


class ProgramVariable(object):
    def __init__(self, program, index, max_length):
        self._index = index
        self._program = program

        length = (GL.constants.GLsizei)()
        size = (GL.constants.GLint)()
        enum = (GL.constants.GLenum)()
        name = (GL.constants.GLchar * max_length)()
        self._get_defails_func(self._program.handle, index, max_length, length, size, enum, name)

        self._size = size.value
        self._enum = enumerations.variables_by_value(enum.value)
        self._name = name.value

        self._parse_type()

    def _format_for_enum(self, enum):
        if '_UNSIGNED_INT' in self._enum.name:
            return 'ui'
        elif '_FLOAT' in self._enum.name:
            return 'f'
        elif '_DOUBLE' in self._enum.name:
            return 'd'
        else:
            return 'i'

    _re_matrix = re.compile(r'_MAT(?P<dimensions>[\dx]+)')
    _re_vector = re.compile(r'_VEC(?P<dimensions>\d)')
    def _parse_type(self):
        """Parses the GL enumeration for the uniform and returns the
        appropriate function to use to set uniform data.
        """
        self._format = self._format_for_enum(self._enum)
        self._dtype = np.dtype(dtypes.for_code(self._format).dtype)

        if '_MAT' in self._enum.name:
            self._is_matrix = True

            match = self._re_matrix.search(self._enum.name)
            dimensions = match.group('dimensions')
            dimensions = dimensions.split('x')
            dimensions = map(int, dimensions)

            # ensure size is 2 dimensions
            # if not, duplicate the size, ie Mat2 -> [2] -> [2, 2] = 4
            if len(dimensions) == 1:
                dimensions = dimensions * 2

            self._dimensions = tuple(dimensions)
        else:
            self._is_matrix = False

            if '_VEC' in self._enum.name:
                match = self._re_vector.search(self._enum.name)
                dimensions = int(match.group('dimensions'))
            else:
                dimensions = 1
            self._dimensions = (dimensions,)

    @property
    def length(self):
        return self._size

    @property
    def enum(self):
        return self._enum

    @property
    def name(self):
        return self._name.split('[')[0]

    @property
    def index(self):
        return self._index

    @property
    def location(self):
        return int(self._get_location_func(self._program.handle, self._name))

    @property
    def dtype(self):
        """The numpy dtype for this attribute.
        """
        return self._dtype

    @property
    def itemsize(self):
        """The number of bytes a single uniform element takes.
        """
        # number of dimensions * dtype
        return reduce(lambda x,y: x*y, self._dimensions) * self._dtype.itemsize

    @property
    def nbytes(self):
        """The total number of bytes this attribute uses.

        This is the equivalent of::

            attribute.size * attribute.itemsize

        """
        return self._size * self.itemsize

    @property
    def dimensions(self):
        return self._dimensions


class Attribute(ProgramVariable):
    _get_defails_func = GL.glGetActiveAttrib
    _get_location_func = GL.glGetAttribLocation

    def __get__(self, obj, cls):
        return self.location


class Uniform(ProgramVariable):
    _get_defails_func = GL_2_0.glGetActiveUniform
    _get_location_func = GL.glGetUniformLocation
    _get_value_func = None
    _set_value_func = None

    def __init__(self, shader, index, max_length):
        super(Uniform, self).__init__(shader, index, max_length)

        # determine what function to use
        # https://www.opengl.org/sdk/docs/man/html/glUniform.xhtml
        # glUniform{size}{type}v
        #   glUniform2iv
        #   glUniform4uiv
        #   glUniform1fv
        # glUniformMatrix{size}{type}v
        #   glUniformMatrix2fv
        #   glUniformMatrix3x2fv

        # https://www.opengl.org/sdk/docs/man/html/glGetUniform.xhtml
        # glGetUniformfv 
        # glGetUniformiv 
        # glGetUniformuiv 
        # glGetUniformdv

        dimensions = map(lambda x: str(x), self._dimensions)
        if self._is_matrix:
            if dimensions[0] == dimensions[1]:
                dimensions = dimensions[0]
            get_func_string = 'glGetUniform{}v'.format(self._format)
            set_func_string = 'glUniformMatrix{}{}v'.format('x'.join(dimensions), self._format)
            self._get_value_func = getattr(GL, get_func_string)
            self._set_value_func = getattr(GL, set_func_string)
        else:
            dimensions = dimensions[0]
            get_func_string = 'glGetUniform{}v'.format(self._format)
            set_func_string = 'glUniform{}{}v'.format(dimensions, self._format)
            self._get_value_func = getattr(GL, get_func_string)
            self._set_value_func = getattr(GL, set_func_string)

    def _element_offset(self):
        """OpenGL stores each uniform value in a 32 byte location.
        Data structures smaller than this (vec2, vec3, sampler2D, etc) will still
        occupy the entire 32 byte location.

        When working with matrices, OpenGL returns the entire matrix located
        at the base location given.
        For a 4x4 matrix, each row of the matrix (a vec4) will occupy 1 location.
        The next matrix is at location + 4.

        For example, 'uniform vec2 vec[2]', vec[0] is at
        location + 0 and vec[1] is at location + 1.

        'uniform mat3 matrix[2]', matrix[0] is at location + 0 and
        matrix[1] is at location + 4.
        matrix[0][1] (second row of the first matrix) is at location + 1.
        """
        if not self._is_matrix:
            return 1
        else:
            return self._dimensions[0]

    def _set_data(self, location, value):
        value = np.array(value, dtype=self._dtype)
        count = value.nbytes / self.itemsize
        if self._is_matrix:
            self._set_value_func(location, count, False, value)
        else:    
            self._set_value_func(location, count, value)

    def _get_data(self, location):
        count = reduce(lambda x,y: x*y, self._dimensions)
        data = np.empty((count,), dtype=self._dtype)
        self._get_value_func(self._program.handle, location, data)
        data.shape = self._dimensions
        return data

    def _get_data_slice(self, index):
        length = index.stop - index.start
        dimensions = [length] + list(self.dimensions)
        data = np.empty(dimensions, dtype=self.dtype)
        element_offset = self._element_offset()
        location = self.location

        for _index in range(length):
            offset = (_index + index.start) * element_offset
            _data = self._get_data(location + offset)
            data[_index] = _data

        # check if the variable is an array or not
        # if not, don't return as an array of values
        if '[' not in self._name:
            data = data[0]
        # convert scalars to single values
        if self._dimensions == (1,):
            data = data[0]

        if index.step:
            data = data[::index.step]

        return data

    def __get__(self, obj, cls):
        return self.data

    def __set__(self, obj, value):
        try:
            self.data = value
        except Exception as e:
            print e

    def __getitem__(self, index):
        if isinstance(index, (int)):
            index = slice(index, index + 1, None)
            data = self._get_data_slice(index)
            # return the slice only
            return data[0]
        elif isinstance(index, slice):
            start = index.start or 0
            stop = min(index.stop or self.length, self.length)
            index = slice(start, stop, index.step)
            return self._get_data_slice(index)
        else:
            raise ValueError('Unsupported indexing method')

    def __setitem__(self, index, value):
        if isinstance(index, (int)):
            index = slice(index, index + 1, None)
        elif isinstance(index, slice):
            if index.step > 1:
                raise ValueError('Step not supported')
            start = index.start or 0
            stop = min(index.stop or self.length, self.length)
            index = slice(start, stop, index.step)
        else:
            raise ValueError('Unsupported indexing method')

        with self._program:
            self._set_data(self.location + (index.start * self._element_offset()), value)

    @property
    def data(self):
        return self._get_data_slice(slice(0, self._size, None))

    @data.setter
    def data(self, value):
        with self._program:
            self._set_data(self.location, value)
