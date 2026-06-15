import boomi_cicd
import boomi_cicd.util.json.change_listener_status


# https://help.boomi.com/bundle/developer_apis/page/r-atm-Change_listener_status.html


def change_listener_status(listener_id, atom_id, action):
    """
    Change the status of a listener for a specific Atom.

    This function sends a request to the AtomSphere API to change the status
    of a listener associated with a particular Atom. The listener ID, Atom ID,
    and the desired action are provided as parameters.

    :param listener_id: The ID of the listener to modify.
    :type listener_id: str
    :param atom_id: The ID of the Atom associated with the listener.
    :type atom_id: str
    :param action: The action to perform on the listener. pause, resume, restart, pause_all, resume_all, or restart_all.
    :type action: str
    :return: True if the listener status change was successful. If the request fails, an error is raised.
    :rtype: bool
    """
    resource_path = "/changeListenerStatus"

    payload = boomi_cicd.util.json.change_listener_status.execute()
    payload["listenerId"] = listener_id
    payload["containerId"] = atom_id
    payload["action"] = action

    boomi_cicd.atomsphere_request(method="post", resource_path=resource_path, payload=payload)
    # If successful, the response will return a 200 and the response empty.
    # Any other response will throw an error within requests_post()
    return True
