import os

def load_properties():
    # 全部加载到环境变量中
    with open("config.properties","r",encoding="utf-8") as r:
        for line in r.readlines():
            if not line.startswith("#"):
                kv = line.strip().split("=")
                key = kv[0]
                value = kv[1]
                os.environ[key] = value


load_properties()