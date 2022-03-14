from abc import ABC, abstractmethod
from tkinter.messagebox import NO
from typing import Tuple, Dict, Any

import adsk.fusion, adsk.core


class Voxel(ABC):
    def __init__(
        self,
        component: adsk.fusion.Component,
        center: Tuple[int],
        side_length: float,
        color: Tuple[str] = None,
        appearance: str = "Steel - Satin",
    ):
        """Abstract Base class for all voxels. Sets the attributes and calls the _createy_body()
        method of the implementing subclass.

        Args:
            component (adsk.fusion.Component): The component into which the voxel is created.
                Cant be changed after initialization.
            center (Tuple[int]): The center point of the voxel as (x,y,z) tuple. The scale
                is according to the Fusion units. Cant be changed after initialization.
            side_length (float): The side length in Fusion units. Cant be changed after initialization.
            color (Tuple[str], optional): Color of the voxel as (r,g,b,o) tuple (0 to 255).
                Defaults to the standard appearance. Can be changed after initialization.
                Setter method must be implemented by the subclass.
            appearance (str, optional): The appearance of the voxel as name of the appearance
                in "Fusion 360 Appearance Library". Defaults to "Steel - Satin".
                Can be changed after initialization. Setter method must be implemented by the subclass.
        """
        # these are the attributes which cant be changed after initialization
        self._comp = component
        self._center = tuple(center)
        self._side_length = side_length
        self._color = tuple(color)
        self._appearance = appearance

        # create the body
        self._body = self._create_body()

    def delete(self) -> None:
        """Deletes the voxler instance. Same syntax for every subclass (DirectBodies and CustomGrphics)"""
        self._body.deleteMe()
        self._body = None

    @property
    def component(self) -> adsk.fusion.Component:
        """The Fusion360 Component which owns this voxel."""
        return self._comp

    @component.setter
    @abstractmethod
    def component(self, new_component: adsk.fusion.Component):
        raise NotImplementedError()

    @property
    def center(self) -> Tuple[float]:
        """The center point of the voxel as (x,y,z) tuple in Fusions default coordinates."""
        return self._center

    @center.setter
    @abstractmethod
    def center(self, new_center: Tuple[float]):
        raise NotImplementedError()

    @property
    def side_length(self) -> float:
        """The side length of the voxel."""
        return self._side_length

    @side_length.setter
    @abstractmethod
    def side_length(self, new_side_length: float):
        raise NotImplementedError()

    @property
    def body(self) -> adsk.fusion.BRepBody:
        """The Fusion BrePBody this voxel represents."""
        return self._body

    @property
    def appearance(self) -> str:
        """The name of the appearance as found in the Fuusion360 Material Library applied to the voxel."""
        return self._appearance

    @appearance.setter
    @abstractmethod
    def appearance(self):
        """Updates the appearance of the voxel by changing the actual apperance of the
        body behind the voxel.
        """
        raise NotImplementedError()

    @property
    def color(self) -> Tuple[int]:
        """The color as (r,g,b,o) tuple which is used to modify the applied appearance."""
        return self._color

    @color.setter
    @abstractmethod
    def color(self):
        """Updates the color of the voxel by changing the actual apperance/color of the
        body behind the voxel.
        """
        raise NotImplementedError()

    def _get_appearance(self) -> adsk.core.Appearance:
        """Utility method to get or create a (colored) appearance from the appearance and
        color attribute of the voxel.

        Returns:
            adsk.core.Appearance: The colored appearance to apply.
        """
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)

        base_appearance = app.materialLibraries.itemByName(
            "Fusion 360 Appearance Library"
        ).appearances.itemByName(self._appearance)

        if self._color is None:
            # no not use id since it is kept at creation of new custom apperance
            appearace_des = design.appearances.itemByName(base_appearance.name)
            return appearace_des

        # create the name of the colored appearance
        r, g, b, o = self._color
        custom_color_suffix = "__custom_"
        colored_appearance_name = (
            f"{self._appearance}{custom_color_suffix}r{r}g{g}b{b}o{o}"
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
        """Creates the Body depending on the used subclass. This method must be implemnted
        by each subclass and determines the shape of the coxel and how its created.
        This method is called in the cosntructor of the Voxel base class.

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError()

    # @abstractmethod
    # def serialize(self) -> Dict[str, Any]:
    #     """Returns a serializable dict which represents the voxel.
    #     All attributes are json serializable. The returned dict can be passed to the
    #     passed to a constructor of the same VoxelClass to duplicate this voxel.

    #     Returns:
    #         Dict[str, Any]: The serialized version of this xovel instance.
    #     """
    #     raise NotImplementedError()

    def recreate_body(self):
        self.delete()
        self._body = self._create_body()


class DirectVoxel(Voxel):
    def __init__(
        self,
        component: adsk.fusion.Component,
        center: Tuple[int],
        side_length: float,
        color: Tuple[str] = None,
        appearance: str = "Steel - Satin",
        name: str = "Voxel",
    ):
        """Abstract Base class for all voxels created as a direct brepbody with the TemporaryBrepManager.
        Ensures that the design is currently in DirectDesign mode.

        Args:
            component (adsk.fusion.Component): The component into which the voxel is created.
                Cant be changed after initialization.
            center (Tuple[int]): The center point of the voxel as (x,y,z) tuple. The scale
                is according to the Fusion units. Cant be changed after initialization.
            side_length (float): The side length in Fusion units. Cant be changed after initialization.
            color (Tuple[str], optional): Color of the voxel as (r,g,b,o) tuple (0 to 255).
                Defaults to the standard appearance. Can be changed after initialization.
                Setter method must be implemented by the subclass.
            appearance (str, optional): The appearance of the voxel as name of the appearance
                in "Fusion 360 Appearance Library". Defaults to "Steel - Satin".
                Can be changed after initialization. Setter method must be implemented by the subclass.
            name (str, optional): The name of the representing body in Fusion. Defaults to "voxel".
        """
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            raise RuntimeError(
                "A instance of a DirectVoxel can not be created in parameteric design environment."
            )

        super().__init__(component, center, side_length, color, appearance)

        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        if self._name != new_name:
            self._name = new_name
            self._body.name = new_name

    @Voxel.color.setter
    def color(self, new_color):
        new_color = tuple(new_color)
        if self._color != new_color:
            self._color = new_color
            self._body.appearance = self._get_appearance()

    @Voxel.appearance.setter
    def appearance(self, new_appearance_name):
        if new_appearance_name != self._appearance:
            self._appearance = new_appearance_name
            self._body.appearance = self._get_appearance()

    @Voxel.component.setter
    def component(self, new_component: adsk.fusion.Component):
        if new_component.id != self._component.id:
            self._component = new_component
            self.recreate_body()

    @Voxel.center.setter
    def center(self, new_center: Tuple[float]):
        new_center = tuple(new_center)
        if self._center != new_center:
            self._center = new_center
            self.recreate_body()

    @Voxel.side_length.setter
    def side_length(self, new_side_length: float):
        if new_side_length != self._side_length:
            self._side_length = new_side_length
            self.recreate_body()


class DirectCube(DirectVoxel):
    def __init__(
        self,
        component: adsk.fusion.Component,
        center: Tuple[int],
        side_length: float,
        color: Tuple[str] = None,
        appearance: str = "Steel - Satin",
        name: str = "Cube",
    ):
        """Instantiabale class for which represents a cubic voxel created as a direct brepbody with the TemporaryBrepManager.

        Args:
            component (adsk.fusion.Component): The component into which the voxel is created.
                Cant be changed after initialization.
            center (Tuple[int]): The center point of the voxel as (x,y,z) tuple. The scale
                is according to the Fusion units. Cant be changed after initialization.
            side_length (float): The side length in Fusion units. Cant be changed after initialization.
            color (Tuple[str], optional): Color of the voxel as (r,g,b,o) tuple (0 to 255).
                Defaults to the standard appearance. Can be changed after initialization.
                Setter method must be implemented by the subclass.
            appearance (str, optional): The appearance of the voxel as name of the appearance
                in "Fusion 360 Appearance Library". Defaults to "Steel - Satin".
                Can be changed after initialization. Setter method must be implemented by the subclass.
            name (str, optional): The name of the representing body in Fusion. Defaults to "cube".
        """
        super().__init__(component, center, side_length, color, appearance, name)

    def _create_body(self) -> adsk.fusion.BRepBody:
        """Creates a cube accorsing to the properties of the voxel as a BrepBody using the
        TemporaryBrepManager.

        Returns:
            adsk.fusion.BRepBody: The created BrepBody
        """
        new_body = self._comp.bRepBodies.add(
            adsk.fusion.TemporaryBRepManager.get().createBox(
                adsk.core.OrientedBoundingBox3D.create(
                    adsk.core.Point3D.create(*self._center),
                    adsk.core.Vector3D.create(1, 0, 0),
                    adsk.core.Vector3D.create(0, 1, 0),
                    self._side_length,
                    self._side_length,
                    self._side_length,
                )
            )
        )
        new_body.appearance = self._get_appearance()
        new_body.name = self._name
        return new_body


class DirectSphere(DirectVoxel):
    def __init__(
        self,
        component: adsk.fusion.Component,
        center: Tuple[int],
        side_length: float,
        color: Tuple[str] = None,
        appearance: str = "Steel - Satin",
        name: str = "Sphere",
    ):
        """Instantiabale class for which represents a spheric voxel created as a direct brepbody with the TemporaryBrepManager.

        Args:
            component (adsk.fusion.Component): The component into which the voxel is created.
                Cant be changed after initialization.
            center (Tuple[int]): The center point of the voxel as (x,y,z) tuple. The scale
                is according to the Fusion units. Cant be changed after initialization.
            side_length (float): The side length in Fusion units. Cant be changed after initialization.
            color (Tuple[str], optional): Color of the voxel as (r,g,b,o) tuple (0 to 255).
                Defaults to the standard appearance. Can be changed after initialization.
                Setter method must be implemented by the subclass.
            appearance (str, optional): The appearance of the voxel as name of the appearance
                in "Fusion 360 Appearance Library". Defaults to "Steel - Satin".
                Can be changed after initialization. Setter method must be implemented by the subclass.
            name (str, optional): The name of the representing body in Fusion. Defaults to "Sphere".
        """
        super().__init__(component, center, side_length, color, appearance, name)

    def _create_body(self) -> adsk.fusion.BRepBody:
        """Creates a sphere accorsing to the properties of the voxel as a BrepBody using the
        TemporaryBrepManager.

        Returns:
            adsk.fusion.BRepBody: The created BrepBody
        """
        new_body = self._comp.bRepBodies.add(
            adsk.fusion.TemporaryBRepManager.get().createSphere(
                adsk.core.Point3D.create(*self._center), self._side_length / 2
            )
        )
        new_body.appearance = self._get_appearance()
        new_body.name = self._name
        return new_body


# region
# class CGVoxel(Voxel):
#     def __init__(
#         self,
#         component,
#         center,
#         side_length,
#         color=(255, 0, 0, 255),
#         appearance=None,
#         cg_group_id="voxler",
#     ):
#         # find or create the custom grapohics group
#         # this needs to be set before callnig the parent constructor because
#         # the apretn contructor will call _create_body which depends on self._graphics
#         self._graphics = None
#         for cg_group in component.customGraphicsGroups:
#             if cg_group.id == cg_group_id:
#                 self._graphics = cg_group
#         if self._graphics is None:
#             self._graphics = component.customGraphicsGroups.add()
#             self._graphics.id = cg_group_id

#         super().__init__(component, center, side_length, color, appearance)

#     def _get_cg_appearannce(self):
#         if self.appearance is None:
#             if self.color is None:
#                 return adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
#                     adsk.core.Color.create(0, 0, 0, 255)
#                 )
#             else:
#                 return adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
#                     adsk.core.Color.create(*self.color)
#                 )
#         else:
#             return adsk.fusion.CustomGraphicsAppearanceColorEffect.create(
#                 self._get_appearance()
#             )

#     def serialize(self) -> Dict[str, Any]:
#         # TODO
#         return super().serialize()

#     @Voxel.color.setter
#     def color(self, new_color):
#         self._color = new_color
#         self._body.color = self._get_cg_appearannce()

#     @Voxel.appearance.setter
#     def appearance(self, appearance_name):
#         self._appearance = appearance_name
#         self._body.color = self._get_cg_appearannce()


# class CGCube(CGVoxel):
#     # def __init__(self, component, center, side_length, color, appearance, cg_group_id):
#     #     super().__init__(component, center, side_length, color, appearance, cg_group_id)

#     def _create_body(self):
#         return self._graphics.addBRepBody(
#             adsk.fusion.TemporaryBRepManager.get().createBox(
#                 adsk.core.OrientedBoundingBox3D.create(
#                     adsk.core.Point3D.create(*self._center),
#                     adsk.core.Vector3D.create(1, 0, 0),
#                     adsk.core.Vector3D.create(0, 1, 0),
#                     self._side_length,
#                     self._side_length,
#                     self._side_length,
#                 )
#             )
#         )


# class CGSphere(CGVoxel):
#     # def __init__(self, component, center, side_length, color, appearance, cg_group_id):
#     #     super().__init__(component, center, side_length, color, appearance, cg_group_id)

#     def _create_body(self):
#         return self._graphics.addBRepBody(
#             adsk.fusion.TemporaryBRepManager.get().createSphere(
#                 adsk.core.Point3D.create(*self._center), self._side_length / 2
#             )
#         )
# endregion
