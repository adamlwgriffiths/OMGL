====
OMGL
====

An easy to use Pythonic 3D OpenGL framework.

OMGL is the Graphical core of the `Bast 3D engine <https://github.com/adamlwgriffiths/bast>`_.

Inspired by the following projects:

* `PyGLy <https://github.com/adamlwgriffiths/PyGLy>`_
* `PyGL <https://github.com/Ademan/pygl>`_
* `Glitter <https://github.com/swenger/glitter>`_


Features
========

* Pythonic - Don't worry about OpenGL's horrible state machine.
* NumPy at the Core - Easily pass complex data structures to OpenGL.
* BYOWS - Bring your own windowing system (`CyGLFW3 recommended <https://github.com/adamlwgriffiths/cyglfw3>`_).



Dependencies
============

* Numpy (1.8.2 as 1.9 has a `critical bug <https://github.com/numpy/numpy/issues/5224>`_)
* PyOpenGL
* Pillow


Optional dependencies dependencies
==================================

* PyOpenGL-accelerate - Speed boost for PyOpenGL
    * `pip install -r requirements-accelerate.txt`
    * or `pip install omgl[accelerate]`
* CyGLFW3 - Windowing system used in examples (or other windowing system)
    * `pip install -r requirements-cyglfw3.txt`
    * or `pip install omgl[cyglfw3]`
* Pyrr - 3D Mathematics library used in examples
    * `pip install -r requirements-pyrr.txt`
    * or `pip install omgl[pyrr]`

To install all dependencies:

* `pip install omgl[accelerate,cyglfw3,pyrr]`


Examples
========


Debugging
---------

You can print out each OpenGL call you or OMGL make by enabling function printing.
This is excellent for debugging OpenGL issues or inspecting the OMGL call logic.

Essentially this replaces all the PyOpenGL glX functions with a proxy function that
prints the functions name and arguments before calling the original function.

::

    from omgl import debug
    debug.print_gl_calls(True)



Numpy Dtypes
------------

It is often important to convert between OpenGL and Numpy dtypes for variable types
and enumerations.

This is easily done with the dtypes module.

::

    from OpenGL import GL
    from omgl import dtypes
    print(dtypes.uint8.dtype)
    print(dtypes.uint8.gl_type)
    print(dtypes.uint8.gl_enum)
    print(dtypes.uint8.char_code)

    d = dtypes.for_enum(GL.GL_UNSIGNED_INT)
    print(d.gl_enum, d.dtype)

    d = dtypes.for_dtype(np.float32)
    print(d.gl_enum, d.dtype)

    d = dtypes.for_code('f')
    print(d.gl_enum, d.dtype)



Textures
--------

Textures can be created using raw data.

::

    from omgl.texture import Texture2D
    data = np.random.random((32,32,4))
    data *= 255
    data = data.astype(np.uint8)

    texture = Texture2D(data)

    texture.active_unit = 0
    texture.bind()


Or loaded from a file using PIL / Pillow

::

    from omgl.texture import Texture2D
    texture = Texture2D.open('assets/texture/formats/RGBA.png')


Textures also provide information about themselves.

::


    from omgl.texture import Texture2D
    texture = Texture2D.open('assets/texture/formats/RGBA.png')

    print(texture.internal_format)
    print(texture.size)
    print(texture.dtype)
    print(texture.shape)


Textures can also be created empty using a shape and dtype.
Passed formats and Internal formats are auto-detected, but can be over-ridden
with the internal_format and format arguments.

::

    from OpenGL import GL
    from omgl.texture import Texture2D
    # create an empty 256x256 texture with 4 channels, RGBA.
    texture = Texture2D(shape=(256,256,4), dtype=np.uint8)
    texture.set_data(data=np.random.random((256,256,4)))

    texture = Texture2D(shape=(256,256,4), dtype=np.uint8, internal_format=GL.GL_RGBA)



Textures will automatically have their min and mag filters set to GL_LINEAR
to avoid 'black textures' in OpenGL 3.
This can be avoided by passing the desired filter mode to the constructor as the
min_filter and mag_filter properties.

::

    from OpenGL import GL
    from omgl.texture import Texture2D
    texture = Texture2D.open('assets/texture/formats/RGBA.png',
        min_filter=GL.GL_NEAREST,
        mag_filter=GL.GL_NEAREST,
    )


MipMap's are automatically generated, and can be re-generated with the 'mipmap' function.
Automatic generation of mipmaps can be disabled by over-riding the mipmap argument
in the constructor and set_data functions.

::

    from omgl.texture import Texture2D
    texture = Texture2D(shape=(256,256,4), dtype=np.uint8, mipmap=False)
    texture.set_data(data=np.random.random((256,256,4)), mipmap=False)
    texture.mipmap()
    texture.set_data(data=np.random.random((256,256,4)), mipmap=False)
    texture.mipmap()



Because of the need for texture minification and magnification, textures consist
of a number of 'levels'. This also means that getting and setting data must specify
the requested level.
By default this is 0.

::

    from omgl.texture import Texture2D
    texture = Texture2D(shape=(256,256,4), dtype=np.uint8, mipmap=False)
    texture.set_data(np.random.random((256,256,4)))
    texture.mipmap()

    # get base level texture data
    print(texture.get_data())

    # get first mipmap level data
    print(texture.get_data(1))

    # a convenience property is provided for level 0
    texture.data = np.random.random((256,256,4))
    print(texture.data)


Various texture parameters can be set at creation via named arguments, or later.

::

    from omgl.texture import Texture2D
    texture = Texture2D.open('assets/texture/formats/RGBA.png', wrap_s=GL.GL_REPEAT)
    texture.wrap_t = GL.GL_CLAMP_TO_EDGE


The active texture unit can be set from the Texture class (or derived classes)
or texture objects themselves.
Note that this property accesses the global active unit property, and isn't
setting that object's texture unit.

::

    from omgl.texture import Texture, Texture2D
    texture = Texture2D.open('assets/texture/formats/RGBA.png')

    # the following calls are all equivalent
    texture.active_unit = 1
    Texture.active_unit = 1
    Texture2D.active_unit = 1

    # we can get the current active unit.
    print(Texture.active_unit)


Buffers
-------


Buffers make use of complex numpy dtype's. This let's OMGL automatically tell OpenGL
about the layout of your buffers.

::

    from omgl.buffer import VertexBuffer
    data = np.array([
        [([ 1., 0.,-1.], [1., 0.])],
        [([-1., 0.,-1.], [0., 0.])],
        [([ 0., 1.,-1.], [.5, 1.])],
        ],
        dtype=[('in_position', np.float32, 3,),('in_uv', np.float32, 2,),]
    )
    vb = VertexBuffer(data)


To avoid the complexities of creating the array, you can convert to a complex array after creation.

::

    from omgl.buffer import VertexBuffer
    flat_data = np.array([
        [ 1., 0.,-1., 1., 0.],
        [-1., 0.,-1., 0., 0.],
        [ 0., 1.,-1., .5, 1.],
    ])
    data = flat_data.view(dtype=[('in_position', np.float32, 3,),('in_uv', np.float32, 2,),])
    vb = VertexBuffer(data)


You can manually provide this information should you not want to use complex dtypes.

::

    from omgl.buffer import VertexBuffer, BufferPointer
    flat_data = np.array([
        [ 1., 0.,-1., 1., 0.],
        [-1., 0.,-1., 0., 0.],
        [ 0., 1.,-1., .5, 1.],
    ])
    data = flat_data.view(dtype=[('in_position', np.float32, 3,),('in_uv', np.float32, 2,),])
    vb = VertexBuffer(data)

    # pointer to vertex data
    # total size of an element is 5 * 32bit floats
    stride = 5 * np.dtype(np.float32).itemsize
    vertex_ptr = BufferPointer(vb, count=3, stride=stride, offset=0, dtype=np.float32)

    # pointer of uv data
    # offset of uv's is the vertex x,y,z, which is 3 * 32bit float.
    offset = 3 * np.dtype(np.float32).itemsize
    uv_tr = BufferPointer(vb, count=2, stride=stride, offset=offset, dtype=np.float32)


Or use the entire array as a single data type

::

    from omgl.buffer import VertexBuffer, BufferPointer
    vertex_data = np.array([
        [ 1., 0.,-1.],
        [-1., 0.,-1.],
        [ 0., 1.,-1.],
    ], dtype=np.float32)
    vertices = VertexBuffer(vertex_data)

    # this data is 2 dimensional to make it easier to read
    # it could be 1 dimensional, with no code changes, if we wished
    uv_data = np.array([
        [1., 0.],
        [0., 0.],
        [0.5, 1.],
    ], dtype=np.float32)
    uvs = VertexBuffer(uv_data)


Texture Buffer's allow like access to 1 dimensional buffer data.
This is great for passing large amounts of random-access data to shaders.

::

    from omgl.buffer import TextureBuffer
    data = np.ones((32,32,4), dtype=np.float32)
    texture_buffer = TextureBuffer(data)
    texture = texture_buffer.texture

    texture.active_unit = 0
    texture.bind()



Shaders
-------

Shader and Program objects wrap GLSL shaders.
Attributes must be set at construction time.

::

    from omgl.shader import VertexShader, FragmentShader, Program
    # vertex shader
    vs = """
        #version 400
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

    # fragment shader
    fs = """
        #version 400
        uniform sampler2D in_diffuse_texture;
        in vec2 ex_uv;
        out vec4 out_color;
        void main(void) {
            out_color = texture(in_diffuse_texture, ex_uv);
        }
        """

    # create and link
    # specify attributes at link time
    program = Program([
        VertexShader(vs),
        FragmentShader(fs),
        ],
        in_position=1,
        in_uv=2,
    )

    # these values can be set automatically using a Pipeline
    with program:
        program.in_projection = np.eye(4)
        program.in_model_view = np.eye(4)
        # set the texture unit to read from
        program.in_diffuse_texture = 0


Or load shaders from a file

::

    from omgl.shader import FragmentShader, VertexShader, Program
    program = Program([
        VertexShader.open('assets/shaders/test.vs'),
        FragmentShader.open('assets/shaders/test.fs'),
        ],
        in_position=1,
        in_uv=2,
    )


Shader Programs automatically find and provide wrappers for their Uniform and
Attribute variables.
Uniform data can be read or set easily.

Variable's are loaded from OpenGL only when accessed, meaning you won't get any
pipeline stalls while loading shaders in parallel.


::

    from omgl.shader import FragmentShader, VertexShader, Program
    program = Program([
        VertexShader.open('assets/shaders/test.vs'),
        FragmentShader.open('assets/shaders/test.fs'),
        ],
        in_position=1,
        in_uv=2,
    )

    # get a variable directly
    program.in_position

    # get an attribute from the attributes dict
    program.attributes['in_position']

    # print a list of attribute variable names
    print(program.attributes.keys())

    # inspect an attribute
    print(program['in_position'].location)
    print(program['in_position'].dtype)
    print(program['in_position'].itemsize)
    print(program['in_position'].nbytes)
    print(program['in_position'].dimensions)
    print(program['in_position'].enum)
    print(program['in_position'].name)
    print(program['in_position'].enum)

    # get a uniform directly
    program.in_projection

    # get a uniform from the uniforms dict
    program.uniforms['in_projection']

    # print a list of uniform variable names
    print(program.uniforms.keys())

    # inspect a uniform
    print(program['in_projection'].location)
    print(program['in_projection'].dtype)
    print(program['in_projection'].itemsize)
    print(program['in_projection'].nbytes)
    print(program['in_projection'].dimensions)
    print(program['in_projection'].enum)
    print(program['in_projection'].name)
    print(program['in_projection'].enum)

    # print the current value of the uniform
    print(program['in_projection'].data)

    # set the value of the uniform
    program['in_projection'].data = np.eye(4)



Pipelines
---------

Pipelines provide a way to automatically link textures, values (uniforms) and
vertex data (attributes) to a shader program before rendering.

The Pipeline allows you to assign values to the shader program without worrying about it being bound or not at the time.

This lets you decouple the shader program from the renderable object itself.


::

    from OpenGL import GL
    from omgl.shader import FragmentShader, VertexShader, Program
    from omgl.buffer import VertexBuffer, VertexArray
    from omgl.pipeline.pipeline import Pipeline

    # shader program
    program = Program([
        VertexShader.open('assets/shaders/test.vs'),
        FragmentShader.open('assets/shaders/test.fs'),
        ],
        in_position=1,
        in_uv=2,
    )

    # vertex data
    data = np.array([
        [([ 1., 0.,-1.], [1., 0.])],
        [([-1., 0.,-1.], [0., 0.])],
        [([ 0., 1.,-1.], [.5, 1.])],
        ],
        dtype=[('in_position', np.float32, 3,),('in_uv', np.float32, 2,),]
    )
    vb = VertexBuffer(data)

    # bind the vertex attributes to a vertex array
    va = VertexArray()

    # bind the vertex array and notify it of our vertex pointers
    with va:
        # get the location of the attributes
        in_position = program.attributes.get('in_position').location
        va[in_position] = vb.pointers['in_position']

        in_uv = program.attributes.get('in_uv')
        va[in_uv] = vb.pointers['in_uv']


    # load our texture
    texture = Texture2D.open('assets/textures/formats/RGBA.png')

    # create a pipeline for our shader
    # the pipeline will automatically assign these uniforms to any matching
    # variable in our shader
    # we can pass any variables we want at construction time as named parameters
    pipeline = Pipeline(program,
        in_diffuse_texture=texture,
    )

    # we can also set any value after creation, there is no difference
    pipeline.in_projection = np.eye(4)
    pipeline.in_model_view = np.eye(4)
    # textures are automatically handled
    # variables that don't exist in the shader are ignored
    pipeline.this_variable_doesnt_exist = (1,2,3,4)

    # bind the pipeline
    # this will actually bind the shader program and push any values into it
    with pipeline:
        # tell the vertex array to render our vertex data as lists of triangles
        va.render(GL.GL_TRIANGLES)


Meshes
------------------

Meshes greatly simplify the boilerplate required to render an object
by wrapping a lot of the above functionality.
Meshes handle vertex arrays, shaders and pipelines for you.


::

    from OpenGL import GL
    from omgl.shader import FragmentShader, VertexShader, Program
    from omgl.buffer import VertexBuffer
    from omgl.pipeline.pipeline import Pipeline
    from omgl.mesh import Mesh

    # shader program
    program = Program([
        VertexShader.open('assets/shaders/test.vs'),
        FragmentShader.open('assets/shaders/test.fs'),
        ],
        in_position=1,
        in_uv=2,
    )

    # vertex data
    data = np.array([
        [([ 1., 0.,-1.], [1., 0.])],
        [([-1., 0.,-1.], [0., 0.])],
        [([ 0., 1.,-1.], [.5, 1.])],
        ],
        dtype=[('in_position', np.float32, 3,),('in_uv', np.float32, 2,),]
    )
    vb = VertexBuffer(data)

    # load our texture
    texture = Texture2D.open('assets/textures/formats/RGBA.png')

    # create a pipeline with our shader and our texture
    pipeline = Pipeline(program, in_diffuse_texture=texture)

    # create a mesh using our pipeline and vertex data
    mesh = Mesh(pipeline, **vb.pointers)

    # render the mesh automatically
    # we can pass in any frame-to-frame here as named arguments
    mesh.render(in_projection=np.eye(4), in_model_view=np.eye(4))


By default, meshes render all vertex data and use GL_TRIANGLES as the primitive
type.

This can be changed at mesh construction time.

::

    from omgl.buffer import IndexBuffer
    indices = IndexBuffer(np.array([1,2,3,4,5,6], dtype=np.uint32))
    mesh = Mesh(pipeline, indices=indices, primitive=GL.GL_TRIANGLE_STRIP)


If vertex buffer's contain mixed primitive types, then use multiple meshes
with different pointers into the data.
To control which elements are rendered, use either an IndexBuffer, or render from
the mesh's VertexArray directly.

::

    mesh.vertex_array.render(GL.GL_TRIANGLE_STRIP, start=5, count=10)
    mesh.vertex_array.render(GL.GL_TRIANGLES, start=20, count=6)


Authors
=======

* `Adam Griffiths <https://github.com/adamlwgriffiths>`_
