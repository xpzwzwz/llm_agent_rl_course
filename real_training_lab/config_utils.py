from pathlib import Path


def load_yaml_config(path):
    if not path:
        return {}
    import yaml

    with Path(path).open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"config must be a mapping: {path}")
    return data


def apply_config_defaults(parser, config_path):
    config = load_yaml_config(config_path)
    if config:
        parser.set_defaults(**config)
    return config

