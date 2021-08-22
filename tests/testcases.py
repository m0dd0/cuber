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


def test_cube_creation():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test cube creation"

    cube = vox.DirectCube(comp, (0, 0, 0), 1)
    cube = vox.DirectCube(comp, (0, 5, 0), 2)
    cube = vox.DirectCube(comp, (2, 0, 0), 1, (255, 0, 0, 255))
    cube = vox.DirectCube(comp, (4, 0, 0), 1, (0, 255, 0, 255))
    cube = vox.DirectCube(comp, (6, 0, 0), 1, appearance="Oak")
    cube = vox.DirectCube(comp, (6, 0, 0), 1, (255, 0, 0, 255), appearance="Oak")
    cube = vox.DirectCube(
        comp, (8, 0, 0), 1, (255, 0, 0, 255), appearance="Oak", name="name"
    )
    cube = vox.DirectCube(comp, (10, 0, 0), 1)
    cube.color = (255, 0, 0, 255)
    cube.appearance = "Oak"
    cube.name = "name2"


def test_sphere_creation():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test sphere creation"

    sphere = vox.DirectSphere(comp, (0, 0, 0), 1)
    sphere = vox.DirectSphere(comp, (0, 5, 0), 2)
    sphere = vox.DirectSphere(comp, (2, 0, 0), 1, (255, 0, 0, 255))
    sphere = vox.DirectSphere(comp, (4, 0, 0), 1, (0, 255, 0, 255))
    sphere = vox.DirectSphere(comp, (6, 0, 0), 1, appearance="Oak")
    sphere = vox.DirectSphere(comp, (6, 0, 0), 1, (255, 0, 0, 255), appearance="Oak")
    sphere = vox.DirectSphere(
        comp, (8, 0, 0), 1, (255, 0, 0, 255), appearance="Oak", name="name"
    )

    sphere = vox.DirectSphere(comp, (10, 0, 0), 1)
    sphere.color = (255, 0, 0, 255)
    sphere.appearance = "Oak"
    sphere.name = "name2"


def test_voxel_world():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test voxel world"

    world = vox.VoxelWorld(1, comp)
    for i in range(50):
        world.add_voxel((0, 0, i), vox.DirectCube, (0, 0, i, 255), "Oak", "world voxel")
        world.add_voxel(
            (0, i, 0), vox.DirectSphere, (0, i, 0, 255), "Oak", "world voxel"
        )
