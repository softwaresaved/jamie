from configparser import ConfigParser


""" A config parser that use the inbuild configParser but add
    the possibility to parse a list of value separated with comma
    and return a list from it
    Source: http://stackoverflow.com/a/11866695
"""


class ConfigParserPerso(ConfigParser):
    """ Inherit from configparser and modify the method get() to
        return a list if it catch [ at the beginning and ] at the end
    """
    def getlist(self, section, option, **kwargs):
            value = self.get(section, option, **kwargs)
            try:
                return_list = list(filter(None, (x.strip() for x in value.splitlines())))
                return return_list
            except AttributeError:
                return value

    def getlistint(self, section, option):
        return [int(x) for x in self.getlist(section, option)]


def main():
    """ """
    parser = ConfigParserPerso()
    parser.read('../config_dev.ini')


if __name__ == '__main__':
    main()