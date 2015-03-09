from __future__ import absolute_import, print_function
from OpenGL import GL
import numpy as np

class DataType(object):
    def __init__(self, integer, signed, np_type, gl_type, gl_enum, basic_type, char_code=None):
        self._integer = integer
        self._signed = signed
        self._np_type = np_type
        self._gl_type = gl_type
        self._gl_enum = gl_enum
        self._char_code = char_code
        self._basic_type = basic_type

    @property
    def dtype(self):
        return self._np_type

    @property
    def gl_type(self):
        return self._gl_type

    @property
    def gl_enum(self):
        return self._gl_enum

    @property
    def char_code(self):
        return self._char_code

boolean = DataType(True, True, np.bool8, GL.constants.GLbyte, GL.GL_BOOL, bool)
int8 = DataType(True, True, np.int8, GL.constants.GLbyte, GL.GL_BYTE, int, 'b')
uint8 = DataType(True, False, np.uint8, GL.constants.GLubyte, GL.GL_UNSIGNED_BYTE, int, 'ub')
int16 = DataType(True, True, np.int16, GL.constants.GLshort, GL.GL_SHORT, int)
uint16 = DataType(True, False, np.uint16, GL.constants.GLushort, GL.GL_UNSIGNED_SHORT, int)
int32 = DataType(True, True, np.int32, GL.constants.GLint, GL.GL_INT, int, 'i')
uint32 = DataType(True, False, np.uint32, GL.constants.GLuint, GL.GL_UNSIGNED_INT, int, 'ui')
# TODO: int64
# TODO: uint64
#float16 = DataType(False, True, np.float16, GL.constants.GLhalfARB, GL.GL_HALF_NV, float, 'f16')
float32 = DataType(False, True, np.float32, GL.constants.GLfloat, GL.GL_FLOAT, float, 'f')
float64 = DataType(False, True, np.float64, GL.constants.GLdouble, GL.GL_DOUBLE, float, 'd')

data_types = [boolean, int8, uint8, int16, uint16, int32, uint32, float32, float64]

def for_enum(enum):
    return dict((int(dtype.gl_enum), dtype) for dtype in data_types)[int(enum)]

def for_code(code):
    return dict((str(dtype.char_code), dtype) for dtype in data_types)[str(code)]

def for_dtype(dtype):
    if isinstance(dtype, np.dtype):
        # handle subdtypes being converted to np.void
        if dtype.subdtype:
            dtype = dtype.subdtype[0]
        else:
            dtype = dtype.type
    return dict((dtype.dtype, dtype) for dtype in data_types)[dtype]
