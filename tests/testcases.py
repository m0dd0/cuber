import traceback
from collections import defaultdict
from time import perf_counter
from typing import List, Callable

import adsk.core, adsk.fusion

from .. import voxler as vox

app = adsk.core.Application.get()
ui = app.userInterface
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent


# TODO rewrite


def execute_cases(cases: List[Callable]):
    """Executes the passed functions in a controlled environment and logs some
        data about their axacution.
    Args:
        cases (List[Callable]): A list of the testfuctions to execute.
    Returns:
        dict: A dictionairy with the test resulte mapped to the function name.
    """
    results = defaultdict(dict)
    for case in cases:
        try:
            print(f"{f' {case.__name__} ':{'#'}^{60}}")
            start = perf_counter()
            case()
            results[case.__name__]["elapsed_time"] = perf_counter() - start
            results[case.__name__]["passed"] = True
        except:
            results[case.__name__]["elapsed_time"] = -1
            results[case.__name__]["passed"] = False
            print(traceback.format_exc())

    return results


def test_driect_cube_creation():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test direct cube creation"

    cube = vox.DirectCube(comp, (0, 0, 0), 1)
    cube = vox.DirectCube(comp, (0, 5, 0), 2)
    cube = vox.DirectCube(comp, (2, 0, 0), 1, (255, 0, 0, 255))
    cube = vox.DirectCube(comp, (4, 0, 0), 1, (0, 255, 0, 255))
    cube = vox.DirectCube(comp, (6, 0, 0), 1, appearance="Oak")
    cube = vox.DirectCube(comp, (8, 0, 0), 1, (255, 0, 0, 255), appearance="Oak")
    cube = vox.DirectCube(
        comp, (10, 0, 0), 1, (255, 0, 0, 255), appearance="Oak", name="name"
    )
    cube = vox.DirectCube(comp, (12, 0, 0), 1)
    cube.color = (255, 0, 0, 255)
    cube.appearance = "Oak"
    cube.name = "name2"


def test_direct_sphere_creation():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test direct sphere creation"

    sphere = vox.DirectSphere(comp, (0, 0, 0), 1)
    sphere = vox.DirectSphere(comp, (0, 5, 0), 2)
    sphere = vox.DirectSphere(comp, (2, 0, 0), 1, (255, 0, 0, 255))
    sphere = vox.DirectSphere(comp, (4, 0, 0), 1, (0, 255, 0, 255))
    sphere = vox.DirectSphere(comp, (6, 0, 0), 1, appearance="Oak")
    sphere = vox.DirectSphere(comp, (8, 0, 0), 1, (255, 0, 0, 255), appearance="Oak")
    sphere = vox.DirectSphere(
        comp, (10, 0, 0), 1, (255, 0, 0, 255), appearance="Oak", name="name"
    )

    sphere = vox.DirectSphere(comp, (12, 0, 0), 1)
    sphere.color = (255, 0, 0, 255)
    sphere.appearance = "Oak"
    sphere.name = "name2"


# def test_cg_cube_creation():
#     comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
#     comp.name = "test cg cube creation"

#     cube = vox.CGCube(comp, (0, 0, 0), 1)
#     cube = vox.CGCube(comp, (0, 5, 0), 2)
#     cube = vox.CGCube(comp, (2, 0, 0), 1, color=None, appearance=None)
#     cube = vox.CGCube(comp, (4, 0, 0), 1, (0, 255, 0, 255))
#     cube = vox.CGCube(comp, (6, 0, 0), 1, appearance="Oak", color=None)
#     cube = vox.CGCube(comp, (8, 0, 0), 1, (255, 0, 0, 255), appearance="Oak")
#     cube = vox.CGCube(
#         comp, (10, 0, 0), 1, (255, 0, 0, 255), appearance="Oak", cg_group_id="asdasd"
#     )
#     cube = vox.CGCube(comp, (12, 0, 0), 1)
#     cube.color = (255, 0, 0, 255)
#     cube.appearance = "Oak"

#     cube = vox.CGCube(comp, (15, 0, 0), 1)
#     cube.delete()


# def test_cg_sphere_creation():
#     comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
#     comp.name = "test cg sphere creation"

#     sphere = vox.CGSphere(comp, (0, 0, 0), 1)
#     sphere = vox.CGSphere(comp, (0, 5, 0), 2)
#     sphere = vox.CGSphere(comp, (2, 0, 0), 1, color=None, appearance=None)
#     sphere = vox.CGSphere(comp, (4, 0, 0), 1, (0, 255, 0, 255))
#     sphere = vox.CGSphere(comp, (6, 0, 0), 1, appearance="Oak", color=None)
#     sphere = vox.CGSphere(comp, (8, 0, 0), 1, (255, 0, 0, 255), appearance="Oak")
#     sphere = vox.CGSphere(
#         comp, (10, 0, 0), 1, (255, 0, 0, 255), appearance="Oak", cg_group_id="asdasd"
#     )
#     sphere = vox.CGSphere(comp, (12, 0, 0), 1)
#     sphere.color = (255, 0, 0, 255)
#     sphere.appearance = "Oak"

#     sphere = vox.CGSphere(comp, (15, 0, 0), 1)
#     sphere.delete()


def test_voxel_world_basic():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test voxel world"

    world = vox.VoxelWorld(1, comp)
    for i in range(10):
        world.add_voxel((0, 0, i), "cube", (0, 0, 100 + i * 10, 255), "Oak")
        world.add_voxel((0, i, 0), "cube", (0, 100 + i * 10, 0, 255), "Oak")
        # world.add_voxel((0, -i, 0), vox.CGCube, (0, 100 + i * 10, 0, 255), "Oak")
        # world.add_voxel((0, 0, -i), vox.CGSphere, (0, 100 + i * 10, 0, 255), "Oak")


def test_world_color_change():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test world color change"

    world = vox.VoxelWorld(1, comp)
    for i in range(10):
        world.add_voxel((0, 0, i), "cube", (0, 0, 255, 255), "Oak")

    for i in range(5):
        world.add_voxel((0, 0, 2 * i), "cube", (255, 0, 0, 255), "Oak")


def test_world_update():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test world update"

    world = vox.VoxelWorld(1, comp)
    for i in range(10):
        world.add_voxel((0, 0, i), "cube", (0, 0, 255, 255), "Oak")

    world.update(
        {
            (0, 0, 2): {"shape": "cube", "color": (255, 0, 0, 255)},
            (0, 0, 4): {"shape": "cube", "color": (255, 0, 0, 255)},
            (0, 0, 15): {"shape": "cube", "color": (255, 0, 0, 255)},
        }
    )


def test_clear():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test world clear"

    world = vox.VoxelWorld(1, comp)
    for i in range(10):
        world.add_voxel((0, 0, i), "cube", (0, 0, 255, 255), "Oak")

    world.clear()
