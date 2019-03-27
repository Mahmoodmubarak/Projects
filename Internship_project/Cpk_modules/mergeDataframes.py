"""
@file mergeDataframes.py
This module defines functions that merges list of DataFrames.
"""

import sys
import pandas as pd
import numpy as np
import natsort
from .getHistrogram import getHistDataframe
from .outliersDetection import getOutliersDataframe


DEBUG = False

def applyIDX(lst, IDX):
    """
    This function takes list of columns names and add group number to the column name.
    @param lst list of column names.
    @param IDX group number.
    @return list of column names.
    """
    return [x+IDX for x in lst]

# ======================================= split merged DataFrame function =============================================

def split_Dataframe(mergedDF, settings_cols, IDX):
    """
    This function splits the merged Dataframe into Ids_DF, Limits_DF, Settings_DF.
    @param mergedDF Merged Dataframe
    @param settings_cols list of setting's column names
    @param IDX  group number
    @return Dataframes as  Ids_DF, Limits_DF, Settings_DF
    """
    # first drop duplicate rows based on "IDs" column, then drop "MeasValues" column,
    # finally change default index of mergedDF with 'IDs' column.
    DataFrame =mergedDF.reset_index().drop_duplicates(subset='IDs').drop(['MeasValues'], axis=1).set_index('IDs')

    # DataFrameCols = ['HwIds', 'MeasNames', 'MeasPointIds', 'R_', 'L1_', 'U1_', 'index', 'setupFrequency']
    # rename limits columns
    cols = ['R_'+IDX , 'L1_'+IDX, 'U1_'+IDX]
    cols_dic = {'R_':cols[0], 'L1_':cols[1], 'U1_':cols[2]}
    DataFrame.rename(columns=cols_dic, inplace=True)
    # Split DataFrame into Ids_DF, Limits_DF , Settings_DF
    Ids_DF = DataFrame[['HwIds', 'MeasNames', 'MeasPointIds']]
    Limits_DF = DataFrame[cols]
    Settings_DF = DataFrame[settings_cols]
    return Ids_DF, Limits_DF, Settings_DF

# ======================================= Samples DataFrame functions ==================================================

def getSamplesdict(arr, IDX):
    """
    This function takes an array as argument and returns dictionary object as:
    samplesdict = {'S0_1':232323, 'S1_1':232323, 'S2_1':232323,.... }

    @param arr array of samples values.
    @param IDX group number
    @return dictionay object
    """
    samplesdict = {}
    for idx, val in enumerate(arr):
        Id = 'S' + str(idx) + '_' + IDX
        samplesdict[Id] = val
    return samplesdict

def getSamplesDataframe(Series, IDX):
    """
    This function iterates over the Series. Each value is an array of sample values.
    Array values are unpacked to get the Samples Dataframe.
    @param Series pandas Series object.
    @param IDX group number.
    @return Samples Dataframe.
    """
    SamplesData = {}
    for ID, arr in Series.items():
        SamplesData[ID] = getSamplesdict(arr, IDX)
    return pd.DataFrame.from_dict(SamplesData, orient='index')

# ======================================= Merged DataFrame function ====================================================

def mergeDataFrames(DFs_list, Bins, Outliers, keep_hist, IDX):
    """
    This function merges list of Dataframes and performs multiple transformations before returning a final merged dataframe.
    The transform steps are as following:
        - Concatenate Dataframes from list of Dataframe along column as merged_DF.
        - Adding a new 'ID' column in 'merged_DF' by combining HwIds, MeasPointIds, MeasNames columns.
        - Split merged_DF into Ids_DF, Settings_DF, Limits_DF
        - Grouping the "MeasValues" with similar "index values" in an array. This will give a pd.Series object.
        - Getting default limits
        - Getting Outlier DataFrame as index = IDs & Columns = [L2, U2]
          After outlier detection new Upperlimit = U2 & new Lowerlimit = L2
        - Adding dummy columns to OutlierDF.
            i.e ['Type_', 'Factor_', 'L_', 'U_', 'Range_', 'FailsCounts_', 'Min_', 'Max_', 'Mean_', 'Std_', 'Cp_', 'Cpk_']
        - Drop IDs from UpdatedSeries where len(ARR) = 0
        - Getting Samples DataFrame as  index=IDs, Columns=[S0_1,S1_1,S2_1,S3_1......SN_1]
        - Getting Histrogram DataFrame as index= IDs, Columns= [B1_1,B2_1,.....BN_1]
        - Combine IDsDF, SampleDF, HistrogramDF, OutlierDF as FinalDF
        - Adding Empty columns in FinalDF as ['STATS_1', 'HIST_1', 'SAMPLES_1', 'LMT_1']
        - Rearranging columns in FinalDf as [ID_cols + LIMIT_cols + STATS_cols + HIST_cols + SAMPLES_cols + SETTINGS_cols]

    @param DFs_list list of DataFrames to merge.
    @param Bins is the number of columns to generate for Histrogram Dataframe.
    @param Outliers is the percentage of outliers to detect.
    @param keep_hist boolean(True/False)
    @param IDX number of groups
    @return a merged DataFrame. This DataFrame is passed to getExcelfile() function in main.py file.
    """

    # concatenating dataframes along columns
    merged_DF = pd.concat(DFs_list, ignore_index=True)
    # Adding a new 'ID' column in 'merged_DF' ________________________________________________________________________:

    merged_DF['IDs'] = merged_DF['HwIds'] + '|' + merged_DF['MeasPointIds'] + '|' + merged_DF['MeasNames']
    merged_DF.set_index('IDs', inplace=True)
    all_cols = merged_DF.columns.tolist()

    # Get setting columns:
    fixed_cols = ['HwIds', 'MeasPointIds', 'MeasNames', 'MeasValues','R_', 'U1_', 'L1_']
    settings_cols = [col for col in all_cols if col not in fixed_cols]

    # Split merged_DF into Ids_DF, Settings_DF, Limits_DF
    # ['MeasPointIds', 'index', 'setupFrequency', 'HwIds', 'MeasNames', 'R_', 'L1_', 'U1_', 'MeasValues']
    # Ids_DF = [ 'HwIds','MeasPointIds', 'MeasNames']
    # Limits_DF = ['R_', 'L1_', 'U1_']
    # Settings_DF = ['index', 'setupFrequency']

    IDs_DF, Limits_DF, Settings_DF  = split_Dataframe(merged_DF, settings_cols, IDX)
    Settings_DF['SETTINGS'] = ''
    Settings_DF = Settings_DF[['SETTINGS']+settings_cols]

    # Grouping the "MeasValues" with similar "index values" in an array. This will give a pd.Series object.
    Series = merged_DF.groupby([merged_DF.index])['MeasValues'].apply(np.array)

    # Getting default limits:
    default_limits = applyIDX(['L1_', 'U1_'], IDX)
    Default_limitDict = Limits_DF[default_limits].to_dict('index')

    # Getting Outlier DataFrame: index: IDs, Columns: [L2, U2]    ---> After outlier detection new Upperlimit = U2 & new Lowerlimit = L2
    OutlierDF, UpdatedSeries = getOutliersDataframe(Series, Default_limitDict, Outliers, IDX)

    # Adding dummy columns to OutlierDF.
    func_cols = ['Type_', 'Factor_', 'L_', 'U_', 'Range_', 'FailsCounts_', 'Min_', 'Max_', 'Mean_', 'Std_', 'Cp_', 'Cpk_']
    func_cols = applyIDX(func_cols, IDX)
    for col in func_cols:
        OutlierDF[col] = ''
    #print(OutlierDF.columns.tolist())

    # Drop IDs from UpdatedSeries where len(ARR) = 0.
    UpdatedSeries = UpdatedSeries[UpdatedSeries.map(len) > 0]
    #print(UpdatedSeries)

    # Getting Samples DataFrame: index: IDs, Columns: eg : [S0_1,S1_1,S2_1,S3_1......SN_1]
    SamplesDF = getSamplesDataframe(UpdatedSeries, IDX)
    # If there are no columns in SamplesDF return empty dataframe

    SamplesDF_cols = natsort.natsorted(SamplesDF.columns.tolist())
    SamplesDF = SamplesDF[SamplesDF_cols]
    # replacing nan values with mean of samples
    SamplesDF.T.fillna(SamplesDF.T.mean(), inplace=True)
    if DEBUG: print(SamplesDF.columns.tolist())
    #print(SamplesDF_cols)

    # Getting Histrogram DataFrame: index: IDs, Columns: eg: [B1_1,B2_1,.....BN_1]
    if keep_hist:
        HistrogramDF = getHistDataframe(UpdatedSeries, Bins , IDX)
        HistrogramDF_cols = natsort.natsorted(HistrogramDF.columns.tolist())
        HistrogramDF = HistrogramDF[HistrogramDF_cols]
        #print(HistrogramDF_cols)

        # Combine IDsDF, SampleDF, HistrogramDF, OutlierDF as FinalDF

        FinalDF = pd.concat([Limits_DF,OutlierDF, HistrogramDF, SamplesDF], axis= 1)
        FinalDF.index.name = 'IDs'

        # Adding Empty columns in FinalDF as ['STATS_1', 'HIST_1', 'SAMPLES_1', 'LMT_1']
        empty_Cols = ['LIMIT_', 'STATS_', 'HIST_', 'SAMPLES_']
        HIST_cols = ['HIST_' + IDX] + HistrogramDF_cols
    else:
        # Combine IDsDF, SampleDF, OutlierDF as FinalDF

        FinalDF = pd.concat([Limits_DF, OutlierDF, SamplesDF], axis=1)
        FinalDF.index.name = 'IDs'

        # Adding Empty columns in FinalDF as ['STATS_1', 'SAMPLES_1', 'LMT_1']
        # These are empty columns to group columns in excel output file.
        empty_Cols = ['LIMIT_', 'STATS_', 'SAMPLES_']

    empty_Cols = applyIDX(empty_Cols, IDX)

    for col in empty_Cols:
        FinalDF[col] = ''

    # Rearranging columns in FinalDf
    #ID_cols = ['HwIds', 'MeasPointIds', 'MeasNames']
    LIMIT_cols = ['LIMIT_'+IDX] + applyIDX(['R_','L1_','U1_','L2_','U2_','Type_', 'Factor_', 'L_', 'U_', 'Range_', 'FailsCounts_'],IDX)
    STATS_cols =  ['STATS_'+IDX] + applyIDX(['Min_', 'Max_', 'Mean_', 'Std_', 'Cp_', 'Cpk_'],IDX)
    #HIST_cols  =  ['HIST_' +IDX] + HistrogramDF_cols
    SAMPLES_cols =  ['SAMPLES_'+IDX] + SamplesDF_cols
    #SETTINGS_cols = ['SETTINGS'] + settings_cols

    #ColsList = ID_cols + LIMIT_cols + STATS_cols + HIST_cols + SAMPLES_cols + SETTINGS_cols
    if keep_hist: ColsList = LIMIT_cols + STATS_cols + HIST_cols + SAMPLES_cols
    else: ColsList = LIMIT_cols + STATS_cols + SAMPLES_cols
    FinalDF = FinalDF[ColsList]
    #print(FinalDF.columns.tolist())
    #print(IDs_DF.columns.tolist())
    #print(Settings_DF.columns.tolist())

    return FinalDF, IDs_DF, Settings_DF



"""

    if DEBUG:
        print('\n')
        print("Initial Merged Dataframe dimentions              :   {0}".format(merged_DF.shape))
        print("Number of rows in merged dataframe           :   {0}".format(merged_DF.shape[0]))
        print("Number of Unique IDs in mergerd dataframe    :   {0}".format(len(merged_DF['IDs'].unique())))


        print("Number of rows in IDsDF                     :  {0}".format(IDsDF.shape[0]))
        print(IDsDF.columns.tolist())
        print(IDsDF.head(5))
        with open("/home/marajput/src/Test_Outputs/IDs_DataFrame.txt", "w") as id_file:
            IDsDF.to_csv(id_file, encoding='utf-8', index=True)


        with open("/home/marajput/src/Test_Outputs/Series_index_Data.txt", "w") as series_file:
            for ID, arr in Series.items():
                series_file.write(ID.join(str(list(arr))))
                series_file.write('\n')


        print('\n', "Outliers Dataframe........................")
        print(OutlierDF.columns.tolist())
        print(OutlierDF.iloc[600:700][:])


        print('\n', "Samples Dataframe........................")
        print(SamplesDF.columns.tolist())
        print(SamplesDF.iloc[600:700][:])
        with open("/home/marajput/src/Test_Outputs/Samples_DataFrame.txt", "w") as Samples_file:
            SamplesDF.to_csv(Samples_file, encoding='utf-8', index=True)


        print('\n', "Histrogram Dataframe........................")
        print(HistrogramDF.columns.tolist())
        print(HistrogramDF.iloc[600:700][:])
        with open("/home/marajput/src/Test_Outputs/Histrogram_DataFrame.txt", "w") as Histrogram_file:
            HistrogramDF.to_csv(Histrogram_file, encoding='utf-8', index=True)


        print(FinalDF.columns.tolist())
        with open("/home/marajput/src/Test_Outputs/Final_DataFrame.txt", "w") as FinalDF_file:
            FinalDF.to_csv(FinalDF_file, encoding='utf-8', index=False)
"""
