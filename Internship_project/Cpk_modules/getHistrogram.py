"""
@file getHistrogram.py
This module defines functions to generate Histrogram Dataframe.
This function is used mergeDataframes.py file
"""


import pandas as pd

def getBinsRange(Max, Min, Width, Bins):
    """
    This function will generate the range of each bin
    @param Max maximum value in samples
    @param Min minimum value in samples
    @param Width width of a bin
    @param Bins number of bins specified in configfile
    @return list
    """
    BinsRange = [Min]
    val = Min

    for i in range(Bins):
        val += Width
        BinsRange.append(val)
    BinsRange[-1] = Max
    return BinsRange

def getFreqTable(arr, Range, bins, BinsRange, IDX):
    """
    This function create a dictionary with key as bin label and value as frequency of values with in that bin range.
    @param arr list of samples.
    @param Range range of sample distribution.
    @param bins number of bins defined in configuration file.
    @param BinsRange list of maximum value of bins.
    @param IDX group number.
    @return freqDict dictionary.
    """
    freqDict = {}
    for i in range(bins):
        Id = 'B' + str(i + 1) + '_' + IDX
        if Range == 0.0:
            count = 0
        else:
            count = len([x for x in arr if BinsRange[i] <= x <= BinsRange[i+1]])
        freqDict[Id] = count
    return freqDict

def getHistDataframe(Series, bins, IDX):
    """
    This function creates a histrogram dataframe.
    @param Series  pd.Series object.
    @param bins number of bins defined in configuration file.
    @param IDX group number.
    @return dataframe object
    """
    HistData = {}

    for ID, arr in Series.items():
        Max = arr.max()
        Min = arr.min()
        Range = Max - Min
        Width = Range / bins
        BinsRange = getBinsRange(Max, Min, Width, bins)
        HistData[ID] = getFreqTable(arr, Range, bins, BinsRange, IDX)

    return pd.DataFrame.from_dict(HistData, orient='index')


