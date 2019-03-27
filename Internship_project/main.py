
"""
@file main.py
This file controls the program execution. The modules are defined seperately and are connected here.
"""

# Built-in liberaries
import os
from os import sys, path
from datetime import datetime
import json
import logging

# Installed liberaries
import xlsxwriter
import pandas as pd

os.environ['LANG'] = 'de_DE.utf-8'

# Imported Cpk modules
from Cpk_modules import getFilenames
from Cpk_modules import getDataFrame
from Cpk_modules import mergeDataFrames
from Cpk_modules import Bar
from Cpk_modules import getExcelfile, getSheetName, getgroupedCells
from Cpk_modules import ConfigFile, valueCheck, loadConfigfile

logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
                    datefmt='[%d-%b-%y %H:%M:%S]', filename='/tmp/Cpk_Tool.log', filemode='a')


DEBUG = False

# Not in use so far
SN_dict = {}            # key : 'SN' and value: [list of HW_info_DF]
                     # eg: {'001085': [HWData_DF1, HWData_DF2]}

# Not implemented yet.
# 'default_path' is the path of a file which is being updated every three hr.
# This file has all the files paths available in /MNT_PROD directory.
default_path = '..........'

def e(): return sys.exit(1)

# **************************************** Program Execution *********************************************************


#sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
#sys.path.append(path.dirname(path.abspath(__file__)))
startTime_total = datetime.now()

# Step 1: Config file initialization ________________________________________________________________________________:

jsonObj = sys.argv[1]
cfgDict = loadConfigfile(jsonObj)
cfgObj = ConfigFile(cfgDict)

logging.info('Configuration file: ')
logging.info(cfgDict)

# Setting up default OUTPUT_DIR path if no OutputDir path is specified in config file.
OutputDir = cfgObj.outputDir()
if not os.path.isdir(OutputDir):
    pathname = os.path.dirname(sys.argv[0])
    OutputDir = os.path.abspath(pathname) +'/'+'Excel_Outputfiles/'
    print('\n')
    print('OutputDir field in configuration file is invalid.')

# Checking BINS value. The default value is 5.
Bins = valueCheck(cfgObj.bins(), 5)

# Checking %OUTLIERS value. The default value is 10.
Outliers_percent = valueCheck(cfgObj.outliers_percentage(),10)

# cfgObj.hide_groups() method will return boolean values. If user want to keep histrogram and settings columns in
# excel output, this method will return (True, True):
keep_hist, keep_settings = cfgObj.hide_groups()

# Specify path for input files:
ROOT_DIRs = cfgObj.rootDir()
# check if the ROOT_DIRs is empty then ROOT_DIRs == default_path, to get files path based on config file.
if len(ROOT_DIRs) == 0:
    ROOT_DIRs = default_path
    print('Please specify the correct Path in configuration file...')
    e()

# Initializing filter object:
Filters = cfgObj.filenameFilter()
#print(Filters)

# Exclude files while getting file names
exclude_files_base = ['linearity', 'ReadFromHardware', 'DutyCycleCheck', 'BadcLinearity', 'WritePartitionTable','MaintenanceRunSummary']
exclude_files_config = cfgObj.exclude_files()
exclude_files = exclude_files_base + exclude_files_config
#print(exclude_files)

# Specify excel output file name:
Username = os.environ["USER"]
TimeStamp = str(datetime.now().strftime('%Y-%m-%d_%Hh%Mm%Ss'))

if cfgObj.Excel_fileName() == "":
    fileName = Username
else:
    fileName = cfgObj.Excel_fileName()

ofile = OutputDir + fileName + '_' + TimeStamp + '.xlsx'

# Step 2: Select files based on configuration file ________________________________________________________________:
print('\n')
print('Selecting Logfiles ..................................................................')
Time1 = datetime.now()
testNames_dict, filesCount = getFilenames(ROOT_DIRs, Filters, exclude_files)

logging.info('Number of Unique testNames:', len(testNames_dict))
logging.info('List of Unique testNames:', '\n')
for key in testNames_dict.keys(): logging.info(key)

T1 = datetime.now() - Time1
print('\n')
print('Total number of logfiles selected: {0}'.format(filesCount))
print('Process time : ' + str(T1))
print('\n')

# Step 3: Parse data from single file as Dataframes __________________________________________________________________:

print('Processing logfiles to generate Excel output file........... ....................')
# Unpacking the testNames_dict with key= "test_ID", val= [list of file paths]
i1 = 0
i2 = 0
Time2 = datetime.now()

with xlsxwriter.Workbook(ofile) as Workbook:
    cpk_format = Workbook.add_format({'bg_color': '#FFFF00'})

    for testName, groupsDict in testNames_dict.items():
        # Initalizing list to store Dataframe from single file.
        # Once loop is over DF_list is passed as argument to mergeDataframes() function.
        """
        testNames_dict:
            {'testname1': {group1: [filepath1, filepath2, filepath3, filepath4], --->mergedDF1 --> finalMergedDF for excel worksheet
                           group2: [filepath1, filepath2, filepath3]             --->mergedDF2 -->
                           },
                           
             'testname2': {group1: [filepath1, filepath2, filepath3, filepath4], --->mergedDF1 --> finalMergedDF for excel worksheet
                           group2: [filepath1, filepath2]                        --->mergedDF2 -->
                           }
            }
        """

        Number_of_groups = len(groupsDict)
        mergedDF_lst = []
        IDs_Settings_DFs = []

        idx = 0  # Number of groups to compare
        for group, filesList in groupsDict.items():
            DFs_list = []

            for file in filesList:
                if DEBUG: print(file)
                fname = file.split('/')[-1]
                i1 += 1
                # Initializing a progress bar
                Bar(i1, total=filesCount, text=fname)

                # Reading logfile and parsing and manipulating data as DataFrame: ----------> processing singlefile
                TestData_df = getDataFrame(file)

                # Append DataFrames in DF_list.
                # if TestData_df is not empty append TestData_df to DFs_list else skip
                if DEBUG: print(testName, '\n', 'Number of Datafames in DFs_list: ', len(DFs_list), '\n')
                if not TestData_df.empty:
                    DFs_list.append(TestData_df)


# Step 4: Concate/mergeing Dataframes and perform transformation ______________________________________________________:

            # Check if DFs_list is not empty
            if len(DFs_list) != 0:
                idx += 1
                mergedDF, IdsDF, settingDF = mergeDataFrames(DFs_list, Bins, Outliers_percent, keep_hist, IDX = str(idx))
                mergedDF_lst.append(mergedDF)

                # IdsDF and settingDF is set common for specific test name group(Worksheet)
                if len(IDs_Settings_DFs) == 0:
                    # STATS_0 columns appear in Output file if there are atleast two groups in Config file.
                    if Number_of_groups > 1:
                        # Add empty STATS_0 columns
                        STATS_0 = ['STATS_0', 'Mean_A', 'Mean_R', 'Stdev_R', 'Cpk_R']
                        for col in STATS_0: IdsDF[col] = ''

                    # Appending IdsDF, settingsDF in to IDs_Settings_DFs list
                    IDs_Settings_DFs.append(IdsDF)
                    # If keep_settings is True, settings columns will appear in final excel output
                    if keep_settings:
                        IDs_Settings_DFs.append(settingDF)

        # Concatenate Dataframes from mergedDF_lst to get finalDF,
        if len(mergedDF_lst) != 0:
            finalDF = pd.concat(mergedDF_lst, axis=1, join='inner')

            # Concatenating IDs + finalDF + Settings in to FinalDF for Excel workbook.
            if keep_settings:
                FinalDF = pd.concat([IDs_Settings_DFs[0], finalDF, IDs_Settings_DFs[1]], axis=1, join='inner')
            else:
                FinalDF = pd.concat([IDs_Settings_DFs[0], finalDF], axis=1, join='inner')

            FinalDF.reset_index(inplace=True)
            FinalDF.fillna('', inplace=True)
            FinalDF_cols = FinalDF.columns.tolist()
            #print(FinalDF_cols)

# Step 4: Writing FinalDF to excel _______________________________________________________________________________:
            # Excel Table Number
            i2 += 1
            table_Num = str(i2)
            len_table_Num = len(table_Num)

            # Number of groups in a worksheet
            groups = idx

            # Get paramters for Worksheet.add_table(table_range, options) function.
            table_range, options, cpkCells_lst = getExcelfile(FinalDF, groups, idx=table_Num)

            # Get worksheet name
            sheetName = getSheetName(testName, table_Num)
            # Initialize worksheet and adding table to it.

            Worksheet = Workbook.add_worksheet(sheetName)
            Worksheet.write(0, 0, testName)
            Worksheet.add_table(table_range, options)

            # Applying formatting to work sheet
            # 1) Cpk cells Conditional formatting:
            for cells in cpkCells_lst:
                Worksheet.conditional_format(cells,    {     'type': 'cell',
                                                         'criteria': '<',
                                                            'value': 2,
                                                           'format': cpk_format})

            # 2) Apply grouping to columns
            groupedCols_lst = getgroupedCells(FinalDF_cols)
            for colsRange in groupedCols_lst:
            #print(colsRange)
                Worksheet.set_column(colsRange, None, None, {'level': 1, 'hidden': True})

            # 3) Freezing header row and first four columns
            Worksheet.freeze_panes(2, 4)

T2 = datetime.now() - Time2
print(T2)
print('\n')
Total_Time = T1 + T2
print('The Excel Output file directory path:  ')
print(OutputDir)
print('\n')
print("Total program execution time: {0}".format(Total_Time))

# TODO: Define relationship to link HW_info_df to final merged_df.
# Appending 'HW_info_df' for each SN in SN_dict:
# if SN not in SN_dict:
#    SN_dict[SN] = []
# SN_dict[SN].append(HwData_DF)
# Updating TestID_Dfs_info dictionary
# TestID_DF_info[testName] = [len(DFs_dim), dict(Counter(DFs_dim))]