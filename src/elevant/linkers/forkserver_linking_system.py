from elevant.linkers.linking_system import LinkingSystem
from elevant import settings
import json

with open(settings.TMP_FORKSERVER_CONFIG_FILE, "r", encoding="utf8") as file:
    config = json.load(file)

if "no_loading" in config and config["no_loading"]:
    linking_system = None
else:
    linking_system = LinkingSystem(config["linker_name"],
                                   config["linker_config"],
                                   coref_linker=config["coreference_linker"],
                                   min_score=config["minimum_score"],
                                   type_mapping_file=config["type_mapping"])
