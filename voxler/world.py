from typing import List, Dict, Tuple

import adsk.core, adsk.fusion

from .voxels import DirectCube, DirectSphere, Voxel


class VoxelWorld:
    def __init__(
        self,
        grid_size: float,
        component: adsk.fusion.Component,
        offset: Tuple[int] = (0, 0, 0),
    ):
        """A world contains a set of voxels. For the voxels the following conditions are
        ensured:
            - voxels have cubic and constantt size (outer bounding box)
            - a world existst in exctly one component
            - only one body per voxel at same time
            - working design and creation modes are determined by the used voxel classes
            - only DirectVoxels which accept the parameters {color, appearance, name} besides
                center and side_length are possible

        In general the position of voxels are given in game coordinates which represents the
        distance from the offset to the center of the voxel in multitudes of the grid size.
        Their actual position is calculated by (offset+game_coord)*grid_size.

        Args:
            grid_size (float): The size (side length) a voxel body can have at max.
            component (adsk.fusion.Component): The component into which the bodies/voxels are created.
            offset (Tuple[int], optional): The offset which is added to the center of each created voxel.
                The offset is measure in voxel units aka the grid size. Defaults to (0, 0, 0).
        """

        self._grid_size = grid_size
        self._component = component
        self._offset = offset

        # {(x_game,y_game,z_game):Voxel} main dict representing/tracking all the voxels in the world
        self._voxels: Dict[Tuple[int], Voxel] = {}

    def get_real_center(self, game_coords: Tuple[int]) -> Tuple[float]:
        """Calculates the actual coordinate of the center in Fusion for the given game_coord
        w.r.t to the grid size and offset of the world.

        Args:
            game_coords (Tuple[int]): The game coordiante as (x,y,z) tuple for which the
                real world coordinate is calculated.

        Returns:
            Tuple[float]: The real world coordinate as (x,y,z) tuple.
        """
        return tuple(
            [(c + o) * self.grid_size for c, o in zip(game_coords, self._offset)]
        )

    def add_voxel(
        self,
        coordinates: Tuple[int],
        shape: str = "cube",
        color: Tuple[int] = None,
        appearance: str = "Steel - Satin",
        name: str = "voxel",
    ):
        """Adds a (direct) voxel to the world at the given game coordinates. The properties
        of the voxels are determined by the passed argumnets.
        If the voxel already exists the voxel is updated or recreated if it has a different
        voxel type.

        Args:
            coordinates (Tuple[int]): The (x_game, y_game, z_game) coordinates of the voxel.
            shape (str, optional): The shape of the added voxel. Possible values are "cube"
                which results in a DirectCube voxel beeing instantiaed and "sphere" which
                results in a DirectSphere beeing instantiated. Defaults to "cube".
            color (Tuple[int], optional): The (r,g,b,o) tuple which gets passed to the
                Voxel constructor. Defaults to None.
            appearance (str, optional): The name of the used appearance which gets passed to
                the voxel constructor. Defaults to "Steel - Satin".
            name (str, optional): The body name of the created voxel. Defaults to "voxel".
        """
        voxel = self._voxels.get(coordinates)

        if shape == "cube":
            voxel_class = DirectCube
        elif shape == "sphere":
            voxel_class = DirectSphere
        else:
            raise ValueError("Invalid shape argument.")

        # delete the voxel from the world if it already exists and has a differnt type than
        # the voxel to add at this place
        if voxel is not None and voxel.__class__ != voxel_class:
            voxel.delete()
            self._voxels.pop(coordinates)

        # create/instatiate the voxel if its not exitant yet (or has been deleted dur to different type)
        if coordinates not in self._voxels:
            self._voxels[coordinates] = voxel_class(
                component=self._component,
                center=self.get_real_center(coordinates),
                side_length=self.grid_size,
                appearance=appearance,
                color=color,
                name=name,
            )

        # if a voxel with the same type already exists at this coordintate onyl the appearnce
        # and color are changed if they differ.
        else:
            # applying equal attributes is prevented in setters of voxel class
            voxel.appearance = appearance
            voxel.color = color
            voxel.name = name

    def remove_voxel(self, coordinates: Tuple[int]):
        """Deletes the voxel at the passed game coordinate by calling its delte() method.
        If there exists no voxel at the given position nothing happens..

        Args:
            coordinates (Tuple[int]): The position of the voxel in game coordinates.
        """
        voxel = self._voxels.get(coordinates)
        if voxel is not None:
            voxel.delete()
            self._voxels.pop(coordinates)

    def clear(self):
        """Removes and deletes all voxels currently present in the world."""
        for voxel in self._voxels.values():
            voxel.delete()

        self._voxels.clear()

    def update(
        self,
        new_world_def: Dict[List, Dict],
        progress_dialog: adsk.core.ProgressDialog = None,
        # progress_dialog_delay=0,
    ) -> bool:
        """Updates the world according to the passed new_world_def. The new world def is a
        {(x_game, y_game, z_game): {"shape":shape, "color":(r,g,b,o), "appearance":appearance, "name":name}} dict.
        This means that the keys define the position of the voxel while the values define the parameters passed to the
        add_voxel method.
        Voxels which are not present in the new_worls_def are deleted and for all voxels
        in the new_world_def the add_voxel method is called.

        Args:
            new_world_def (Dict[List, Dict]): The representation of the new world as as
            {(x_game, y_game, z_game): add_voxel_params} dict. So e.g.
            {(0,0,0): {"voxel_class": DirectCube, "color": (255,0,0), "appearance": "Steel - Satin", name: "vox"}.
            progress_dialog (adsk.core.ProgressDialog, optional): If a progress dialog is
                passed this is shown while adding the new voxels. Defaults to None.

        Returns:
            bool: Whether the update was fully executed (can be aborted when giving progress_dialog).
        """
        existing = self.get_coordinates()
        for coord in set(existing):
            if coord not in new_world_def.keys():
                self.remove_voxel(coord)

        cancelled = False

        if progress_dialog is None:
            for coord, voxel_def in new_world_def.items():
                self.add_voxel(coordinates=coord, **voxel_def)
        else:
            progress_dialog.show(
                progress_dialog.title,
                progress_dialog.message,
                0,
                len(new_world_def),
                # progress_dialog_delay,
            )
            for i, (coord, voxel_def) in enumerate(new_world_def.items()):
                if progress_dialog.wasCancelled:
                    cancelled = True
                    break
                self.add_voxel(coordinates=coord, **voxel_def)
                progress_dialog.progressValue = i + 1
            progress_dialog.hide()

        return not cancelled

    # do not return the full _voxels dict somewhere to ensure it doesnt get
    # manipulated wrong. Instead these methods should be used.
    def get_voxel(self, coordinates: Tuple[int]) -> Voxel:
        """Returns the voxel instance which represnets the body at the provided game coordinate.

        Args:
            coordinates (Tuple[int]): The (x_game, y_game, z_game) coordinates of the voxel.

        Returns:
            Voxel: The voxel instance at this position.
        """
        return self._voxels.get(coordinates)

    def get_all_voxels(self) -> List[Voxel]:
        """All voxel instances which are managed by this world.

        Returns:
            List[Voxel]: All voxel instances which are managed by this world.
        """
        return list(self._voxels.values())

    def get_coordinates(self) -> List[Tuple[int]]:
        """Returns a list of all game coordinates tuple which are "occupied" by a voxel.

        Returns:
            List[Tuple[int]]: The list of game coorsintates of existing voxels in the game.
        """
        return self._voxels.keys()

    @property
    def grid_size(self):
        return self._grid_size

    def _rebuild_voxel(self, game_coord: Tuple[int], voxel: Voxel) -> Voxel:
        """Recreaes the given voxel with the same properties. For center and grid size
        the values according to this worls instance are used.

        Args:
            game_coord (Tuple[int]): The game coordinate of the voxel to recreate.
            voxel (Voxel): The voxel to recreate.

        Returns:
            Voxel: The recreatd / updated voxel.
        """
        # we do not simply use the setters as this would rebuild the body for every assignemnt
        new_voxel = voxel.__class__(
            self._component,
            self.get_real_center(game_coord),
            self._grid_size,
            voxel.color,
            voxel.appearance,
            voxel.name,
        )
        voxel.delete()
        return new_voxel

    def _rebuild(self):
        """Recreates all voxels in the world. This shoulf get executed when we change properties
        like grid_size or offset as it invokes the (efficient) rebuilf of all voxels.
        """
        self._voxels = {
            game_coord: self._rebuild_voxel(game_coord, voxel)
            for game_coord, voxel in self._voxels.items()
        }

    @grid_size.setter
    def grid_size(self, new_grid_size):
        self._grid_size = new_grid_size
        self._rebuild()

    @property
    def component(self):
        return self._component

    @property
    def offset(self):
        return self._offset
