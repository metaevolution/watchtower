import json
from watchtower.logging_config import logger
from watchtower.models import Config, Host

DEFAULT_CONF_FILENAME = "watchtower.json"

class InvalidWatchTowerConfigException(Exception):
    pass


class AppConfig:
    def __init__(self, conf_file=DEFAULT_CONF_FILENAME):
        json_conf = self.load_json_from_file(conf_file)
        logger.debug("Loaded json config from file: %s", json_conf)

        self._config = self.load_config(json_conf)
        logger.debug("Loaded json into Config model: %s", self._config)


    @property
    def config(self):
        return self._config    
    
    def load_json_from_file(self, filename: str) -> None:
        with open(filename, "r") as conf_file:
            return json.load(conf_file)
            

    def load_config(self, json_config: dict):
        return Config.from_dict(json_config)
    
    # def validate_config(self, conf: dict) -> bool:  
        

    # def validate_test(self, test: dict):



    

            
        
