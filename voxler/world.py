from typing import Any, List, Dict, Tuple

import adsk.core, adsk.fusion

from .voxels import DirectCube, Voxel


class VoxelWorld:
    def __init__(
        self,
        grid_size: float,
        component: adsk.fusion.Component,
        offset: Tuple[int] = (0, 0, 0),
    ):
        """A world contains a set of voxels. For the voxels the following conditions are
        ensured:
            - voxels have cubic and constnt size
            - a world existst in exctly one component
            - only one body per voxel at same time
            - working design and creation modes are determined by the used voxel classes
            - all voxel classes contain appearance and color and name property which are the only

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
        self._voxels = {}

    def add_voxel(
        self,
        coordinates: Tuple[int],
        voxel_class: Voxel = DirectCube,
        color: Tuple[int] = None,
        appearance: str = "Steel - Satin",
        additional_properties: Dict[str, Any] = None,
    ):
        """Adds a voxel to the world at the given game coordinates. Which kind of voxel
        gets added is determined by the passed Voxel class and the other parameters which
        get passed to the constructor of the voxel class.
        If the voxel already exists the voxel is updated or recreated if it has a different
        voxel type.

        Args:
            coordinates (Tuple[int]): The (x_game, y_game, z_game) coordinates of the voxel.
            voxel_class (Voxel, optional): The Voxel class which is used to build this voxel.
                Defaults to DirectCube.
            color (Tuple[int], optional): The (r,g,b,o) tuple which gets passed to the
                Voxel constructor. Defaults to None.
            appearance (str, optional): The name of the used appearance which gets passed to
                the voxel constructor. Defaults to "Steel - Satin".
            additional_properties (Dict[str, Any], optional): Additional properties which get
                passed to the voxel constructor. Defaults to None.
        """
        if additional_properties is None:
            additional_properties = {}

        voxel = self._voxels.get(coordinates)

        # delete the voxel from the world if it already exists and has a differnt type than
        # the voxel to add at this place
        if voxel is not None and voxel.__class__ != voxel_class:
            voxel.delete()
            self._voxels.pop(coordinates)

        # create/instatiate the voxel if its not exitant yet (or has been deleted dur to different type)
        if coordinates not in self._voxels:
            self._voxels[coordinates] = voxel_class(
                component=self._component,
                center=[
                    (c + o) * self.grid_size for c, o in zip(coordinates, self._offset)
                ],
                side_length=self.grid_size,
                appearance=appearance,
                color=color,
                **additional_properties
            )

        # if a voxel with the same type already exists at this coordintate onyl the appearnce
        # and color are changed if they differ.
        else:
            if appearance != voxel.appearance:
                voxel.appearance = appearance
            if color != voxel.color:
                voxel.color = color

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
        {(x_game, y_game, z_game): add_voxel_params} dict. This means that the keys define
        the position of the voxel while the values define the parameters passed to the
        add_voxel method.
        Voxels which are not present in the new_worls_def are deleted and for all voxels
        in the new_world_def the add_voxel method is called.

        Args:
            new_world_def (Dict[List, Dict]): The representation of the new world as as
            {(x_game, y_game, z_game): add_voxel_params} dict. So e.g.
            {(0,0,0): {"voxel_class": DirectCube, "color": (255,0,0), "appearance": "Steel - Satin", name "vox"}.
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

    # @grid_size.setter
    # def grid_size(self, new_grid_size):
    #     self._grid_size = new_grid_size

    @property
    def component(self):
        return self._component

    @property
    def offset(self):
        return self._offset
