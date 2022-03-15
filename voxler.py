import traceback
from pprint import pprint
from time import perf_counter
from collections import defaultdict

import adsk.core, adsk.fusion

from .tests import testcases

# a list or a single test function to test
# if a single testfunction is testes the addin.stop method is called at leaving addin
# if multiple testfunctions are provided we stop the addin immideately after the test
# which created it got executed.
# TESTCASES = testcases.ALL_CASES
TESTCASES = [testcases.test_driect_cube_creation]


addin = None


def run(context):
    try:
        adsk.core.Application.get().activeDocument.design.designType = (
            adsk.fusion.DesignTypes.DirectDesignType
        )

        results = defaultdict(dict)
        for case in TESTCASES:
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

        print("### RESULTS ###")
        pprint(dict(results), width=200)
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
