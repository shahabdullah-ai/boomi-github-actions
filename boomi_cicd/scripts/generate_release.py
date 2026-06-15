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


def get_latest_package_version(component_id):
    """Return the highest packageVersion string from Boomi for this component, or None if unpacked."""
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

    results = response.get("result", [])
    if not results:
        return None

    return max(results, key=lambda r: r.get("createdDate", "")).get("packageVersion")


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
        version = get_latest_package_version(c["componentId"])
        if version is None:
            print(f"[generate] WARNING: no packaged version found for {c.get('name', c['componentId'])} — skipping")
            continue
        pipelines.append({
            "componentId": c["componentId"],
            "componentType": c.get("type", ""),
            "packageVersion": version,
            "notes": c.get("name", ""),
        })

    release = {"pipelines": pipelines}

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(release, f, indent=2)

    print(f"[generate] Wrote {len(pipelines)} processes to {output_path}")
    for p in pipelines:
        print(f"  {p['notes']} → {p['packageVersion']}")


if __name__ == "__main__":
    main()
