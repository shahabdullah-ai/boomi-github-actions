import os

from dotenv import load_dotenv

load_dotenv()


BASE_URL = os.environ.get("BOOMI_BASE_URL")
"""Base URL for Boomi AtomSphere API."""
ACCOUNT_ID = os.environ.get("BOOMI_ACCOUNT_ID")
"""Account ID for Boomi AtomSphere API."""
USERNAME = os.environ.get("BOOMI_USERNAME")
"""Username for Boomi AtomSphere API. If using an API Token (recommended), then BOOMI_TOKEN. will prefix the 
username."""
PASSWORD = os.environ.get("BOOMI_PASSWORD")
"""Password for Boomi AtomSphere API. Often it is an API Token."""
ENVIRONMENT_NAME = os.environ.get("BOOMI_ENVIRONMENT_NAME")
"""Environment Name for deployments."""
ATOM_NAME = os.environ.get("BOOMI_ATOM_NAME")
"""Atom Name for deployments."""
ATOM_NAME_DR = os.environ.get("BOOMI_ATOM_NAME_DR")
"""Atom Name for DR deployments."""
COMPONENT_GIT_URL = os.environ.get("BOOMI_COMPONENT_GIT_URL")
"""Git URL for component. Used when copying component XML to a repository."""
CLI_BASE_DIR = os.environ.get("BOOMI_CLI_BASE_DIR", "")
"""Base directory for Boomi CICD CLI scripts. Optional."""
RELEASE_BASE_DIR = os.environ.get("BOOMI_RELEASE_BASE_DIR", "")
"""Base directory for the release json file. Optional."""
RELEASE_FILE = os.environ.get("BOOMI_RELEASE_FILE")
"""The name of the release json file. RELEASE_FILE is often concatenated with RELEASE_BASE_DIR."""
ENV_RELEASE_FILE = os.environ.get("BOOMI_ENV_RELEASE_FILE")
"""The name of the environment extensions release json file. ENV_RELEASE_FILE is often concatenated with 
RELEASE_BASE_DIR."""
COMPONENT_REPO_NAME = os.environ.get("BOOMI_COMPONENT_REPO_NAME", "boomi_components")
"""The name of the component repository used within the component-xml scripts. boomi_components is the default value. """
SONAR_RULES_FILE = os.environ.get(
    "BOOMI_SONAR_RULES_FILE", "boomi_cicd/templates/sonarqube/BoomiSonarRules.xml"
)
"""Location of the SonarQube rules file. boomi_cicd/util/sonarqube/BoomiSonarRules.xml is the default location within 
the library."""
SONARQUBE_HOST_URL = os.environ.get("BOOMI_SONARQUBE_HOST_URL", "")
"""URL for SonarQube."""
SONARQUBE_PROJECT_KEY = os.environ.get("BOOMI_SONARQUBE_PROJECT_KEY", "")
"""Project Key for SonarQube."""
SONARQUBE_TOKEN = os.environ.get("BOOMI_SONARQUBE_TOKEN", "")
"""Token for SonarQube."""

# Set AtomSphere API Rate Limit -- 10 calls per second
CALLS_PER_SECOND = os.environ.get("BOOMI_API_CALLS", 10)
"""Number of calls to the Boomi AtomSphere API per second. Default is 10."""
RATE_LIMIT_SECONDS = 1
RATE_LIMIT_MILLISECONDS = RATE_LIMIT_SECONDS * 1000

# Set AtomSphere API XML namespace
NAMESPACES = {"bns": "http://api.platform.boomi.com/"}
