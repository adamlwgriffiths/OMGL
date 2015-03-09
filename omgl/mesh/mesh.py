

class Mesh(object):
    def __init__(self, submeshes):
        self._submeshes = submeshes or []

    def render(self, **uniforms):
        for submesh in self._submeshes:
            submesh.render(**uniforms)
