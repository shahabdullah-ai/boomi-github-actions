import os

import boomi_cicd
from boomi_cicd import logger


sonarqube_dir = boomi_cicd.install_sonarqube()

base_folder = '"' + os.path.join(os.getcwd(), boomi_cicd.COMPONENT_REPO_NAME) + '"'
logger.info(f"Boomi Component Repo Directory: {base_folder}")
logger.info(f"Sonar Host URL: {boomi_cicd.SONARQUBE_HOST_URL}")

os.system(
    rf"{sonarqube_dir}\bin\sonar-scanner.bat"
    rf" -Dsonar.projectKey={boomi_cicd.SONARQUBE_PROJECT_KEY}"
    rf" -Dsonar.projectBaseDir={base_folder}"
    rf" -Dsonar.sources={base_folder}"
    rf" -Dsonar.host.url={boomi_cicd.SONARQUBE_HOST_URL}"
    rf" -Dsonar.login={boomi_cicd.SONARQUBE_TOKEN}"
)
