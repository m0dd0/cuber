import logging
import traceback
from time import perf_counter
from abc import ABC, abstractmethod

import adsk.fusion, adsk.core


class Voxel(ABC):
    def __init__(
        self,
        component,
        center,
        side_length,
        color=None,
        material=None,
        # base_feature=None, # is not setable in direct design
        name="Voxel",
    ):
        super().__init__()
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            raise RuntimeError(
                "A Instance of a DirectCube can not be created in parameteric design environment."
            )

        # these are the attributes which cant be changed after initialization
        self._comp = component
        self._center = center
        self._side_length = side_length
        self._color = color
        self._material = material
        self._name = name
        # self._base_feature = base_feature

        self._body = self._comp.bRepBodies.add(self._create_body())

    def _get_appearance(self):
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)

        base_appearance = app.materialLibraries.itemByName(
            "Fusion 360 Appearance Library"
        ).appearances.itemByName(self._material)

        if self._color is None:
            return base_appearance

        # create the name of the colored appearance
        r, g, b, o = self._color
        custom_color_suffix = "__custom_"
        colored_appearance_name = (
            f"{self._material}{custom_color_suffix}r{r}g{g}b{b}o{o}"
        )

        # create or get the colored appearance
        colored_appearance = design.appearances.itemByName(colored_appearance_name)
        if colored_appearance is None:
            colored_appearance = design.appearances.addByCopy(
                base_appearance,
                colored_appearance_name,
            )
            colored_appearance.appearanceProperties.itemByName(
                "Color"
            ).value = adsk.core.Color.create(r, g, b, o)

        return colored_appearance

    @abstractmethod
    def _create_body(self):
        raise NotImplementedError()

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

    @property
    def name(self):
        return self._name


#     @name.setter
#     def name(self, new_name):
#         self._name = new_name
#         self._body.name = new_name

#     @color.setter
#     def color(self, new_color):
#         self._color = new_color
#         self._body.appearance = self._get_appearance()

#     @property
#     def material(self):
#         return self._material

#     @material.setter
#     def material(self, material_name):
#         self._material = material_name
#         self._body.appearance = self._get_appearance()

#     def delete(self):
#         self._body.deleteMe()


# class DirectVoxel(Voxel):
#     pass


# class CubeVoxel(Voxel):
#     pass


# class DirectCube(DirectVoxel, CubeVoxel):
#     pass


class DirectCube(Voxel):
    def __init__(
        self,
        component,
        center,
        side_length,
        color=None,
        material=None,
        name="Cube",
    ):
        super().__init__(component, center, side_length, color, material, name)

    def _create_body(self):
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
        return brep


# class DirectSphere(DirectVoxel):
#     def __init__(
#         self,
#         component,
#         center,
#         diameter,
#         color,
#         material,
#         name,
#     ):
#         super().__init__()
#         app = adsk.core.Application.get()
#         design = adsk.fusion.Design.cast(app.activeProduct)
#         if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
#             raise RuntimeError(
#                 "A Instance of a DirectCube can not be created in parameteric design environment."
#             )

#         # these are the attributes which cant be changed after initialization
#         self._comp = component
#         self._center = center
#         self._diameter = diameter

#         # create the sphere itself
#         brep = adsk.fusion.TemporaryBRepManager.get().createSphere(
#             adsk.core.Point3D.create(*self._center), self._diameter / 2
#         )

#         self._body = self._comp.bRepBodies.add(brep)

#         # these are the attributes that can be manipulated after creation
#         # therefore the setter functions are used to set them
#         self._material = self._body.appearance.name if material is None else material
#         self._color = color
#         self._name = name


class VoxelWorld:
    def __init__(self, grid_size, component):
        # limitations and conditions:
        #       voxels have cubic and constnt size
        #       a world existst in exctly one component
        #       only one body per voxel at same time
        #       working design modes are determined by the used voxel classes
        #       all voxel classes contain material and color and name property

        self._grid_size = grid_size
        self._component = component

        self._voxels = {}

    def add_voxel(
        self, coordinates, voxel_class=DirectCube, color=None, material=None, name=None
    ):
        voxel = self._voxels.get(coordinates)
        if voxel is not None and voxel.__class__ != voxel_class:
            voxel.delete()
            self._voxels.pop(coordinates)

        if coordinates not in self._voxels:
            voxel_class(
                component=self._component,
                center=[c * self.grid_size for c in coordinates],
                side_length=self.grid_size,
                material=material,
                color=color,
                name=name,
            )
        else:
            if material != voxel.material:
                voxel.material = material
            if color != voxel.color:
                voxel.color = color
            if name != voxel.name:
                voxel.name = name

    def remove_voxel(self, coordinates):
        voxel = self._voxels.get(coordinates)
        if voxel is not None:
            voxel.delete()
            self._voxels.pop(coordinates)

    def clear_world(self):
        for voxel in self._voxels.values():
            voxel.delete()

        self._voxels.clear()

    def update(self, new_world_def):
        existing = self.get_coordinates()
        for coord in existing:
            if coord not in new_world_def.keys():
                self.remove_voxel(coord)

        for coord, voxel_def in new_world_def.items():
            self.add_voxel(*voxel_def)

    # do not return the full _voxels dict somewhere to ensure it doesnt get
    # manipulated wrong. Instead these methods should be used.
    def get_voxel(self, coordinates):
        return self._voxels.get(coordinates)

    def get_all_voxels(self):
        return self._voxels.values()

    def get_coordinates(self):
        return self._voxels.keys()

    def to_json(self):
        raise NotImplementedError()

    def from_json(self, new_world_json):
        # ...
        # self.update(d)
        raise NotImplementedError()

    @property
    def grid_size(self):
        return self._grid_size

    @property
    def component(self):
        return self._component


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component

        times = []

        for i in range(10):
            # start = perf_counter()
            # DirectCube(comp, (-i, i, -i), 1, (0, 0, 0, 0), "Pine")
            # 0.025
            # DirectCube(comp, (-i, i, -i), 1)
            # 0.025
            cube = DirectCube(comp, (-i, i, -i), 1)
        #     start = perf_counter()
        #     cube.color = (255, 0, 0, 255)
        #     times.append(perf_counter() - start)
        # print(sum(times) / len(times))

    except:
        print("Failed:\n{}".format(traceback.format_exc()))


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
