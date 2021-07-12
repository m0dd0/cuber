import logging
import traceback

import adsk.fusion, adsk.core


class DirectCube:
    def __init__(
        self,
        component,
        center,
        side_length,
        color=None,
        material=None,
        base_feature=None,
    ):

        # these are the attributes which cant be changed after initialization
        self._comp = component
        self._center = center
        self._side_length = side_length
        self._base_feature = base_feature

        # create the cube itself
        brep = adsk.fusion.TemporaryBRepManager.get().createBox(
            adsk.core.OrientedBoundingBox3D.create(
                adsk.core.Point3D.create(*self._center),
                adsk.core.Vector3D.create(1, 0, 0),
                adsk.core.Vector3D.create(0, 1, 0),
                self._side_length,
                self._side_length,
                self._side_length,
            )
        )

        # add it to the design
        if self._base_feature is not None:
            self._body = self._comp.bRepBodies.add(brep, self._base_feature)
        else:
            self._body = self._comp.bRepBodies.add(brep)

        # these are the attributes that can be manipulated after creation
        # therefore the setter functions are used to set them
        self._material = None
        self.material = self._body.appearance.name if material is None else material

        self._color = None
        self.color = color

    def _get_appearance(self):
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)

        if self._color is not None:
            return design.appearances.itemByName(self._material)

        r, g, b, o = self._color

        # create the name of the colored appearance
        custom_color_suffix = "__custom_"
        colored_appearance_name = (
            f"{self._material}{custom_color_suffix}r{r}g{g}b{b}o{o}"
        )

        # create or get the colored appearance
        colored_appearance = design.appearances.itemByName(colored_appearance_name)
        if colored_appearance is None:
            colored_appearance = design.appearances.addByCopy(
                app.materialLibraries.itemByName(
                    "Fusion 360 Appearance Library"
                ).appearances.itemByName(self._material),
                colored_appearance_name,
            )
            colored_appearance.appearanceProperties.itemByName(
                "Color"
            ).value = adsk.core.Color.create(r, g, b, o)

        return colored_appearance

    @property
    def component(self):
        return self._comp

    @property
    def center(self):
        return self._center

    @property
    def side_length(self):
        return self._side_length

    @property
    def body(self):
        return self._body

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, new_color):
        self._color = new_color
        self._body.appearance = self._get_appearance()

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, material_name):
        self._material = material_name
        self._body.appearance = self._get_appearance()

    def delete(self):
        self._body.deleteMe()


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component

        cube = DirectCube(comp, (0, 0, 0), 1)

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


# begin region
# class Sphere:
#     def __init__(self, component, center, diameter, color, material, build_type):
#         pass

#     def delete(self):
#         pass


# class VoxelWorld:
#     def __init__(self, grid_size, component):
#         super().__init__()

#         self._bodies = {(x, y, z): Block}  # x,y,z in game/grid/voxel coordinates

#     def add_shape(self, shape_class, position, material, color):
#         body = self._bodies.get(position)
#         if body is None:
#             body = shape_class(self.component, self.grid_size, material, color)
#             self._bodies[position] = body
#         else:
#             if isinstance(body, shape_class):
#                 body.material = material
#                 body.color = color
#             else:
#                 body.delete()
#                 body = Block(self.component, self.grid_size, material, color)
#                 self._bodies[position] = body
#         return body

#     def add_block(self, position, material, color):
#         return self.add_shape(Block, position, material, color)

#     def add_sphere(self, position, material, color):
#         pass

#     def update_worls(self, elements: Dict[position:(shape, material, color)]):
#         for pos in elements.keys():
#             self.add_shape(shape, material, color)
#         for pos in self._elements:
#             if pos not in elements:
#                 self._elements[pos].delete()
#                 self._elements.pop(pos)
#             # if pos in self._bodies:


# class Game:
#     def get_voxels(self):
#         voxels = {(0, x, y): (Block, self.material)}
# voxels = [Voxel(pos, field.color) for pos in field.elements] + []
# end region
