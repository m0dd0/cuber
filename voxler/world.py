from typing import List, Dict

import adsk.core

from .voxels import DirectCube


class VoxelWorld:
    def __init__(self, grid_size, component, offset=(0, 0, 0)):
        # limitations and conditions:
        #       voxels have cubic and constnt size
        #       a world existst in exctly one component
        #       only one body per voxel at same time
        #       working design and creation modes are determined by the used voxel classes
        #       all voxel classes contain appearance and color and name property which are the only
        #       parameters that can be set by the user of the voxelWorld class

        self._grid_size = grid_size
        self._component = component
        self._offset = offset

        self._voxels = {}

    def add_voxel(
        self,
        coordinates,
        voxel_class=DirectCube,
        color=None,
        appearance="Steel - Satin",
        additional_properties=None,
    ):
        if additional_properties is None:
            additional_properties = {}

        voxel = self._voxels.get(coordinates)
        if voxel is not None and voxel.__class__ != voxel_class:
            voxel.delete()
            self._voxels.pop(coordinates)

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
        else:
            if appearance != voxel.appearance:
                voxel.appearance = appearance
            if color != voxel.color:
                voxel.color = color

    def remove_voxel(self, coordinates):
        voxel = self._voxels.get(coordinates)
        if voxel is not None:
            voxel.delete()
            self._voxels.pop(coordinates)

    def clear(self):
        for voxel in self._voxels.values():
            voxel.delete()

        self._voxels.clear()

    def update(
        self,
        new_world_def: Dict[List, Dict],
        progress_dialog: adsk.core.ProgressDialog = None,
        progress_dialog_delay=0,
    ):
        existing = self.get_coordinates()
        for coord in set(existing):
            if coord not in new_world_def.keys():
                self.remove_voxel(coord)

        if progress_dialog is None:
            for coord, voxel_def in new_world_def.items():
                self.add_voxel(coordinates=coord, **voxel_def)
        else:
            cancelled = False
            progress_dialog.show(
                progress_dialog.title,
                progress_dialog.message,
                0,
                len(new_world_def),
                progress_dialog_delay,
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

    @grid_size.setter
    def grid_size(self, new_grid_size):
        self._grid_size = new_grid_size

    @property
    def component(self):
        return self._component

    @property
    def offset(self):
        return self._offset