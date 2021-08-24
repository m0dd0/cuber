import traceback
from collections import defaultdict
from time import perf_counter
from typing import List, Callable
from uuid import uuid4

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


def test_voxel_world_basic():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test voxel world"

    world = vox.VoxelWorld(1, comp)
    for i in range(10):
        world.add_voxel((0, 0, i), vox.DirectCube, (0, 0, 100 + i * 10, 255), "Oak")
        world.add_voxel((0, i, 0), vox.DirectSphere, (0, 100 + i * 10, 0, 255), "Oak")


def test_world_color_change():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test world color change"

    world = vox.VoxelWorld(1, comp)
    for i in range(10):
        world.add_voxel((0, 0, i), vox.DirectCube, (0, 0, 255, 255), "Oak")

    for i in range(5):
        world.add_voxel((0, 0, 2 * i), vox.DirectCube, (255, 0, 0, 255), "Oak")


def test_world_update():
    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test world update"

    world = vox.VoxelWorld(1, comp)
    for i in range(10):
        world.add_voxel((0, 0, i), vox.DirectCube, (0, 0, 255, 255), "Oak")

    world.update(
        {
            (0, 0, 2): {"voxel_class": vox.DirectCube, "color": (255, 0, 0, 255)},
            (0, 0, 4): {"voxel_class": vox.DirectCube, "color": (255, 0, 0, 255)},
            (0, 0, 15): {"voxel_class": vox.DirectCube, "color": (255, 0, 0, 255)},
        }
    )


def test_color():
    base_appearance = app.materialLibraries.itemByName(
        "Fusion 360 Appearance Library"
    ).appearances.itemByName("Oak")

    # colored_appearance = design.appearances.itemByName(colored_appearance_name)
    # if colored_appearance is None:

    comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    comp.name = "test color"

    for i in range(10):
        cube = adsk.fusion.TemporaryBRepManager.get().createBox(
            adsk.core.OrientedBoundingBox3D.create(
                adsk.core.Point3D.create(0, 0, i),
                adsk.core.Vector3D.create(1, 0, 0),
                adsk.core.Vector3D.create(0, 1, 0),
                1,
                1,
                1,
            )
        )

        cube = comp.bRepBodies.add(cube)

        colored_appearance = design.appearances.addByCopy(base_appearance, str(uuid4()))
        colored_appearance.appearanceProperties.itemByName(
            "Color"
        ).value = adsk.core.Color.create(0, 0, 100 + i * 10, 255)

        cube.appearance = colored_appearance