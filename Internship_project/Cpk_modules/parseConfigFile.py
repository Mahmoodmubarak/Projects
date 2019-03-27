"""
@file parseConfigFile.py
This module defines class to parse the configuration file fields.

"""
import json

class ConfigFile():
    """
    This class takes jason object as argument. Class methods are defined to parse each key value pair.
    """

    def __init__(self, cfg):
        self.cfg = cfg

    def Excel_fileName(self):
        return self.cfg['FILE_NAME']

    def outputDir(self):
        return self.cfg['OUTPUT_DIR']

    def bins(self):
        return self.cfg['BINS']

    def outliers_percentage(self):
        return self.cfg['%OUTLIERS']

    def hide_groups(self):
        hist = self.cfg['HIDE_GROUPS']['Hist']
        settings = self.cfg['HIDE_GROUPS']['Settings']
        return hist, settings

    def exclude_files(self):
        return self.cfg['EXCLUDE_FILES']

    def rootDir(self):
        paths_list = [group['Path'] for group in self.cfg['GROUPS']]
        return paths_list

    def filenameFilter(self):
        obj = {}
        idx = 0
        groups = ['group' + str(i) for i in range(1, len(self.cfg['GROUPS'])+1)]

        for groupDict in self.cfg['GROUPS']:

            key = groups[idx]
            obj[key] = {}
            idx += 1
            for k in 'VARIANT HW TASK TRANSITION TEST YEAR MONTH'.split():
                obj[key][k] = groupDict[k]
        return obj

# Load config.json file into python dict object
def loadConfigfile(cfgFile):
    cfgDict = {}
    with open(cfgFile, 'r') as f:
        cfgDict.update(json.load(f))
    return cfgDict

def valueCheck(value, default_value):
    """
    This function will check value (give by user in configuration file).
    If conditions are not satisfied the default value of 5 is used.
    @param value: value passed
    @param default_value: default value passed
    @return: int value
    """
    if isinstance(value, int):
        if value < default_value:
            value = default_value
    else: value = default_value
    return value


