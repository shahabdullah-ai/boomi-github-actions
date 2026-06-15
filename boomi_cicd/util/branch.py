import boomi_cicd
import boomi_cicd.util.json.branch

## https://developer.boomi.com/docs/api/platformapi/Branch


def get_branch_id(branch_name):
    """
    Get the branch ID for a given branch name.

    :param branch_name: The name of the branch.
    :type branch_name: str
    :return: The ID of the branch.
    :rtype: str
    """
    resource_path = "/Branch/query"

    payload = boomi_cicd.util.json.branch.query()
    payload["QueryFilter"]["expression"]["argument"][0] = branch_name

    response = boomi_cicd.atomsphere_request(method="post", resource_path=resource_path, payload=payload)

    branches = response.json().get("result", [])

    if len(branches) == 0:
        raise BranchNotFoundError(f"Branch '{branch_name}' not found")
    if len(branches) == 1 and "id" in branches[0] and branches[0]["name"] == branch_name:
        return branches[0].get("id")
    if len(branches) > 1:
        raise MultipleBranchesFoundError(f"Multiple branches found with the same name. Branch name in query: '{branch_name}'")


    raise BranchNotFoundError(f"Branch '{branch_name}' not found")

def create_branch(branch_name, parent_branch_id, description=""):
    """
    Create a new branch.

    :param branch_name: The name of the new branch.
    :type branch_name: str
    :param parent_branch_id: The ID of the parent branch.
    :type parent_branch_id: str
    :param description: The description of the new branch. (Optional)
    :type description: str
    :return: The ID of the newly created branch.
    :rtype: str
    """
    
    if not branch_name:
        raise ValueError("Branch name cannot be empty")
    if not parent_branch_id:
        raise ValueError("Parent branch ID cannot be empty")
    resource_path = "/Branch"

    payload = {
        "name": branch_name,
        "description": description,
        "parentId": parent_branch_id
    }

    response = boomi_cicd.atomsphere_request(method="post", resource_path=resource_path, payload=payload)


    branch_id = response.json().get("id")
    if not branch_id:
        raise Exception("Branch creation failed: missing branch ID in response.")
    return branch_id



class BranchNotFoundError(Exception):
    """Raised when a branch is not found."""
    pass

class MultipleBranchesFoundError(Exception):
    """Raised when multiple branches are found with the same name."""
    pass