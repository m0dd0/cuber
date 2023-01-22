import logging
from typing import List, Dict, Tuple, Any

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
        appearance: str = "Prism-256",
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
                the voxel constructor. Defaults to "Prism-256".
            name (str, optional): The body name of the created voxel. Defaults to "voxel".
        """
        if shape == "cube":
            voxel_class = DirectCube
        elif shape == "sphere":
            voxel_class = DirectSphere
        else:
            raise ValueError("Invalid shape argument.")

        # delete the voxel from the world if it already exists and has a differnt type than
        # the voxel to add at this place
        voxel = self._voxels.get(coordinates)
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

    def delete_voxel(self, coordinates: Tuple[int]):
        """Deletes the voxel at the passed game coordinate by calling its delte() method.
        If there exists no voxel at the given position nothing happens. The voxel might also have been
        deleted already by an external processs. In this case the resulting error is logged and

        Args:
            coordinates (Tuple[int]): The position of the voxel in game coordinates.
        """
        success = False
        voxel = self._voxels.get(coordinates)
        if voxel is not None:
            try:
                voxel.delete()
                success = True
            except RuntimeError as _:
                logging.getLogger(__name__).warning(
                    f"Could not delete voxel at {coordinates} succesfully."
                )
            self._voxels.pop(coordinates)

        return success

    def clear(self):
        """Removes and deletes all voxels currently present in the world."""
        coords_to_delete = set(self._voxels.keys())
        for coord in coords_to_delete:
            self.delete_voxel(coord)

    def _number_of_changes(self, world_def: Dict[Tuple, Dict]) -> int:
        """Gets the number of voxels that must be changed or created in order to have the
        passed world definition. (emoving voxels is very fast, therfore we do not account them as change)

        Args:
            world_def (Dict[Tuple, Dict]): The representation of the new world as as
            {(x_game, y_game, z_game): add_voxel_params} dict. So e.g.
            {(0,0,0): {"voxel_class": DirectCube, "color": (255,0,0), "appearance": "Prism-256", name: "vox"}.

        Returns:
            int: The number of changes needed.
        """
        i = 0
        for coord, voxel_def in world_def.items():
            voxel = self._voxels.get(coord)

            if (
                not voxel
                or voxel.shape != voxel_def["shape"]
                or voxel.appearance != voxel_def["appearance"]
                or voxel.color != voxel_def["color"]
            ):
                i += 1

        # removing voxels is very fast, therfore we do not account them as change
        # for coord in set(self.get_coordinates()):
        #     if coord not in world_def.keys():
        #         i += 1

        return i

    def update(
        self,
        new_world_def: Dict[Tuple, Dict],
        progress_dialog: adsk.core.ProgressDialog = None,
        changes_for_dialog: int = None
        # progress_dialog_delay=0,
    ) -> bool:
        """Updates the world according to the passed new_world_def. The new world def is a
        {(x_game, y_game, z_game): {"shape":shape, "color":(r,g,b,o), "appearance":appearance, "name":name}} dict.
        This means that the keys define the position of the voxel while the values define the parameters passed to the
        add_voxel method.
        Voxels which are not present in the new_worls_def are deleted and for all voxels
        in the new_world_def the add_voxel method is called.

        Args:
            new_world_def (Dict[Tuple, Dict]): The representation of the new world as as
            {(x_game, y_game, z_game): add_voxel_params} dict. So e.g.
            {(0,0,0): {"shape": "cube", "color": (255,0,0), "appearance": "Prism-256", name: "vox"}.
            progress_dialog (adsk.core.ProgressDialog, optional): If a progress dialog is
                passed this is shown while adding the new voxels. Defaults to None.
            changes_for_dialog (int, optional): The number of voxels that must be created
                or changed in order to update the world until a progress_dialog is used. Gets ignored if
                no progress_dialog has been passed. Defaults to None which means that the progess_dialog
                is always used if given.

        Returns:
            bool: Whether the update was fully executed (can be aborted when giving progress_dialog).
        """
        coords_to_delete = set(self.get_coordinates()) - set(new_world_def.keys())
        for coord in coords_to_delete:
            self.delete_voxel(coord)

        cancelled = False

        if progress_dialog is None or (
            changes_for_dialog is not None
            and self._number_of_changes(new_world_def) < changes_for_dialog
        ):
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
        return list(self._voxels.keys())

    def get_current_world_def(self) -> Dict[str, Any]:
        """Returns the current world definition. The world definition contains a description of the properties
        of each voxel but is independent of the world configuration like offset, component or grid_size.
        I.e. it returns a dict in the form of:
        {(x_game,y_game,z_game):{"shape": shape, "color": (r,g,b,o), "appearance": appearnce, "name": name}}

        Returns:
            Dict[str, Any]: The serialized world definition.
        """
        world_def = {}
        for coord, voxel in self._voxels.items():
            # we do not use the voxel.serailize() method as it might contain more attributes than needed
            world_def[coord] = {
                "shape": voxel.shape,
                "color": voxel.color,
                "appearance": voxel.appearance,
                "name": voxel.name,
            }
        return world_def

    @property
    def grid_size(self):
        return self._grid_size

    def _rebuild(self, progress_dialog: adsk.core.ProgressDialog = None) -> bool:
        """Recreates all voxels in the world with the current world definition and the (new) world configuration.
        This should get executed when we change properties like grid_size.

        Args:
            progress_dialog (adsk.core.ProgressDialog, optional): If a progress dialog is
                passed this is shown while adding the new voxels. Defaults to None.

        Returns:
            bool: Whether the update was fully executed (can be aborted when giving progress_dialog).
        """
        current_world_def = self.get_current_world_def()
        self.clear()
        return self.update(current_world_def, progress_dialog)

    @property
    def component(self):
        return self._component

    @property
    def offset(self):
        return self._offset

    def set_grid_size(
        self, new_grid_size: int, progress_dialog: adsk.core.ProgressDialog = None
    ) -> bool:
        """Updates the voxel size attribute and rebuilds all voxels.

        Args:
            new_grid_size (int): The new grid size.
            progress_dialog (adsk.core.ProgressDialog, optional): If a progress dialog is
                passed this is shown while adding the new voxels. Defaults to None.

        Returns:
            bool: Whether the update was fully executed (can be aborted when giving progress_dialog).
        """
        if new_grid_size == self._grid_size:
            return

        self._grid_size = new_grid_size
        return self._rebuild(progress_dialog)
