"""Raw OpenGL command version for use when developing new features or
debugging Bast issues.
"""

from __future__ import absolute_import, print_function
import cyglfw3 as glfw
import numpy as np
import pyrr
import time
import ctypes
from PIL import Image

if not glfw.Init():
    exit()

version = (4,0)
glfw.WindowHint(glfw.CLIENT_API, glfw.OPENGL_API)
major, minor = version
glfw.WindowHint(glfw.CONTEXT_VERSION_MAJOR, major)
glfw.WindowHint(glfw.CONTEXT_VERSION_MINOR, minor)
glfw.WindowHint(glfw.CONTEXT_ROBUSTNESS, glfw.NO_ROBUSTNESS)
glfw.WindowHint(glfw.OPENGL_FORWARD_COMPAT, 1)
glfw.WindowHint(glfw.OPENGL_DEBUG_CONTEXT, 1)
glfw.WindowHint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

window_size = (640, 480)
window = glfw.CreateWindow(window_size[0], window_size[1], 'Bast')
if not window:
    glfw.Terminate()
    exit()

glfw.MakeContextCurrent(window)

from OpenGL import GL

def redirector(fn):
    def func(*args, **kwargs):
        print('{}({}, {})'.format(fn.__name__, args, kwargs))
        return fn(*args, **kwargs)
    return func

for name in dir(GL):
    # ignore normal module values
    if not name.startswith('gl'):
        continue

    func = getattr(GL, name)
    func = redirector(func)
    setattr(GL, name, func)



#
# Shader
#
vs_source = """
#version 400
layout(location=0) in vec3 in_position;
layout (location = 1) in vec2 in_uv;
uniform mat4 in_projection;
uniform mat4 in_model_view;
out vec2 ex_uv;
void main() {
    gl_Position = in_projection * in_model_view * vec4(in_position, 1.0);
    ex_uv = in_uv;
}
"""

fs_source = """
#version 400
in vec2 ex_uv;
uniform sampler2D in_diffuse_texture;
uniform samplerBuffer in_buffer_texture;
out vec4 out_color;
void main(void) {
    //out_color = vec4(1.,1.,1.,1.);
    //out_color = vec4(gl_FragCoord.xyz / vec3(640., 480., 1.), 1.0);
    //out_color = vec4(ex_uv.x, ex_uv.y, 1.0, 1.0);
    //out_color = texture(in_diffuse_texture, ex_uv);
    out_color = texelFetch(in_buffer_texture, 0);
}
"""

vs = GL.glCreateShader(GL.GL_VERTEX_SHADER)
GL.glShaderSource(vs, vs_source)
GL.glCompileShader(vs)
log = GL.glGetShaderInfoLog(vs)
if log:
    print(log)

fs = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
GL.glShaderSource(fs, fs_source)
GL.glCompileShader(fs)
log = GL.glGetShaderInfoLog(fs)
if log:
    print(log)

sp = GL.glCreateProgram()
GL.glAttachShader(sp, vs)
GL.glAttachShader(sp, fs)
GL.glBindFragDataLocation(sp, 0, 'out_color')
GL.glLinkProgram(sp)
GL.glUseProgram(sp)

def set_uniform_f(name, value, count=1):
    location = GL.glGetUniformLocation(sp, name)
    GL.glUniform1fv(location, count, value)

def set_uniform_i(name, value, count=1):
    location = GL.glGetUniformLocation(sp, name)
    GL.glUniform1iv(location, count, value)

def set_uniform_matrix(name, value, count=1):
    location = GL.glGetUniformLocation(sp, name)
    GL.glUniformMatrix4fv(location, count, False, value)


#
# Vertex Data
#
va = GL.glGenVertexArrays(1)
GL.glBindVertexArray(va)


data, indices = pyrr.geometry.create_cube((5,5,5), st=True, dtype=np.float32)
data = data[indices]
buff = GL.glGenBuffers(1)
GL.glBindBuffer(GL.GL_ARRAY_BUFFER, buff)
GL.glBufferData(GL.GL_ARRAY_BUFFER, data.nbytes, data, GL.GL_DYNAMIC_DRAW)

location = GL.glGetAttribLocation(sp, 'in_position')
GL.glEnableVertexAttribArray(location)
GL.glVertexAttribPointer(location, 3, GL.GL_FLOAT, False, 5*4, None)

location = GL.glGetAttribLocation(sp, 'in_uv')
GL.glEnableVertexAttribArray(location)
GL.glVertexAttribPointer(location, 2, GL.GL_FLOAT, False, 5*4, ctypes.c_void_p(3*4))


aspect = float(window_size[0]) / float(window_size[1])
projection = pyrr.Matrix44.perspective_projection(90., aspect, 1., 100., np.float32)
model_view = pyrr.Matrix44.from_translation([0.,0.,-10.], np.float32)
#model_view = pyrr.Matrix44.from_x_rotation(np.pi / 2.) * model_view
rotation = pyrr.Matrix44.from_x_rotation(np.pi / 2.)

set_uniform_matrix('in_projection', np.array(projection, dtype=np.float32))
set_uniform_matrix('in_model_view', np.array(model_view, dtype=np.float32))


#
# Textures
#

image = Image.open("assets/textures/formats/rgba.png")
image = image.transpose(Image.FLIP_TOP_BOTTOM)
image = image.convert('RGBX')
#data = np.asarray(image, dtype=np.uint8)
data = np.array(image.getdata())
data.shape = (image.size[0], image.size[1], -1)


texture = GL.glGenTextures(1)
GL.glActiveTexture(GL.GL_TEXTURE0 + 0)
GL.glBindTexture(GL.GL_TEXTURE_2D, texture)

GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8, data.shape[0], data.shape[1], 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, data)

set_uniform_i('in_diffuse_texture', 0)



#
# Buffer Texture
#


#data = np.empty((512,512,4), dtype=np.uint8)
#data[:] = 128
data = np.empty((512,512,4), dtype=np.float32)
data[:] = 1.0

buff_tex = GL.glGenBuffers(1)
GL.glBindBuffer(GL.GL_TEXTURE_BUFFER, buff_tex)
GL.glBufferData(GL.GL_TEXTURE_BUFFER, data.nbytes, data, GL.GL_DYNAMIC_DRAW)

buffer_texture = GL.glGenTextures(1)
GL.glActiveTexture(GL.GL_TEXTURE0 + 1)
GL.glBindTexture(GL.GL_TEXTURE_BUFFER, buffer_texture)

#GL.glTexBuffer(GL.GL_TEXTURE_BUFFER, GL.GL_RGBA8, buff_tex)
GL.glTexBuffer(GL.GL_TEXTURE_BUFFER, GL.GL_RGBA32F, buff_tex)

set_uniform_i('in_buffer_texture', 1)



#
# Main
#
GL.glEnable(GL.GL_DEPTH_TEST)
GL.glDisable(GL.GL_CULL_FACE)
GL.glClearColor(0.2, 0.2, 0.2, 1.0)

last = time.clock()

while not glfw.WindowShouldClose(window):
    current = time.clock()
    delta = current - last

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(data))

    model_view = pyrr.Matrix44.from_y_rotation(np.pi * delta) * model_view
    set_uniform_matrix('in_model_view', np.array(model_view, dtype=np.float32))

    glfw.SwapBuffers(window)
    glfw.PollEvents()

    last = current

glfw.DestroyWindow(window)
glfw.Terminate()
