import os
import platform
from zipfile import ZipFile

import defusedxml.ElementTree as ET
import requests
from defusedxml import minidom

import boomi_cicd
from boomi_cicd import logger


def process_git_release(repo, file_components, release):
    """
    Process a release from the release json and update the component repository.
    This function is the main function for the component_xml_git.py script.
    :param repo: Boomi Component Repository
    :param file_components: The base name/value pair for the component name and component ID.
    :param release: The release json.
    :return: None.
    """
    component_id = release["componentId"]
    process_name = release["processName"]
    package_version = release["packageVersion"]
    process_base_dir = f"{boomi_cicd.COMPONENT_REPO_NAME}/{process_name}"

    # Check if the packaged component's name has changed.
    rename_component_folder(repo, file_components, component_id, process_name)

    component_refs = get_component_refs(process_base_dir)

    packaged_component_id = boomi_cicd.query_packaged_component(
        component_id, package_version
    )
    packaged_manifest = boomi_cicd.get_package_component_manifest(packaged_component_id)
    component_info_names = set()

    for component_info in get_component_info_from_manifest(packaged_manifest):
        component_info_id = component_info.attrib["id"]
        component_file_name = process_component(
            repo, process_base_dir, component_info_id, component_refs, process_name
        )

        component_info_names.add(component_file_name)

    delete_unused_files(repo, process_base_dir, component_info_names, process_name)
    set_component_xml_file_refs(process_base_dir, component_refs)


def clone_repository():
    """
    Clone the component repository.
    The function will import GitPython to avoid the need to install git unless the component_xml_git.py script is used.
    :return: Repo object
    """
    # Lazy load git.
    # GitPython requires git to be installed.
    # This allows for users to not install git unless the component_xml_git.py script is used.
    from git import Repo

    repo = Repo.clone_from(boomi_cicd.COMPONENT_GIT_URL, boomi_cicd.COMPONENT_REPO_NAME)
    logger.info(f"Git Repo Status: {repo.git.status()}".replace("\n", " "))
    return repo


def rename_component_folder(repo, file_components, component_id, process_name):
    """
    Rename the component folder if the process name has changed.
    :param repo: Boomi Component Repository
    :param file_components: The base name/value pair for the component name and component ID.
    :param component_id: The component ID.
    :param process_name: The process name.
    :return: None.
    """
    if (
        component_id in file_components
        and process_name != file_components[component_id]
    ):
        logger.info(
            f"Process name changed. Original: {file_components[component_id]}. New: {process_name}"
        )
        repo.git.mv(f"{file_components[component_id]}", f"{process_name}")
        file_components[component_id] = process_name


def get_component_refs(process_base_dir):
    """
    Get the component references from the directory.
    :param process_base_dir:
    :return: A name/value pair for the component name and component ID.
    :rtype: set
    """
    component_refs = {}
    if os.path.exists(process_base_dir):
        component_refs = boomi_cicd.get_component_xml_file_refs(process_base_dir)
        logger.info(f"Created component_refs: {component_refs}")
    return component_refs


def get_component_info_from_manifest(packaged_manifest):
    """
    Get the component info from the packaged manifest.
    This contains a list of all component ids within the packaged component.
    :param packaged_manifest:
    :return: A list of all the component IDs within the packaged component manifest.
    :rtype: list
    """
    root = ET.fromstring(packaged_manifest)
    return root.findall(".//bns:componentInfo", boomi_cicd.NAMESPACES)


def process_component(
    repo, process_base_dir, component_info_id, component_refs, process_name
):
    component_xml = boomi_cicd.query_component(component_info_id)
    component_name = ET.fromstring(component_xml).attrib["name"]
    component_file_name = f"{component_name}.xml"

    if (
        component_info_id in component_refs
        and component_file_name != component_refs[component_info_id]
    ):
        logger.info(
            f"Component name changed. Original: {component_refs[component_info_id]}. New: {component_name}"
        )
        repo.git.mv(
            f"{process_name}/{component_refs[component_info_id]}",
            f"{process_name}/{component_file_name}",
        )

    with open(f"{process_base_dir}/{component_file_name}", "w") as f:
        f.write(minidom.parseString(component_xml).toprettyxml(indent="  "))

    component_refs[component_info_id] = component_file_name
    return component_file_name


def commit_and_push(repo, commit_message="Commit from Boomi CICD"):
    """
    Commit and push changes to the component repository.
    :param repo: Repo object
    :param commit_message: Commit Message.
    Default is "Commit from Boomi CICD".
    :return: None.
    """
    repo.index.add("*")
    commit_message = commit_message
    logger.info(f"Commiting changes: {commit_message}")
    repo.index.commit(commit_message)
    repo.remote("origin").push("main")


def delete_unused_files(repo, process_base_dir, component_info_names, process_name):
    """
    Delete unused files from the component repository.
    :param repo: Repo object
    :param process_base_dir: Directory of the current process.
    :param component_info_names:
    :param process_name: Name of the process from the release JSON file.
    :return: None.
    """
    for dirpath, dirnames, filenames in os.walk(process_base_dir):
        for filename in filenames:
            if filename not in component_info_names and filename != ".componentRef":
                repo.git.rm(f"{process_name}/{filename}")
                logger.info(f"Deleted {filename} from {process_name}")


def get_component_xml_file_refs(location):
    """
    Read .componentRef file to get component id of folder/files.

    :param location: The location of the file.
    :type location: str
    :return: A dictionary containing folder references with their IDs as keys and names as values.
    :rtype: dict
    """
    file_refs = {}
    if os.path.exists(os.path.join(location, ".componentRef")):
        with open(os.path.join(location, ".componentRef"), "r") as f:
            folder_refs = f.read()
        for folder_ref in folder_refs.split("\n"):
            if folder_ref != "":
                folder_ref_split = folder_ref.split("=")
                folder_ref_id = folder_ref_split[0]
                folder_ref_name = folder_ref_split[1]
                file_refs[folder_ref_id] = folder_ref_name
    else:
        open(os.path.join(location, ".componentRef"), "w").close()
    return file_refs


def set_component_xml_file_refs(location, file_refs):
    """
    Write .componentRef file to set component id of folder/files.

    :param location: The location of the file.
    :type location: str
    :param file_refs: A dictionary containing folder references with their IDs as keys and names as values.
    :type file_refs: dict
    """
    with open(os.path.join(location, ".componentRef"), "w") as f:
        for file_ref in file_refs:
            f.write("{}={}\n".format(file_ref, file_refs[file_ref]))


def install_sonarqube():
    """
    Install SonarQube Scanner CLI.

    :return: The path to the SonarQube Scanner CLI executable.
    :rtype: str
    """
    platform_system = platform.system()
    if platform_system == "Linux":
        # Download linux zip
        # https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.8.0.2856-linux.zip
        sonarqube_version = "sonar-scanner-cli-4.8.0.2856-linux"
        sonarqube_version_unzip = "sonar-scanner-4.8.0.2856-linux"
    elif platform_system == "Windows":
        # Download windows zip
        # https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.8.0.2856-windows.zip
        sonarqube_version = "sonar-scanner-cli-4.8.0.2856-windows"
        sonarqube_version_unzip = "sonar-scanner-4.8.0.2856-windows"
    else:
        raise OSError(f"Unsupported OS: {platform_system}")

    # Download SonarQube
    url = "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/"
    sonarqube_version_zip = f"{sonarqube_version}.zip"

    r = requests.get(url + sonarqube_version_zip, allow_redirects=True)
    with open(sonarqube_version_zip, "wb") as f:
        f.write(r.content)

    # Extract SonarQube
    with ZipFile(sonarqube_version_zip, "r") as zipObj:
        zipObj.extractall()

    return sonarqube_version_unzip
