import json
import sys

import boomi_cicd
import boomi_cicd.util.json.process_schedule
from boomi_cicd import logger


# https://help.boomi.com/bundle/developer_apis/page/r-atm-Process_Schedules_object.html


def query_process_schedules(atom_id, process_id):
    """
    Query the process schedules to get the conceptual ID.

    :param atom_id: The ID of the Atom.
    :type atom_id: str
    :param process_id: The ID of the process.
    :type process_id: str
    :return: The conceptual ID of the process schedule.
    :rtype: str
    :raises: SystemExit: If the process is not deployed.
    """
    resource_path = "/ProcessSchedules/query"

    payload = boomi_cicd.util.json.process_schedule.query()
    payload["QueryFilter"]["expression"]["nestedExpression"][0]["argument"][0] = atom_id
    payload["QueryFilter"]["expression"]["nestedExpression"][1]["argument"][
        0
    ] = process_id

    response = boomi_cicd.atomsphere_request(method="post", resource_path=resource_path, payload=payload)

    json_response = json.loads(response.text)
    if json_response["numberOfResults"] == 0:
        logger.error(
            f"Process is not deployed. Atom Name: {boomi_cicd.ATOM_NAME}, Process Id: {process_id}"
        )
        sys.exit(1)
    conceptual_id = json.loads(response.text)["result"][0]["id"]
    return conceptual_id


def update_process_schedules(component_id, conceptual_id, atom_id, schedules):
    """
    Update the process schedules.

    :param component_id: The ID of the component.
    :type component_id: str
    :param conceptual_id: The conceptual ID of the process schedule.
    :type conceptual_id: str
    :param atom_id: The ID of the Atom.
    :type atom_id: str
    :param schedules: The schedules to update. If empty, the schedules will be cleared.
    :type schedules: str or None
    :return: True if the process schedules are updated successfully, False otherwise.
    :rtype: bool
    :raises: SystemExit: If the schedule format is invalid.
    """
    resource_path = "/ProcessSchedules/{}/update".format(conceptual_id)

    payload = boomi_cicd.util.json.process_schedule.update()
    payload["processId"] = component_id
    payload["atomId"] = atom_id
    payload["id"] = conceptual_id

    # If schedules is empty, then clear the schedules.
    # If not empty, then update the schedules.
    if schedules is not None:
        schedules = schedules.split(";")

        for schedule in schedules:
            split_schedule = schedule.strip().split(" ")
            if len(split_schedule) != 6:
                logger.error(
                    f"Invalid schedule format. Format: {schedule}. Arguments passed: {len(split_schedule)}. "
                    f"Arguments expected: 6."
                )
                sys.exit(1)
            json_variable = {
                "@type": "Schedule",
                "minutes": split_schedule[0],
                "hours": split_schedule[1],
                "daysOfWeek": split_schedule[2],
                "daysOfMonth": split_schedule[3],
                "months": split_schedule[4],
                "years": split_schedule[5],
            }

            if payload["Schedule"]:
                payload["Schedule"].append(json_variable)
            else:
                payload["Schedule"] = [json_variable]

    boomi_cicd.atomsphere_request(method="post", resource_path=resource_path, payload=payload)

    return True
