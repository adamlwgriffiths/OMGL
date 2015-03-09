from __future__ import absolute_import
from OpenGL import GL
from OpenGL.GL.ARB import texture_rg
import numpy as np
from .. import dtypes
from ..proxy import Proxy, Integer32Proxy
from ..object import ManagedObject, BindableObject, DescriptorMixin
try:
    from PIL import Image
except:
    Image = None

# TODO: add multisample texture
# https://www.opengl.org/wiki/Texture_Storage#Immutable_storage
# init method:
#   o levels -> samples
#   + fixed_samples = False

# TODO: FBO texture (see pygol)



class TextureUnitProxy(Integer32Proxy):
    def __init__(self):
        super(TextureUnitProxy, self).__init__(
            getter_args=[GL.GL_ACTIVE_TEXTURE],
            setter=GL.glActiveTexture,
        )

    def _get_result(self, value):
        result = super(TextureUnitProxy, self)._get_result(value)
        return result - GL.GL_TEXTURE0

    def _set_args(self, obj, value):
        return [GL.GL_TEXTURE0 + value]

class TextureProxy(Proxy):
    def __init__(self, property, **kwargs):
        super(TextureProxy, self).__init__(
            getter_args=[property],
            setter_args=[property],
            prepend_args=['_target'],
            bind=True,
            **kwargs
        )

class Integer32TextureProxy(TextureProxy):
    def __init__(self, property):
        super(Integer32TextureProxy, self).__init__(
            property,
            getter=GL.glGetTexParameteriv,
            setter=GL.glTexParameteri,
            dtype=np.int32,
        )

class Float32TextureProxy(TextureProxy):
    def __init__(self, property):
        super(Float32TextureProxy, self).__init__(
            property,
            getter=GL.glGetTexParameterfv,
            setter=GL.glTexParameterf,
            dtype=np.float32,
        )


class TextureLevelProxy(Proxy):
    def __init__(self, property, level=0, **kwargs):
        super(TextureLevelProxy, self).__init__(
            getter_args=[level, property],
            prepend_args=['_target'],
            **kwargs
        )

    def _get_args(self, obj, cls):
        return super(TextureLevelProxy, self)._get_args(obj, cls) + [obj.handle]

class Integer32TextureLevelProxy(TextureLevelProxy):
    def __init__(self, property, level=0):
        super(Integer32TextureLevelProxy, self).__init__(
            property,
            level,
            getter=GL.glGetTexLevelParameteriv,
            dtype=np.int32,
        )

class Float32TextureLevelProxy(TextureLevelProxy):
    def __init__(self, property, level=0):
        super(Float32TextureLevelProxy, self).__init__(
            property,
            level,
            getter=GL.glGetTexLevelParameterfv,
            dtype=np.float32,
        )


class SwizzleProxy(TextureProxy):
    _swizzles = (
        ('r', GL.GL_RED),
        ('g', GL.GL_GREEN),
        ('b', GL.GL_BLUE),
        ('a', GL.GL_ALPHA),
        ('0', GL.GL_ZERO),
        ('1', GL.GL_ONE),
    )
    _swizzle_from_gl = dict((gl, char,) for char,gl in _swizzles)
    _swizzle_to_gl = dict(_swizzles)

    @classmethod
    def swizzle_from_gl(cls, swizzle):
        return [cls._swizzle_from_gl[s] for s in swizzle]

    @classmethod
    def swizzle_to_gl(cls, swizzle):
        return [cls._swizzle_to_gl[s] for s in swizzle]

    def __init__(self):
        super(SwizzleProxy, self).__init__(
            GL.GL_TEXTURE_SWIZZLE_RGBA,
            getter=GL.glGetTexParameteriv,
            setter=GL.glTexParameteriv,
            dtype=np.uint32,
        )

    def __get__(self, obj, cls):
        value = super(SwizzleProxy, self).__get__(obj, cls)
        return self.swizzle_from_gl(value)

    def __set__(self, obj, value):
        value = self.swizzle_to_gl(value)
        super(SwizzleProxy, self).__set__(obj, value)

    def _set_args(self, obj, value):
        value = (GL.GLint * len(value))(*value)
        return super(SwizzleProxy, self)._set_args(obj, value)


class ActiveUnitMetaClass(type):
    """Allows the setting of the active_unit variable when called on a class, instead of an object.
    https://stackoverflow.com/questions/28403069/way-to-have-a-class-level-type-descriptor-with-set
    """
    active_unit = TextureUnitProxy()


class Texture(DescriptorMixin, BindableObject, ManagedObject):
    __metaclass__ = ActiveUnitMetaClass

    _create_func = GL.glGenTextures
    _delete_func = GL.glDeleteTextures
    _bind_func = GL.glBindTexture

    max_units = Integer32Proxy(GL.GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS)
    active_unit = TextureUnitProxy()

    max_size = Integer32Proxy(GL.GL_MAX_TEXTURE_SIZE)
    max_array_length = Integer32Proxy(GL.GL_MAX_ARRAY_TEXTURE_LAYERS)

    min_filter = Integer32TextureProxy(GL.GL_TEXTURE_MIN_FILTER)
    mag_filter = Integer32TextureProxy(GL.GL_TEXTURE_MAG_FILTER)

    lod_bias = Float32TextureProxy(GL.GL_TEXTURE_LOD_BIAS)
    min_lod = Integer32TextureProxy(GL.GL_TEXTURE_MIN_LOD)
    max_lod = Integer32TextureProxy(GL.GL_TEXTURE_MAX_LOD)

    mipmap_base_level = Integer32TextureProxy(GL.GL_TEXTURE_BASE_LEVEL)
    mipmap_max_level = Integer32TextureProxy(GL.GL_TEXTURE_MAX_LEVEL)

    border_color = Float32TextureProxy(GL.GL_TEXTURE_BORDER_COLOR)

    compare_mode = Integer32TextureProxy(GL.GL_TEXTURE_COMPARE_MODE)
    compare_func = Integer32TextureProxy(GL.GL_TEXTURE_COMPARE_FUNC)

    stencil_mode = Integer32TextureProxy(GL.GL_DEPTH_STENCIL_TEXTURE_MODE)

    swizzle = SwizzleProxy()

    @classmethod
    def infer_internal_format(cls, shape, dtype, explicit=False):
        try:
            # GL_RED doesn't give us specific types in PyOpenGL, so use GL_R
            # GL_R and GL_RG should be taken from the rg extension
            base, module = {
                1:  ('GL_R', texture_rg),
                2:  ('GL_RG', texture_rg),
                3:  ('GL_RGB', GL),
                4:  ('GL_RGBA', GL),
            }[shape[-1]]

            if explicit:
                # include type information for signed and unsigned integers
                # also for 32 bit integers
                type = {
                    np.uint8:   '8UI',
                    np.uint16:  '16UI',
                    np.uint32:  '32UI',
                    np.int8:    '8I',
                    np.int16:   '16I',
                    np.int32:   '32I',
                    np.float16: '16F',
                    np.float32: '32F',
                }[dtype.type]
            else:
                type = {
                    np.uint8:   '8',
                    np.uint16:  '16',
                    np.uint32:  '',
                    np.int8:    '8',
                    np.int16:   '16',
                    np.int32:   '',
                    np.float16: '16F',
                    np.float32: '32F',
                }[np.dtype(dtype).type]

            string = base + type
            enum = getattr(module, string)
            return enum
        except KeyError as e:
            raise ValueError(e.message)

    @classmethod
    def infer_format(cls, shape, dtype):
        try:
            # GL_R and GL_RG should be taken from the rg extension
            base, module = {
                1:  ('GL_RED', GL,),
                2:  ('GL_RG', texture_rg,),
                3:  ('GL_RGB', GL,),
                4:  ('GL_RGBA', GL,),
            }[shape[-1]]

            string = base
            enum = getattr(module, string)
            return enum
        except KeyError as e:
            raise ValueError(e.message)


class BasicTexture(Texture):
    _pil_formats = {
        'RGB':  GL.GL_RGB,
        'RGBA': GL.GL_RGBA,
        'RGBX': GL.GL_RGBA,
        'RGBa': GL.GL_RGBA,
        '1':    GL.GL_RED,
        'L':    GL.GL_RED,
        'LA':   texture_rg.GL_RG,
        'F':    GL.GL_RGB,
        'I':    GL.GL_RGB,
    }

    _pil_dtypes = {
        'RGB':  dtypes.uint8,
        'RGBA': dtypes.uint8,
        'RGBX': dtypes.uint8,
        'RGBa': dtypes.uint8,
        '1':    dtypes.uint8,
        'L':    dtypes.uint8,
        'LA':   dtypes.uint8,
        'F':    dtypes.float32,
        'I':    dtypes.int32,
    }

    _pil_swizzles = {
        '1':    'rrr1',
        'L':    'rrr1',
        'I':    'rrr1',
        'F':    'rrr1',
        'LA':   'rrrg',
    }

    @classmethod
    def open(cls, filename, flip=True, **kwargs):
        if not Image:
            raise ValueError('PIL not installed')

        image = Image.open(filename)
        if flip:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        obj = cls(image, **kwargs)
        return obj

    @classmethod
    def _process_image(cls, image):
        # some TIFF images don't render correctly
        # if we convert them to RGBX they suddenly
        # begin rendering correctly
        # so let's do that
        # some TIFF images can't be converted
        # this may throw an IOError exception
        # handle unsupported formats
        # convert from unsupported formats to RGBX
        image = image.convert('RGBX')

        return image

    @classmethod
    def _image_to_np_array(cls, image):
        dtype = cls._pil_dtypes.get(image.mode, dtypes.uint8)
        data = np.asarray(image, dtype=dtype.dtype)
        data.shape = (image.size[0], image.size[1], -1)

        return data

    def __init__(self, data=None, shape=None, dtype=None, internal_format=None, format=None, level=0, mipmap=True, **properties):
        super(Texture, self).__init__()

        if Image and isinstance(data, Image.Image):
            # PIL image
            if self._target != GL.GL_TEXTURE_2D:
                raise ValueError('Must use Texture2D for PIL images')

            image = data
            image = self._process_image(data)
            data = self._image_to_np_array(image)
            properties['swizzle'] = properties.get('swizzle') or self._pil_swizzles.get(image.mode)


        if data is not None:
            self._shape = shape or data.shape
            self._dtype = dtype or data.dtype
            self._format = format or self.infer_format(data.shape, data.dtype)
            self._internal_format = internal_format or self.infer_internal_format(data.shape, data.dtype)
            data_type = dtypes.for_dtype(data.dtype)
        elif shape and dtype:
            self._shape = shape
            self._dtype = dtype
            self._format = format or GL.GL_RGBA
            self._internal_format = internal_format or self.infer_internal_format(shape, dtype)
            data_type = dtypes.for_dtype(np.uint8)
        else:
            raise ValueError('Invalid parameters')

        self._size = self._shape[:-1]

        level = 0
        border = 0
        args = [self._target, level, self._internal_format,]
        args += list(self._size)
        args += [border, self._format, data_type.gl_enum, data]

        # set a default min / mag filter
        properties['min_filter'] = properties.get('min_filter', GL.GL_LINEAR)
        properties['mag_filter'] = properties.get('mag_filter', GL.GL_LINEAR)

        # set any proxy values before we continue
        for k,v in properties.items():
            if v:
                setattr(self, k, v)

        with self:
            self._set(*args)

        if mipmap:
            self.mipmap()

    def get_data(self, level=0):
        data_type = dtypes.for_dtype(np.int8)

        with self:
            # BUG: PyOpenGL doesn't support GL_RG or GL_RG_INTEGER here
            # we have to get the red and green components individually
            if self._format in [texture_rg.GL_RG, texture_rg.GL_RG_INTEGER,]:
                red_enum = GL.GL_RED_INTEGER if self._format == texture_rg.GL_RG_INTEGER else GL.GL_RED
                green_enum = GL.GL_GREEN_INTEGER if self._format == texture_rg.GL_RG_INTEGER else GL.GL_GREEN

                red = GL.glGetTexImage(self._target, level, red_enum, data_type.gl_enum, outputType=np.ndarray)
                green = GL.glGetTexImage(self._target, level, green_enum, data_type.gl_enum, outputType=np.ndarray)
                data = np.empty_like(self._npdata)
                data[...,0] = red
                data[...,1] = green
            else:
                data = GL.glGetTexImage(self._target, level, self._format, data_type.gl_enum, outputType=np.ndarray)

        data = data.view(dtype=self._dtype)
        return data

    def set_data(self, data, format=None, offset=None, level=0):
        if Image and isinstance(data, Image.Image):
            # PIL image
            # TODO: handle other targets, including 2d texture arrays, 3d textures, etc
            if self._target != GL.GL_TEXTURE_2D:
                raise ValueError('Must use Texture2D for PIL images')

            image = data
            image = self._process_image(data)
            data = self._image_to_np_array(image)

        format = format or self.infer_format(data.shape, data.dtype)
        offset = offset or [0 for _ in self.size]
        data_type = dtypes.for_dtype(data.dtype)

        args = [self._target, level,]
        args += offset + list(data.shape[:-1])
        args += [format, data_type.gl_enum, data,]

        with self:
            self._sub_set(*args)


    def mipmap(self):
        with self:
            GL.glGenerateMipmap(self._target)

    @property
    def internal_format(self):
        return self._internal_format

    @property
    def size(self):
        return self._size

    @property
    def dtype(self):
        return self._dtype

    @property
    def shape(self):
        return self._shape

    @property
    def data(self):
        return self.get_data(0)

    @data.setter
    def data(self, value):
        self.set_data(value)


class Texture1D_Mixin(object):
    _set = GL.glTexImage1D
    _immutable_set = GL.glTexStorage1D
    _sub_set = GL.glTexSubImage1D

    wrap_s = Integer32TextureProxy(GL.GL_TEXTURE_WRAP_S)

    @property
    def width(self):
        return self.shape[0]


class Texture2D_Mixin(object):
    _set = GL.glTexImage2D
    _immutable_set = GL.glTexStorage2D
    _sub_set = GL.glTexSubImage2D

    wrap_s = Integer32TextureProxy(GL.GL_TEXTURE_WRAP_S)
    wrap_t = Integer32TextureProxy(GL.GL_TEXTURE_WRAP_T)

    @property
    def width(self):
        return self.shape[0]

    @property
    def height(self):
        return self.shape[1]


class Texture3D_Mixin(object):
    _set = GL.glTexImage3D
    _immutable_set = GL.glTexStorage3D
    _sub_set = GL.glTexSubImage3D

    wrap_s = Integer32TextureProxy(GL.GL_TEXTURE_WRAP_S)
    wrap_t = Integer32TextureProxy(GL.GL_TEXTURE_WRAP_T)
    wrap_r = Integer32TextureProxy(GL.GL_TEXTURE_WRAP_R)

    @property
    def width(self):
        return self.shape[0]

    @property
    def height(self):
        return self.shape[1]

    @property
    def depth(self):
        return self.shape[2]


class Texture1D(Texture1D_Mixin, BasicTexture):
    _target = GL.GL_TEXTURE_1D

class Texture2D(Texture2D_Mixin, BasicTexture):
    _target = GL.GL_TEXTURE_2D

class Texture3D(Texture3D_Mixin, BasicTexture):
    _target = GL.GL_TEXTURE_3D

class TextureArray1D(Texture2D_Mixin, BasicTexture):
    _target = GL.GL_TEXTURE_1D_ARRAY

class TextureArray2D(Texture3D_Mixin, BasicTexture):
    _target = GL.GL_TEXTURE_2D

class RectangularTexture(Texture2D_Mixin, BasicTexture):
    _target = GL.GL_TEXTURE_RECTANGLE

class BufferTexture(Texture):
    _target = GL.GL_TEXTURE_BUFFER

    bound_buffer = Integer32TextureLevelProxy(GL.GL_TEXTURE_BUFFER_DATA_STORE_BINDING)

    def __init__(self, buffer, internal_format=None):
        super(BufferTexture, self).__init__()
        self._buffer = buffer
        self._internal_format = internal_format or self.infer_internal_format(buffer.shape, buffer.dtype, explicit=True)

        with self:
            GL.glTexBuffer(self._target, self._internal_format, buffer.handle)

    @property
    def internal_format(self):
        return self._internal_format

    @property
    def size(self):
        return self._buffer._size

    @property
    def dtype(self):
        return self._buffer._dtype

    @property
    def shape(self):
        return self._buffer.shape

    @property
    def width(self):
        return self._buffer.size

    @property
    def buffer(self):
        return self._buffer

"""
class CubeMapTexture(BasicTexture):
    _target = GL.GL_TEXTURE_CUBE_MAP

class FrameBufferTexture(Texture2D):
    pass
"""
