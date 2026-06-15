import json

import boomi_cicd
from boomi_cicd import logger


# https://developer.boomi.com/docs/api/platformapi/MergeRequest#tag/MergeRequest/operation/ExecuteMergeRequest

# The Modifies or Update a MergeRequest object is not implemented because of the complexity of the request. 
# Create the payload and use atomsphere_request directly.

def query_merge_request(source_branch_id=None, destination_branch_id=None, stage=None):
    """
    Query merge requests based on sourch branch ID, target branch ID, or stage. Source branch ID or target branch ID must be supplied. stage is optional.

    :param source_branch_id: The source branch ID to filter by.
    :type source_branch_id: str
    :param destination_branch_id: The destination branch ID to filter by.
    :type destination_branch_id: str
    :param stage: The stage to filter by. Possible values are "NOT_EXIST", "DRAFTING", "FAILED_TO_DRAFT," "FAILED_TO_REDRAFT", "DRAFTED", "REVIEWING", "MERGING", "MERGED", "FAILED_TO_MERGE", "DELETED", "REDRAFTING", and "REVERTED".
    :type stage: str
    :return: The merge request query response. Return contains original response data from API.
    :rtype: dict
    """

    if not source_branch_id and not destination_branch_id:
        raise ValueError(
            "Either source_branch_id or destionation_branch_id must be provided."
        )

    resource_path = "/MergeRequest/query"

    payload = {
        "QueryFilter": {"expression": {"operator": "and", "nestedExpression": []}}
    }
    if source_branch_id:
        payload["QueryFilter"]["expression"]["nestedExpression"].append(
            {
                "argument": [source_branch_id],
                "operator": "EQUALS",
                "property": "sourceBranchId",
            }
        )

    if destination_branch_id:
        payload["QueryFilter"]["expression"]["nestedExpression"].append(
            {
                "argument": [destination_branch_id],
                "operator": "EQUALS",
                "property": "destinationBranchId",
            }
        )

    if stage:
        payload["QueryFilter"]["expression"]["nestedExpression"].append(
            {"argument": [stage], "operator": "EQUALS", "property": "stage"}
        )

    # TODO: Enabled queryMore results
    response = boomi_cicd.atomsphere_request(
        method="post", resource_path=resource_path, payload=payload
    )

    json_response = json.loads(response.text)

    return json_response


def get_merge_request(merge_request_id):
    """
    Get a merge request by its ID.

    :param merge_request_id: The merge request ID.
    :type merge_request_id: str
    :return: The merge request retrieval response. Return contains original response data from API.
    :rtype: dict
    """

    if not merge_request_id:
        raise ValueError("merge_request_id must be provided.")

    resource_path = f"/MergeRequest/{merge_request_id}"

    response = boomi_cicd.atomsphere_request(method="get", resource_path=resource_path)

    json_response = json.loads(response.text)

    return json_response


def create_merge_request(
    source_branch_id, destination_branch_id, strategy, priority_branch
):
    """
    You can use the Merge Request object to merge a development branch into the main branch. \
        To create a merge request, you need the branch IDs for the source and destination branches. \
        The source branch is the branch you want to merge into the destination branch.

    :param source_branch_id: The source branch ID.
    :type source_branch_id: str
    :param destination_branch_id: The destination branch ID.
    :type destination_branch_id: str
    :param strategy: The merge strategy. Must be 'OVERRIDE' or 'CONFLICT_RESOLVE'. \
        There are two merge request strategies you can choose from: OVERRIDE or CONFLICT_RESOLVE. \
        An override merge automatically resolves any merge conflicts by prioritizing the branch \
        specified in the priorityBranch field. If you choose the CONFLICT_RESOLVE strategy, \
        you have the opportunity to review any conflicts and choose which version you want to keep.
    :type strategy: str
    :param priority_branch: The priority branch for conflict resolution. Must be 'SOURCE' or 'DESTINATION'.
    :type priority_branch: str
    :return: The merge request creation response id. Return contains the merge request ID.
    :rtype: str
    """

    if not source_branch_id or not destination_branch_id:
        raise ValueError(
            "Both source_branch_id and destionation_branch_id must be provided."
        )
    if strategy not in ["OVERRIDE", "CONFLICT_RESOLVE"]:
        raise ValueError("Invalid strategy. Must be 'OVERRIDE' or 'CONFLICT_RESOLVE'.")
    if priority_branch not in ["SOURCE", "DESTINATION"]:
        raise ValueError("Invalid priority_branch. Must be 'SOURCE' or 'DESTINATION'.")

    resource_path = "/MergeRequest"

    payload = {
        "sourceBranchId": source_branch_id,
        "destinationBranchId": destination_branch_id,
        "strategy": strategy,
        "priorityBranch": priority_branch,
    }

    response = boomi_cicd.atomsphere_request(
        method="post", resource_path=resource_path, payload=payload
    )

    json_response = json.loads(response.text)

    if "id" not in json_response:
        raise ValueError(f"Merge request creation failed. Response: {json_response}")

    return json_response["id"]


def execute_merge_request(merge_request_id, action):
    """
    Execute a merge request by its ID.

    :param merge_request_id: The merge request ID.
    :type merge_request_id: str
    :return: The merge request execution response. Return contains original response data from API.
    :rtype: dict
    """

    if not merge_request_id:
        raise ValueError("merge_request_id must be provided.")
    if action not in ["MERGE", "REVERT", "RETRY_DRAFTING"]:
        raise ValueError(
            "Invalid action. Must be 'MERGE', 'REVERT', or 'RETRY_DRAFTING'."
        )

    # Check to merge stage to ensure that the merge can be executed
    merge_stage = get_merge_request(merge_request_id)["stage"]

    if action == "MERGE" and merge_stage not in ["REVIEWING", "FAILED_TO_MERGE"]:
        raise ValueError(
            f"Merge request cannot be merged in its current stage: {merge_stage}"
        )
    if action == "REVERT" and merge_stage not in ["MERGED", "DELETED"]:
        raise ValueError(
            f"Merge request cannot be reverted in its current stage: {merge_stage}"
        )
    if action == "RETRY_DRAFTING" and merge_stage not in [
        "FAILED_TO_DRAFT",
        "FAILED_TO_REDRAFT",
    ]:
        raise ValueError(
            f"Merge request drafting cannot be retried in its current stage: {merge_stage}"
        )

    resource_path = f"/MergeRequest/execute/{merge_request_id}"

    payload = {"id": merge_request_id, "mergeRequestAction": action}

    response = boomi_cicd.atomsphere_request(
        method="post", resource_path=resource_path, payload=payload
    )

    json_response = json.loads(response.text)

    return json_response
