"""Tests for harness matching in generate_release.

Pure logic, no platform calls — generate_release imports boomi_cicd, which needs
credentials at import time, so the function is loaded from source in isolation.

    python3 tests/test_find_test_harnesses.py
"""
import ast
import os
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parents[1] / "boomi_cicd/scripts/generate_release.py"


def load_find_test_harnesses():
    """Extract just the one function, so importing the module's deps isn't required."""
    tree = ast.parse(SRC.read_text())
    fn = next(
        (n for n in tree.body
         if isinstance(n, ast.FunctionDef) and n.name == "find_test_harnesses"),
        None,
    )
    assert fn is not None, "find_test_harnesses not found in generate_release.py"
    ns = {"os": os}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SRC), "exec"), ns)
    return ns["find_test_harnesses"]


find_test_harnesses = load_find_test_harnesses()


def comp(cid, name):
    return {"componentId": cid, "name": name, "type": "process"}


FAILURES = []


def check(label, actual, expected):
    if actual != expected:
        FAILURES.append(f"{label}\n     expected: {expected}\n     actual:   {actual}")
        print(f"  FAIL  {label}")
    else:
        print(f"  ok    {label}")


def run():
    os.environ.pop("BOOMI_TEST_SUFFIX", None)

    # A harness is matched to the process whose name it extends.
    got = find_test_harnesses([comp("p1", "Invoice Sync"), comp("t1", "Invoice Sync - Test")])
    check("matches harness to its process", {k: v["componentId"] for k, v in got.items()}, {"p1": "t1"})

    # A process ending in the suffix with nothing to test is NOT a harness — this is
    # the case that would otherwise silently drop a real deliverable from the manifest.
    got = find_test_harnesses([comp("p2", "Regression - Test")])
    check("orphan suffix is not a harness", got, {})

    # Only exact "<name><suffix>" matches; a longer name is a different process.
    got = find_test_harnesses([comp("p3", "Order Feed"), comp("t3", "Order Feed - Test Harness")])
    check("near-miss name does not match", got, {})

    # Several processes, only some tested.
    got = find_test_harnesses([
        comp("a", "Alpha"), comp("at", "Alpha - Test"),
        comp("b", "Beta"),
        comp("c", "Gamma"), comp("ct", "Gamma - Test"),
    ])
    check("mixed set matches only the tested ones",
          {k: v["componentId"] for k, v in got.items()}, {"a": "at", "c": "ct"})

    # Suffix is configurable.
    os.environ["BOOMI_TEST_SUFFIX"] = "_TEST"
    got = find_test_harnesses([comp("p4", "Ship Notice"), comp("t4", "Ship Notice_TEST")])
    check("honours BOOMI_TEST_SUFFIX", {k: v["componentId"] for k, v in got.items()}, {"p4": "t4"})

    # Default suffix must not match once overridden.
    got = find_test_harnesses([comp("p5", "Ship Notice"), comp("t5", "Ship Notice - Test")])
    check("default suffix inactive when overridden", got, {})

    # Empty suffix disables matching rather than matching everything.
    os.environ["BOOMI_TEST_SUFFIX"] = ""
    got = find_test_harnesses([comp("p6", "Any"), comp("t6", "Any - Test")])
    check("empty suffix disables matching", got, {})
    os.environ.pop("BOOMI_TEST_SUFFIX", None)

    # A component must never be its own harness.
    got = find_test_harnesses([comp("x", " - Test")])
    check("component cannot be its own harness", got, {})

    # Unnamed components must not crash the matcher.
    got = find_test_harnesses([{"componentId": "n1"}, comp("p7", "Real"), comp("t7", "Real - Test")])
    check("tolerates components with no name",
          {k: v["componentId"] for k, v in got.items()}, {"p7": "t7"})


if __name__ == "__main__":
    print("find_test_harnesses")
    run()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILED\n")
        for f in FAILURES:
            print("  - " + f)
        sys.exit(1)
    print("all passed")
