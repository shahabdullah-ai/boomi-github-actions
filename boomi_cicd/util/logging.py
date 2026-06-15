import logging
import os
import sys


def info(msg):
    logging.info(msg)


def debug(msg):
    logging.debug(msg)


def warning(msg):
    logging.warning(msg)


def error(msg):
    logging.error(msg)


if os.environ.get("AZURE_HTTP_USER_AGENT") is not None:
    # Logging conf
    # Azure DevOps already includes the date/time
    logging.basicConfig(
        stream=sys.stdout,
        format="%(levelname)-5s %(message)s",
        level=logging.DEBUG,
    )
else:
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s.%(msecs)03d %(levelname)-5s %(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

# Use logger as the global name for logging with the boomi_cicd library.
logger = logging.getLogger()

header = r"""
    __                                                __
   / /_  ____  ____  ____ ___  (_)   _____(_)________/ /
  / __ \/ __ \/ __ \/ __ `__ \/ /   / ___/ / ___/ __  /
 / /_/ / /_/ / /_/ / / / / / / /   / /__/ / /__/ /_/ /
/_.___/\____/\____/_/ /_/ /_/_/____\___/_/\___/\__,_/
                             /_____/                              
"""
for line in header.splitlines():
    logger.info(line)
