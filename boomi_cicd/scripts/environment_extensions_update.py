import boomi_cicd

# The environment_extensions_update.py script updates the environment extensions for the
# environment set within the environment variables json.


# Open environment extensions release json
env_ext_release = boomi_cicd.set_env_release()
environment_id = boomi_cicd.query_environment(boomi_cicd.ENVIRONMENT_NAME)
boomi_cicd.update_environment_extensions(environment_id, env_ext_release)
