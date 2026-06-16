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


def get_folder_ids(folder_name):
    """
    Return all folder IDs whose fullPath starts with folder_name.
    Uses POST /Folder/query which returns the complete flat folder list with fullPath.
    """
    response = boomi_cicd.atomsphere_request(
        method="post",
        resource_path="/Folder/query",
        payload={},
    ).json()

    folders = response.get("result", [])
    matching = [
        f["id"] for f in folders
        if f.get("fullPath", "").startswith(folder_name)
        and not f.get("deleted", False)
    ]

    print(f"[generate] Found {len(matching)} folder(s) under '{folder_name}'")
    return matching


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
    response = boomi_cicd.atomsphere_request(
        method="post",
        resource_path="/ComponentMetadata/query",
        payload=payload,
    ).json()
    return [r for r in response.get("result", []) if r.get("type") in DEPLOYABLE_TYPES]


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
    response = boomi_cicd.atomsphere_request(
        method="post",
        resource_path="/ComponentMetadata/query",
        payload=payload,
    ).json()
    return [r for r in response.get("result", []) if r.get("type") in DEPLOYABLE_TYPES]


def get_latest_package_version(component_id, branch_ids=None):
    """Return (packageVersion, branchId) for the most recently created package, or (None, None)."""
    all_results = []

    if branch_ids:
        for branch_id in branch_ids:
            response = boomi_cicd.atomsphere_request(
                method="post",
                resource_path="/PackagedComponent/query",
                payload={
                    "QueryFilter": {
                        "expression": {
                            "operator": "and",
                            "nestedExpression": [
                                {"argument": [component_id], "operator": "EQUALS", "property": "componentId"},
                                {"argument": [branch_id], "operator": "EQUALS", "property": "branchId"},
                            ],
                        }
                    }
                },
            ).json()
            all_results.extend(response.get("result", []))
    else:
        response = boomi_cicd.atomsphere_request(
            method="post",
            resource_path="/PackagedComponent/query",
            payload={
                "QueryFilter": {
                    "expression": {
                        "argument": [component_id],
                        "operator": "EQUALS",
                        "property": "componentId",
                    }
                }
            },
        ).json()
        all_results = response.get("result", [])

    if not all_results:
        return None, None

    best = max(all_results, key=lambda r: r.get("createdDate", ""))
    return best.get("packageVersion"), best.get("branchId")


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
            print(f"[generate] WARNING: no folders matched '{folder}', querying all processes")
            candidates = query_all_processes()
    else:
        candidates = query_all_processes()
        print(f"[generate] {len(candidates)} candidate processes (no folder filter)")

    components = verify_non_deleted(candidates)
    components = list({c["componentId"]: c for c in components}.values())
    print(f"[generate] {len(components)} processes confirmed non-deleted")

    pipelines = []
    for c in components:
        version, branch_id = get_latest_package_version(c["componentId"], branch_ids or None)
        if version is None:
            print(f"[generate] WARNING: no packaged version found for {c.get('name', c['componentId'])} — skipping")
            continue
        entry = {
            "componentId": c["componentId"],
            "componentType": c.get("type", ""),
            "packageVersion": version,
            "notes": c.get("name", ""),
        }
        if branch_id:
            entry["branchId"] = branch_id
        pipelines.append(entry)

    release = {"pipelines": pipelines}

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(release, f, indent=2)

    print(f"[generate] Wrote {len(pipelines)} processes to {output_path}")
    for p in pipelines:
        branch_note = f" (branch: {p['branchId']})" if p.get('branchId') else ""
        print(f"  {p['notes']} → {p['packageVersion']}{branch_note}")


if __name__ == "__main__":
    main()
