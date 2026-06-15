import boomi_cicd


# This script is used to turn off listener and batch schedules in primary atom and on in DR
# The atoms are set up in an active-active configuration within the same environment
# No persisted properties are being used on the primary atom

# Open release json
releases = boomi_cicd.set_release()

# Get atom id
atom_id = boomi_cicd.query_atom(boomi_cicd.ATOM_NAME)
atom_dr_id = boomi_cicd.query_atom(boomi_cicd.ATOM_NAME_DR)

for release in releases["pipelines"]:
    component_id = release["componentId"]
    # Turn off listener in primary and on in DR
    if "listenerStatus" in release:
        boomi_cicd.change_listener_status(component_id, atom_id, "pause")
        boomi_cicd.change_listener_status(component_id, atom_id, "resume")

    # Pause schedules in primary and resume in DR
    if "schedule" in release:
        # Get conceptual id of deployed process
        conceptual_id = boomi_cicd.query_process_schedule_status(atom_id, component_id)
        conceptual_id_dr = boomi_cicd.query_process_schedule_status(
            atom_dr_id, component_id
        )

        boomi_cicd.update_process_schedule_status(
            component_id, conceptual_id, atom_id, False
        )
        boomi_cicd.update_process_schedule_status(
            component_id, conceptual_id_dr, atom_dr_id, True
        )
