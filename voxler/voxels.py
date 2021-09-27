from abc import ABC, abstractmethod

import adsk.fusion, adsk.core


class Voxel(ABC):
    def __init__(
        self,
        component,
        center,
        side_length,
        color=None,
        appearance="Steel - Satin",
    ):
        # these are the attributes which cant be changed after initialization
        self._comp = component
        self._center = center
        self._side_length = side_length
        self._color = color
        self._appearance = appearance

        # create the body
        self._body = self._create_body()

        # call the setter methods to apply the properties
        self.appearance = self._appearance
        self.color = self._color

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
    def appearance(self):
        return self._appearance

    @property
    def color(self):
        return self._color

    def _get_appearance(self):
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)

        base_appearance = app.materialLibraries.itemByName(
            "Fusion 360 Appearance Library"
        ).appearances.itemByName(self._appearance)

        if self._color is None:
            return base_appearance

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
        raise NotImplementedError()

    @abstractmethod
    def delete(self):
        raise NotImplementedError()

    @appearance.setter
    @abstractmethod
    def appearance(self):
        raise NotImplementedError()

    @color.setter
    @abstractmethod
    def color(self):
        raise NotImplementedError()


class DirectVoxel(Voxel):
    def __init__(
        self,
        component,
        center,
        side_length,
        color,
        appearance,
        name="Voxel",
    ):
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            raise RuntimeError(
                "A instance of a DirectVoxel can not be created in parameteric design environment."
            )

        super().__init__(component, center, side_length, color, appearance)

        # name is only supported by DirectVoxels, not for CGVoxesl
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name
        self._body.name = new_name

    @color.setter
    def color(self, new_color):
        self._color = new_color
        self._body.appearance = self._get_appearance()

    @appearance.setter
    def appearance(self, appearance_name):
        self._appearance = appearance_name
        self._body.appearance = self._get_appearance()

    def delete(self):
        self._body.deleteMe()


class DirectCube(DirectVoxel):
    def __init__(
        self,
        component,
        center,
        side_length,
        color=None,
        appearance="Steel - Satin",
        name="Cube",
    ):
        super().__init__(component, center, side_length, color, appearance, name)

    def _create_body(self):
        return self._comp.bRepBodies.add(
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


class DirectSphere(DirectVoxel):
    def __init__(
        self,
        component,
        center,
        side_length,
        color=None,
        appearance="Steel - Satin",
        name="Sphere",
    ):
        super().__init__(component, center, side_length, color, appearance, name)

    def _create_body(self):
        return adsk.fusion.TemporaryBRepManager.get().createSphere(
            adsk.core.Point3D.create(*self._center), self._side_length / 2
        )


class CGVoxel(Voxel):
    def __init__(self, component, center, side_length, color, appearance):
        super().__init__(component, center, side_length, color, appearance)
        # self._graphics = self._comp.

    def delete(self):
        pass

    @color.setter
    def color(self, new_color):
        pass

    @appearance.setter
    def appearance(self, appearance_name):
        pass


class CGCube(CGVoxel):
    def __init__(self, component, center, side_length, color, appearance):
        super().__init__(component, center, side_length, color, appearance)

    def _create_body(self):
        self._graphics.addBrepBody(
            adsk.fusion.TemporaryBRepManager.get().createSphere(
                adsk.core.Point3D.create(*self._center), self._side_length / 2
            )
        )


class CGSphere(CGVoxel):
    def __init__(self, component, center, side_length, color, appearance):
        super().__init__(component, center, side_length, color, appearance)

    def _create_body(self):
        pass