import json

import boomi_cicd
import boomi_cicd.util.json.atom


# https://help.boomi.com/bundle/developer_apis/page/r-atm-Atom_object.html


def query_atom(atom_name):
    """
    Query the Atom by name and retrieve its ID.

    This function sends a request to the AtomSphere API to query for an Atom
    with the specified name. If the Atom is found, then an ID is returned. If no
    atom is found, then an error is logged, and the program exits.

    :param atom_name: The name of the Atom to query.
    :type atom_name: str
    :return: The ID of the queried Atom.
    :rtype: str
    :raises ValueError: If the Atom is not found.
    """
    resource_path = "/Atom/query"

    payload = boomi_cicd.util.json.atom.query()
    payload["QueryFilter"]["expression"]["argument"][0] = atom_name

    response = boomi_cicd.atomsphere_request(method="post", resource_path=resource_path, payload=payload)

    json_response = json.loads(response.text)
    if json_response["numberOfResults"] == 0:
        raise ValueError(f"Atom not found. Atom Name: {atom_name}")
    atom_id = json.loads(response.text)["result"][0]["id"]
    return atom_id
