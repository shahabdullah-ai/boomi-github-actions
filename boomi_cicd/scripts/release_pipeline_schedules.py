import boomi_cicd


# Open release json
releases = boomi_cicd.set_release()

# Get atom id
atom_id = boomi_cicd.query_atom(boomi_cicd.ATOM_NAME)

for release in releases["pipelines"]:
    component_id = release["componentId"]
    if "schedule" in release:
        # Get conceptual id of deployed process
        conceptual_id = boomi_cicd.query_process_schedules(atom_id, component_id)

        boomi_cicd.update_process_schedules(
            component_id,
            conceptual_id,
            atom_id,
            release["schedule"] if "schedule" in release else None,
        )
