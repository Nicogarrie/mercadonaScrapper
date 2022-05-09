from configparser import ConfigParser


def init_config_mercadona():
    return init_config(filename='config.ini', section='mercadona')


def init_config_postgres():
    return init_config(filename='config.ini', section='postgres')


def init_config(filename, section):
    config_params = {}

    parser = ConfigParser()
    parser.read(filename)

    if not parser.has_section(section):
        raise Exception(
            'Section {0} not found in the {1} file'.format(section, filename))

    params = parser.items(section)
    for param in params:
        config_params[param[0]] = param[1]

    return config_params
