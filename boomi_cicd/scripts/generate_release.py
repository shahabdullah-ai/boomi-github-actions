import json
import os
import boomi_cicd

DEPLOYABLE_TYPES = {
    "process",
    "webservice.external",
    "webservice.internal",
    "flowservice",
    "processroute",
    "tpgroup",
    "customlibrary",
    "certificate",
}


def query_all_pages(resource_path, payload):
    """Fetch all pages from a Boomi query endpoint using queryToken/queryMore pagination."""
    results = []
    response = boomi_cicd.atomsphere_request(
        method="post",
        resource_path=resource_path,
        payload=payload,
    ).json()
    results.extend(response.get("result", []))
    total = response.get("numberOfResults", len(results))

    while len(results) < total and response.get("queryToken"):
        try:
            response = boomi_cicd.atomsphere_request(
                method="post",
                resource_path=resource_path.replace("/query", "/queryMore"),
                payload={"queryToken": response["queryToken"]},
            ).json()
            results.extend(response.get("result", []))
        except Exception as e:
            print(f"[paginate] queryMore stopped at {len(results)}/{total} — {e}")
            break

    return results


def get_folder_ids(folder_name):
    """
    Return all folder IDs whose fullPath starts with folder_name.
    Traverses hierarchy by name filter + fullPath match to avoid Folder/queryMore limitations.
    """
    parts = [p.strip() for p in folder_name.split("/")]
    target_id = None

    for i, part in enumerate(parts):
        expected_path = "/".join(parts[:i + 1])
        payload = {
            "QueryFilter": {
                "expression": {
                    "argument": [part],
                    "operator": "EQUALS",
                    "property": "name",
                }
            }
        }
        results = query_all_pages("/Folder/query", payload)
        match = next(
            (f for f in results if f.get("fullPath") == expected_path and not f.get("deleted", False)),
            None,
        )
        if not match:
            print(f"[generate] Found 0 folder(s) under '{folder_name}'")
            return []
        target_id = match["id"]

    # BFS using parentId filter to collect all descendants
    all_ids = [target_id]
    queue = [target_id]
    while queue:
        pid = queue.pop(0)
        children = query_all_pages("/Folder/query", {
            "QueryFilter": {
                "expression": {
                    "argument": [pid],
                    "operator": "EQUALS",
                    "property": "parentId",
                }
            }
        })
        for child in [c for c in children if not c.get("deleted", False)]:
            all_ids.append(child["id"])
            queue.append(child["id"])

    print(f"[generate] Found {len(all_ids)} folder(s) under '{folder_name}'")
    return all_ids


def query_processes_in_folder(folder_id):
    """Query non-deleted deployable components for a single folder ID."""
    payload = {
        "QueryFilter": {
            "expression": {
                "operator": "and",
                "nestedExpression": [
                    {"argument": ["false"],    "operator": "EQUALS", "property": "deleted"},
                    {"argument": [folder_id],  "operator": "EQUALS", "property": "folderId"},
                ],
            }
        }
    }
    results = query_all_pages("/ComponentMetadata/query", payload)
    return [r for r in results if r.get("type") in DEPLOYABLE_TYPES]


def query_all_processes():
    """Query all non-deleted deployable components without folder filter (fallback)."""
    payload = {
        "QueryFilter": {
            "expression": {
                "operator": "and",
                "nestedExpression": [
                    {"argument": ["false"], "operator": "EQUALS", "property": "deleted"},
                ],
            }
        }
    }
    results = query_all_pages("/ComponentMetadata/query", payload)
    return [r for r in results if r.get("type") in DEPLOYABLE_TYPES]


def get_latest_package_version(component_id, branch_ids=None):
    """Return (packageVersion, branchId) for the most recently created package, or (None, None)."""
    all_results = []

    if branch_ids:
        for branch_id in branch_ids:
            all_results.extend(query_all_pages("/PackagedComponent/query", {
                "QueryFilter": {
                    "expression": {
                        "operator": "and",
                        "nestedExpression": [
                            {"argument": [component_id], "operator": "EQUALS", "property": "componentId"},
                            {"argument": [branch_id], "operator": "EQUALS", "property": "branchId"},
                        ],
                    }
                }
            }))
    else:
        all_results = query_all_pages("/PackagedComponent/query", {
            "QueryFilter": {
                "expression": {
                    "argument": [component_id],
                    "operator": "EQUALS",
                    "property": "componentId",
                }
            }
        })

    if not all_results:
        return None, None, None

    best = max(all_results, key=lambda r: r.get("createdDate", ""))
    return best.get("packageVersion"), best.get("branchId"), best.get("createdDate")


def verify_non_deleted(components):
    """Verify each component is truly non-deleted via individual GET (safety net)."""
    verified = []
    for c in components:
        cid = c.get("componentId")
        try:
            detail = boomi_cicd.atomsphere_request(
                method="get",
                resource_path=f"/ComponentMetadata/{cid}",
            ).json()
            if not detail.get("deleted", False):
                verified.append(c)
        except Exception:
            pass
    return verified


def find_test_harnesses(components):
    """Map each component id to its automated-test harness, matched by name.

    A harness cannot be discovered from the API — nothing on a component records
    "this tests that" — so it is resolved by convention: a process named
    "<name><suffix>" is the harness for the process named "<name>" within the same
    folder set. Override the suffix with BOOMI_TEST_SUFFIX; set it empty to disable
    harness matching entirely.

    Returns {tested_component_id: harness_component_record}.
    """
    suffix = os.environ.get("BOOMI_TEST_SUFFIX", " - Test")
    if not suffix:
        return {}

    by_name = {}
    for c in components:
        name = c.get("name", "")
        if name:
            by_name.setdefault(name, c)

    harnesses = {}
    for c in components:
        name = c.get("name", "")
        if not name.endswith(suffix):
            continue
        tested = by_name.get(name[: -len(suffix)])
        # A process merely ending in the suffix is not a harness unless the process
        # it would be testing actually exists.
        if tested and tested["componentId"] != c["componentId"]:
            harnesses[tested["componentId"]] = c

    if harnesses:
        print(f"[generate] Matched {len(harnesses)} test harness(es) by '{suffix}' suffix")
    return harnesses


def main():
    folder = os.environ.get("BOOMI_FOLDER_NAME", "")
    release_base_dir = os.environ.get("BOOMI_RELEASE_BASE_DIR", ".")
    output_path = os.path.join(release_base_dir, "release", "release.json")

    # Resolve optional branch names to IDs
    branch_ids = []
    branch_names_raw = os.environ.get("BOOMI_BRANCH_NAME", "").strip()
    if branch_names_raw:
        from boomi_cicd.util.branch import BranchNotFoundError
        for name in [b.strip() for b in branch_names_raw.split(",") if b.strip()]:
            try:
                bid = boomi_cicd.get_branch_id(name)
                branch_ids.append(bid)
                print(f"[generate] Resolved branch '{name}' → {bid}")
            except BranchNotFoundError:
                print(f"[generate] WARNING: branch '{name}' not found — skipping")

    if folder:
        folder_ids = get_folder_ids(folder)
        if folder_ids:
            candidates = []
            for fid in folder_ids:
                results = query_processes_in_folder(fid)
                candidates.extend(results)
            print(f"[generate] {len(candidates)} candidate processes across {len(folder_ids)} folder(s)")
        else:
            raise SystemExit(f"[generate] ERROR: no folders matched '{folder}'. Check BOOMI_FOLDER_NAME — folder must exist and be accessible in this account.")
    else:
        candidates = query_all_processes()
        print(f"[generate] {len(candidates)} candidate processes (no folder filter)")

    components = verify_non_deleted(candidates)
    components = list({c["componentId"]: c for c in components}.values())
    print(f"[generate] {len(components)} processes confirmed non-deleted")

    harnesses = find_test_harnesses(components)
    harness_ids = {h["componentId"] for h in harnesses.values()}

    pipelines = []
    for c in components:
        # The test stage deploys and executes a harness against the process it tests,
        # so a harness must not also appear as a deliverable of its own — otherwise it
        # promotes to Stage and Production alongside real integrations.
        if c["componentId"] in harness_ids:
            continue

        version, branch_id, created_date = get_latest_package_version(c["componentId"], branch_ids or None)
        if version is None:
            print(f"[generate] WARNING: no packaged version found for {c.get('name', c['componentId'])} — skipping")
            continue
        name = c.get("name", "")
        entry = {
            "componentId": c["componentId"],
            "componentType": c.get("type", ""),
            "packageVersion": version,
            # automated_testing_junit.py indexes processName directly, so it must always
            # be present — a missing key is a KeyError that kills the whole test stage.
            "processName": name,
            "notes": name,
        }
        if created_date:
            entry["createdDate"] = created_date
        if branch_id:
            entry["branchId"] = branch_id
        harness = harnesses.get(c["componentId"])
        if harness:
            entry["automatedTestId"] = harness["componentId"]
        pipelines.append(entry)

    release = {"pipelines": pipelines}

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(release, f, indent=2)

    print(f"[generate] Wrote {len(pipelines)} processes to {output_path}")
    for p in pipelines:
        branch_note = f" (branch: {p['branchId']})" if p.get('branchId') else ""
        test_note = " [+test]" if p.get("automatedTestId") else ""
        print(f"  {p['notes']} → {p['packageVersion']}{branch_note}{test_note}")


if __name__ == "__main__":
    main()
