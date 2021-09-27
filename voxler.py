import traceback
from pprint import pprint

import adsk.core, adsk.fusion

from .tests import testcases


def run(context):
    try:
        adsk.core.Application.get().activeDocument.design.designType = (
            adsk.fusion.DesignTypes.DirectDesignType
        )

        all_testcases = [
            getattr(testcases, name)
            for name in dir(testcases)
            if name.startswith("test") and callable(getattr(testcases, name))
        ]

        current_testcases = [
            # testcases.test_driect_cube_creation,
            # testcases.test_direct_sphere_creation,
            testcases.test_cg_cube_creation,
            testcases.test_cg_sphere_creation,
        ]

        results = testcases.execute_cases(current_testcases)
        print("### RESULTS ###")
        pprint(dict(results))
        if all([r["passed"] for r in results.values()]):
            print("### PASSED ###")
        else:
            print("### FAILED ###")

    except:
        print("Failed:\n{}".format(traceback.format_exc()))


def stop(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

    except:
        print("Failed:\n{}".format(traceback.format_exc()))
