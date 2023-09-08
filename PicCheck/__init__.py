import os
import yaml


def get_env():
    # 这里获取设置的环境变量
    env = os.environ.get("ENV")
    if env is None:
        env = "debug"
    return env


def load_config():
    env = get_env()
    path = f"config_{env}.yaml"
    with open(path, encoding='utf-8') as f:
        cfg = yaml.load(f.read(), Loader=yaml.FullLoader)
        print(f"当前运行环境:{env}")
        return cfg


class Config(object):
    def __init__(self, cfg: str):
        self.cfg_type = cfg
        self.config = load_config()

    def get_config(self, key: str):
        return self.config[self.cfg_type][key]


postgresql_cfg = Config("POSTGRESQL")
