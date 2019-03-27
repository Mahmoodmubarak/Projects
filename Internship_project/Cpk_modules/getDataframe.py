"""
@file getDataframe.py
This module defines functions to parse data from a single logfile and converts it in DataFrame.
Performs multiple transformation on DataFrame and returns a single DataFrame.

"""

import re
import pandas as pd
import numpy as np
import sys

DEBUG = False

# Dictionary of Patterns:
patterns = {}

# ____________________________Defining patterns to parse data from a logfile___________________________________________.

# Meta data
pattern_STversion   = re.compile('  ST Version: (?P<ST_Version>.+)')
pattern_RHELversion = re.compile('RHEL version: (?P<RHEL_Version>.+)')
pattern_WorkStation = re.compile(' Workstation: (?P<WorkStation>.+)')
pattern_TimeStamp   = re.compile('TestSessionData.StartTimeStamp="(?P<TimeStamp>(?P<Date>[0-9-]{10}) (?P<Time>[0-9:.]{11}))')

KEY_STVersion   = 'ST_Version'
KEY_RHELversion = 'RHEL_Version'
KEY_Workstation = 'WorkStation'
KEY_Timestamp   = 'TimeStamp'
KEY_Date        = 'Date'
KEY_Time        = 'Time'


patterns[KEY_STVersion]   = pattern_STversion
patterns[KEY_RHELversion] = pattern_RHELversion
patterns[KEY_Workstation] = pattern_WorkStation
patterns[KEY_Timestamp]   = pattern_TimeStamp

# TestSession Data
pattern_TestSession = re.compile('TestSessionData.(?P<HwIDs>.+)="(?:HighLevelSerialNumber = (?P<HighLevelSerialNumber>[-A-Z0-9 ]+)(?:, Vendor = (?P<Vendor>[A-Z0-9]{2}), PartNumber = (?P<PartNumber>[-A-Z0-9]{10,12}), SerialNumber = (?P<SerialNumber>[0-9]{1,6}), EdcOracle = (?P<EdcOracle>[0-9]{1,3}), ManufacturerProductionDate = (?P<ManufacturerProductionDate>[0-9]{0,3})(?:(?:, FpgaBundle = (?P<FpgaBundel>.+))|(?:, FpgaRevision = (?P<FpgaRevision>.+)))?)?)"')
KEY_TestSession = 'TestSession'
patterns[KEY_TestSession] = pattern_TestSession


# Test Data
pattern_RunNumber      = re.compile('[*]+ Run Number: (?P<RunNumber>[0-9]+)')
pattern_Usagelines     = re.compile('(?P<Usagelines>#[1-4]:.+)')
pattern_Data           = re.compile('(?P<Data>(?:[PF]_;>>;)(?:.+))')

KEY_RunNumber = 'RunNumber'
KEY_Usagelines = 'Usagelines'
KEY_Data = 'Data'

patterns[KEY_RunNumber] = pattern_RunNumber
patterns[KEY_Usagelines] = pattern_Usagelines
patterns[KEY_Data] = pattern_Data

def e(): return sys.exit(1)

def getMeasGroups(cols, measlabels):

    """
    This function group column names in a dictionary as {'measlabel': list of GroupedCols}:
    {'A1':[A1, U1, L1, R1], 'A2':[A2, U2], 'A3':[A3, U3, R3]}
    Note:
    Logfiles may have one or multiple measurments. In Usageline #1 the measurment columns are labeled as 'A1', 'A2'...'AN'.
    'measlabel' represents those measuments.

    @param cols (str) list of columns
    @param measlabels (int) number of measurments in a logfile
    @return dictionary Key = measlabel  and Value = list of GroupedCols
    """

    measGroups = {}
    for key in measlabels:
        idx = key.replace('A', '')
        pattern = 'A' + idx + '|U' + idx + '|L' + idx + '|R' + idx
        measGroups[key] = list(set(re.findall(pattern, cols)))
    return measGroups

def updateKeys(Dict):
    """
    this function updates keys of dictionary
    @param Dict
    @return updated dictionary
    """
    groupDict = {}

    for key, value in Dict.items():
        if 'A' in key:
            groupDict['MeasValues'] = value
        elif 'U' in key:
            groupDict['U1_'] = value
        elif 'L' in key:
            groupDict['L1_'] = value
        elif 'R' in key:
            groupDict['R_'] = value
    return groupDict

def getGroupsValuesDF(Series):
    """
    This fucntion iterate over each value of Series and each value is a list.
    Unpack the values from Dataframe['Grouped Values'] in columns as ['MeasValues', 'U1', 'L1', 'R']
    @param Series
    @return Dataframe
    """
    GroupsData = {}
    for Idx, Dict in Series.items():
        GroupsData[Idx] = updateKeys(Dict)
    Dataframe = pd.DataFrame.from_dict(GroupsData, orient='index')
    # add missing column if any of ['U1_','L1_', 'R1_']
    missing_col = ['U1_','L1_', 'R_']
    cols = Dataframe.columns.tolist()
    for col in missing_col:
        if col not in cols:
            Dataframe[col] = np.nan

    return Dataframe


def processFile(filepath):

    """
    This function parse the logfile using regular expressions. Converts the parsed data into a Dataframe.
    This function only parse logfiles have all the four Usagelines.
    @param filepath its a logfile relative path
    @return parsed data as Dataframe
    """
    # Initallizing Data Containers for HLA Serial Number, Metadata, TestSessionData, TestData__________________________:

    MetaData_keys = [KEY_STVersion, KEY_RHELversion, KEY_Workstation, KEY_Timestamp, KEY_Date, KEY_Time]
    MetaData = {}

    TestSessionData_key = ['HwIDs', 'HighLevelSerialNumber', 'Vendor', 'PartNumber', 'SerialNumber', 'EdcOracle', 'ManufacturerProductionDate', 'FpgaBundel', 'FpgaRevision']
    TestSessionData = []

    TestData_keys = [KEY_RunNumber, KEY_Usagelines, KEY_Data]
    TestData = []
    ulcount = 0     # ulcount => UsageLine Count
    runNumber = ''

    # Reading log file and parsing MetaData, TestSessionData and TestData into relavent containers.

    with open(filepath, 'r') as ifile:

        for line in ifile.readlines():
            #print(line)
            for key in patterns:
                pattern = patterns[key]
                m = pattern.match(line)

                if m is not None:
                    obj = m.groupdict()
                    key = list(obj.keys())[0]

                    # Capturing Metadata:
                    if key in MetaData_keys:
                        MetaData.update(obj)

                    # Capturing Testsessiondata:
                    elif key in TestSessionData_key:
                        TestSessionData.append(obj)

                    # Capturing Testdata and adding RunNumber:
                    elif key in TestData_keys:
                        #print('pass3')
                        if key == KEY_RunNumber:
                            runNumber = obj[key]

                        if key == KEY_Usagelines:
                            ulcount += 1

                            if ulcount == 1:
                                #line += ';RunNumber'
                                TestData.append(line.strip().replace('_', '').split(';'))

                            if ulcount == 4:
                                #line += ';RunNumber'
                                TestData.append(line.strip().split(';'))

                        if key == KEY_Data:
                            #line += ';' + runNumber
                            TestData.append(line.strip().split(';'))

    # Check if logfile has all the 4 usage lines. If not then return empty dataframe.
    if ulcount != 4:
        return pd.DataFrame()
    # ============================= Converting 'TestData'into Dataframe and filtering columns =========================

    cols = str(TestData[0])
    selected_cols = re.findall('[mAULRs]{1}[0-9]{1,}', cols)
    return pd.DataFrame(TestData[1:], columns=TestData[0])[selected_cols]

# ================================= Perform Transformation on DataFrame ===============================================
# =====================================================================================================================

def getDataFrame(file):
    """
    This function performs all the heavy lifting. Following are the data transformation steps to get final dataframe:
    - processFile function returns initial DataFrame, only with required data columns.
    - Convert selected columns data to numeric i.e Measurments, Upperlimit, Lowerlimit, Expected Value eg: [A1, U1, L1, R1]
    - Add grouped columns in DataFrame.
      Example: Column 'A1', Values: dict {A1:val1, U1:val2, L12:val3, R1:val4},
              Column 'A2', Values : dict {A2:val5, U2:val6}
    - Dropping excess columns Upperlimits[U1,U2,..UN], lowerlimits[L1,L2,..,LN], ExpectedValues[R1,R2,..,RN] from DataFrame
    - Unpivoting DataFrame to four columns as ['s0','m0','MeasNames','Grouped Values'] + settings columns
    - Unpack the the values from Dataframe['Grouped Values'] into columns as ['MeasValues', 'U1', 'L1', 'R']
    - Dropping Dataframe['Grouped Values'] column.
    - Concatenating DataFrame with groupedValues_DF to get final Dataframe
    - Overwriting measlabels with measNames as {'A1':'measuredfrequency', 'A2':'diffrequency'}

    @param file its file path
    @return Dataframe
    """
    DataFrame = processFile(file)

    # Check if dataframe is empty or not.
    if DataFrame.empty:
        return pd.DataFrame()

    cols_list = DataFrame.columns.tolist()
    if DEBUG: print('Initial Dataframe columns:','\n', cols_list, '\n')

    cols_str = str(cols_list)

    # Create measNames_dict:
    # measlabels -->  'A1', 'A2', ..., 'AN'
    # measNames  -->  'measuredfrequency', 'difffrequency'

    measNames_dict =  {}  # eg: {'A1':'measuredfrequency', 'A2':'difffrequency'}
    measlabels = re.findall('[A]{1}[0-9]{1,}', cols_str)
    if DEBUG: print('Measurements Labels:', '\n', measlabels, '\n')

    for i in measlabels:
        measName = DataFrame.loc[0,i]
        measNames_dict[i] = measName

    # Create MeasGroups dictionary --> {'A1':[A1, U1, L1, R1], 'A2':[A2, U2],  'A3':[A3, U3, R3]} # {'measlabel': GroupedCols}
    measGroupsDict = getMeasGroups(cols_str, measlabels)
    if DEBUG: print('Measgroups Dictionary:', '\n', measGroupsDict, '\n')

    # Create settings dictionary
    settings_dict = {}
    non_settingsLabels_set = set(re.findall('[AULRm]{1}[0-9]{1,}|s0', cols_str))
    settingsLabels_set = set(cols_list).difference(non_settingsLabels_set)
    settingsLabels = list(settingsLabels_set)
    if DEBUG: print('Settings Labels', '\n', settingsLabels, '\n')

    for i in settingsLabels:
        setting = DataFrame.loc[0, i]
        settings_dict[i] = setting

    # Step 2:Add grouped columns in DataFrame

    DataFrame.drop(0, inplace=True)
    DataFrame.reset_index(inplace=True, drop=True)

    # convert columns to numeric
    numeric_cols = re.findall('[AULR]{1}[0-9]{1,}', cols_str)

    if DEBUG: print('Columns to be converted to float data type:', '\n', numeric_cols, '\n')

    for col in numeric_cols:
        try:
            DataFrame[col] = pd.to_numeric(DataFrame[col]) # , errors='coerce'
        except ValueError as error:   # ValueError: Unable to parse string "ok"
            return pd.DataFrame()
            #DataFrame[col] = DataFrame[col].map({'ok': 1.0})
            #if DEBUG: print(error)



    # In case of other exceptional values, cast them as 1.0.
    #DataFrame.fillna(0.0, inplace=True)


    # Add grouped columns in DataFrame
    # column 'A1', Values: dict {A1:val1, U1:val2, L1:val3, R1:val4}, column 'A2', Values : dict {A2:val5, U2:val6}

    for measlabel, GroupedCols in measGroupsDict.items():
        DataFrame[measlabel] = DataFrame.loc[:, GroupedCols].to_dict('records')

    # droping excess columns Upperlimits[U1,U2,..UN], lowerlimits[L1,L2,..,LN], ExpectedValues[R1,R2,..,RN]
    limitsCols = re.findall('[ULR]{1}[0-9]{1,}', cols_str)
    if DEBUG: print('Limits columns Labels:', '\n', limitsCols, '\n')

    DataFrame.drop(columns=limitsCols,inplace=True)

    rename_cols_dict = {'s0':'HwIds','m0':'MeasPointIds'}
    rename_cols_dict.update(settings_dict)
    DataFrame.rename(columns= rename_cols_dict, inplace=True)

# Step 3: Unpivoting DataFrame to four columns as ['s0','m0','MeasNames','Grouped Values'] + settings columns

    DataFrame = pd.melt(DataFrame, id_vars=list(rename_cols_dict.values()), var_name='MeasNames', value_name='Grouped Values')

    # Step 4: Unpack the the values from DataFrame['Grouped Values'] in columns as ['MeasValues', 'U1_idx', 'L1_idx', 'R1_idx']

    Series = DataFrame.loc[:, 'Grouped Values']
    # Series --> groupedValues_DF --> drop 'Grouped Values' column from DataFrame --> DataFrame = pd.concat(DataFrame + groupedValues_DF)

    groupedValues_DF = getGroupsValuesDF(DataFrame.loc[:, 'Grouped Values'])
    DataFrame.drop(columns= 'Grouped Values', inplace=True)

    # Overwriting measlabels with measNames as {'A1':'measuredfrequency', 'A2':'diffrequency'}
    for label, Name in measNames_dict.items():
        index_lst = DataFrame.index[DataFrame['MeasNames'] == label]
        DataFrame.loc[index_lst, 'MeasNames'] = Name
    # Concatenating DataFrame with groupedValues_DF to get final Dataframe
    DataFrame = pd.concat([DataFrame, groupedValues_DF], axis=1)
    if DEBUG: print(DataFrame.columns.tolist())

    return DataFrame

#Module Testing Script:
if __name__ == '__main__':

    files_broke_script = ['/MNT_PROD/data/WaveScale/N2601-66601_001065/2018081412h52m35s_bbac6091/PS1600/Centipede.Channel.Receiver.Standard.SingleEnded.Time.Skew.Misc.Reset.Apply.2018.08.14.12h52m35s.th194874.log']

    for file in files_broke_script:
        DF = getDataFrame(file)
        print(DF)
        e()
