import datetime
import os

import boomi_cicd


# Open release json
releases = boomi_cicd.set_release()

# Perform a query to get the branch id if needed.
# source_branch = boomi_cicd.get_branch_id("dev")
# destination_branch = boomi_cicd.get_branch_id("main")

# Optionally, create and execute a merge request before deployments.
# merge_request = boomi_cicd.create_merge_request(source_branch, destination_branch, "OVERRIDE", "SOURCE")
# boomi_cicd.execute_merge_request(merge_request, "MERGE")

_filter_enabled = os.environ.get("DEPLOY_CHANGED_ONLY", "false").lower() == "true"
_since_raw = os.environ.get("SINCE_DATE", "").strip()
_since_version = _since_raw.replace("-", ".") if _since_raw else datetime.date.today().strftime("%Y.%m.%d")

if _filter_enabled:
    print(f"[filter] DEPLOY_CHANGED_ONLY enabled — skipping components with packageVersion < {_since_version}")

environment_id = boomi_cicd.query_environment(boomi_cicd.ENVIRONMENT_NAME)

_atom_names = [a.strip() for a in os.environ.get("BOOMI_ATOM_NAME", "").split(",") if a.strip()]
try:
    _atom_ids = [boomi_cicd.query_atom(name) for name in _atom_names]
except ValueError as exc:
    raise SystemExit(f"[atom] {exc}") from exc

if _atom_ids:
    _env_atom_ids = boomi_cicd.get_environment_atom_ids(environment_id)
    _kept_names, _kept_ids = [], []
    for name, atom_id in zip(_atom_names, _atom_ids):
        if atom_id in _env_atom_ids:
            _kept_names.append(name)
            _kept_ids.append(atom_id)
        else:
            print(f"[atom] Skipping {name} — not attached to {boomi_cicd.ENVIRONMENT_NAME}")
    _atom_names = _kept_names
    _atom_ids = _kept_ids
    if not _atom_ids:
        print(f"[atom] No specified atoms attached to {boomi_cicd.ENVIRONMENT_NAME} — deploying to full environment")

if _atom_ids:
    print(f"[atom] Targeting {len(_atom_ids)} atom(s) in {boomi_cicd.ENVIRONMENT_NAME}: {', '.join(_atom_names)}")
else:
    print("[atom] No atom filter — deploying to full environment")

for release in releases["pipelines"]:
    component_id = release["componentId"]
    package_version = release["packageVersion"]
    notes = release.get("notes")

    if _filter_enabled and package_version < _since_version:
        print(f"[filter] Skipping {notes} (version {package_version} < {_since_version})")
        continue

    package_id = boomi_cicd.query_packaged_component(component_id, package_version)

    if not package_id:
        branch_id = release.get("branchId")
        package_id = boomi_cicd.create_packaged_component(
            component_id, package_version, notes, branch_id
        )

    # The third parameter determines if the package is currently deployed (True) or has every been deployed (False)
    if _atom_ids:
        for atom_id in _atom_ids:
            if not boomi_cicd.query_deployed_package(package_id, environment_id, False, atom_id=atom_id):
                boomi_cicd.create_deployed_package(release, package_id, environment_id, atom_id=atom_id)
    else:
        package_deployed = boomi_cicd.query_deployed_package(package_id, environment_id, False)
        if not package_deployed:
            boomi_cicd.create_deployed_package(release, package_id, environment_id)
        # delete_deployed_package(deployment_id) # Delete deployment is useful for testing
