"""
@file getFilenames.py
This module defines functions to parse logfiles name and select them based on parameters given by user in configuration file.
"""


import re
import os, sys
from . import regex
from .progressbar import Bar

def e(): sys.exit(1)


def fileCounter_1(paths):

    """
    This function counts number of files in a specified path

    @param paths root path of directory
    @return Number of files in a directory, recursively counting files in subdirectories
    """
    files_count = 0
    for path in paths:
        for dir in path:
            files_count += sum(len(files) for _, _, files in os.walk(dir))
    return files_count

def matchFail(testname, excludefiles):
    i = 0
    for x in excludefiles:
        if x in testname:
            i += 1
    if i>0:
        return False
    else:
        return True

def getFilenames(ROOT_DIRs, Filters, exclude_files):

    """
    This function select file names based on configuration file

    @param ROOT_DIRs root directory for log files
    @param Filters parameters to parse logfile name
    @return list of selected logfiles
    """
    # Exclude files is a list of pattern, if found in testname then exclude that test name from selection.
    exclude_testnames = exclude_files
    # Initializing Variable for progressbar.Bar function i.e (i and Total).
    Bar()

    # fileCounter_1() counts number of files in selected dirs.
    total = fileCounter_1(ROOT_DIRs)
    i = 0

    testNames_dict = {}
    """{ 'testname1':  {group1: [filepath1,filepath2,filepath3,filepath4],  
                        group2: [filepath1,filepath2,filepath3]},
                                   
         'testname2':  {group1: [filepath1,filepath2,filepath3,filepath4],
                        group2: [filepath1,filepath2]}  
        }
    """

    filesCount = 0
    idx = 1
#   print(ROOT_DIRs)

    for dirList in ROOT_DIRs:

        group = 'group' + str(idx)
        idx += 1
        pattern = re.compile(regex.getRegex(Filters[group]))

        for rootPath in dirList:
            #print(rootPath)
            for path, dirs, files in os.walk(rootPath):

                i += len(files)

                Bar(i, total)
                for filename in files:

                    full_path = '{0}/{1}'.format(path, filename)

                    m = pattern.match(filename)

                    if m is None:
                        #print(filename + " doesn't match pattern")
                        continue

                    if not os.path.isfile(full_path):
                        #print(filename + " doesn't exist")
                        continue

                    if m is not None:

                        testName = filename.split('.201')[0]
                        #print('\n')
                        #print(testName)

                        # if the strings in the 'exclude_files list' are in testname, matchFail() function will return false, else return True
                        include = matchFail(testName, exclude_files)
                        # if 'include' is True the testname will be add in testNames_dict.
                        if include:
                            filesCount += 1
                            #print(testName)
                            if filesCount > 0:
                                if testName not in testNames_dict:
                                    testNames_dict[testName] = {group: []}

                                if group not in testNames_dict[testName]:
                                    testNames_dict[testName].update({group: []})

                                testNames_dict[testName][group].append(full_path)

                    else:
                        continue

    return testNames_dict, filesCount
