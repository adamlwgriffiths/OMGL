import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import cyglfw3 as glfw
import time
import math

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
import numpy as np
from omgl.buffer.buffer import VertexBuffer
from omgl.shader.shader import FragmentShader, VertexShader
from omgl.shader.program import Program
from omgl.mesh.sub_mesh import SubMesh
from omgl.pipeline.pipeline import Pipeline
from omgl.texture.texture import Texture2D
import pyrr
from pyrr import Matrix44

vss = """
    #version 400
    //layout(location=0) in vec3 in_position;
    in vec3 in_position;
    in vec2 in_uv;
    uniform mat4 in_projection;
    uniform mat4 in_model_view;
    out vec2 ex_uv;
    void main() {
        gl_Position = in_projection * in_model_view * vec4(in_position, 1.0);
        ex_uv = in_uv;
    }
    """

fss = """
    #version 400
    uniform sampler2D in_diffuse_texture;
    in vec2 ex_uv;
    out vec4 out_color;
    void main(void) {
        out_color = texture(in_diffuse_texture, ex_uv);
    }
    """

data, indices = pyrr.geometry.create_cube((5.,5.,5.,), st=True, dtype=np.float32)
flat_data = data[indices]


shaped_data = flat_data.view(dtype=[('in_position', np.float32, 3,),('in_uv', np.float32, 2,),])
vb = VertexBuffer(shaped_data)


fs = FragmentShader(fss)
vs = VertexShader(vss)
sp = Program([vs, fs])


pl = Pipeline(sp)
sm = SubMesh(pl, **vb.pointers)



dtype = np.uint8
dtype_max = np.iinfo(dtype).max
#dtype = np.float32
texture_data = np.random.random((32,32,4))
texture_data *= dtype_max
texture_data = texture_data.astype(dtype)

texture = Texture2D(texture_data)

texture.active_unit = pl.program.in_diffuse_texture
texture.bind()


aspect = float(window_size[0]) / float(window_size[1])
projection = Matrix44.perspective_projection(90., aspect, 1., 100., np.float32)
model_view = Matrix44.from_translation([0.,0.,-8.], np.float32)

GL.glClearColor(0.2, 0.2, 0.2, 1.0)
GL.glEnable(GL.GL_DEPTH_TEST)
GL.glDisable(GL.GL_CULL_FACE)

last = time.clock()

glfw.MakeContextCurrent(window)
while not glfw.WindowShouldClose(window):
    current = time.clock()
    delta = current - last

    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    rotation = Matrix44.from_y_rotation(math.pi * delta, np.float32)
    model_view = rotation * model_view

    sm.render(in_projection=projection, in_model_view=model_view)

    glfw.SwapBuffers(window)
    glfw.PollEvents()

    last = current


glfw.DestroyWindow(window)

glfw.Terminate()
exit()
