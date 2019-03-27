"""
@file outliersDetection.py
This module defines function that uses generalized ESD algorithm to detect outliers.

"""

from __future__ import print_function, division
import numpy as np
import pandas as pd
from PyAstronomy import pyasl



def getOutliersDataframe(Series, Default_limitsDict, Outliers_percentage, IDX):
    """
    This function iterates over a Series. Each value is an array of sample values.
    The array is passed to algorithm to detect outliers and new Upper and lower limits are evaluated is any.
    Finally converts the new limit values to a Dataframe.

    @param Series pandas series object.
    @param Default_limitsDict Dictionary object.
    @param Outliers_percentage  to calculate maximum no of outliers to detect.
    @param IDX group number.
    @return Dataframe and Series without nan values.
    """
    OutliersDict = {}
    U1 = 'U1_'+IDX
    L1 = 'L1_'+IDX
    U2 = 'U2_'+IDX
    L2 = 'L2_'+IDX

    for ID, ARR in Series.items():

        Upperlimit = Default_limitsDict[ID][U1]
        Lowerlimit = Default_limitsDict[ID][L1]

        # Removing all nan values from the array
        ARR = ARR[np.logical_not(np.isnan(ARR))]
        Series[ID] = ARR[:]
        maxOLs = int(len(ARR) * Outliers_percentage/100)           # Maximum Outliers
        # Case 1 : If the standard deviation > 0.0 then use the algorithm to find outliers.
        if len(set(ARR)) > 1 and len(ARR) > maxOLs:
            # pyasl.generalizedESD will return a tuple of length  2 as eg:  r = (r[0],r[1])
            # r[0] --> Number of outliers
            # r[1] --> Indices of outliers
            if maxOLs < 1:
                maxOLs = 2

            r = pyasl.generalizedESD(ARR, maxOLs, 0.05)

            NumOutliers = r[0]
            # Case 1(a) : If there is any outlier then find new Upper/lower limits
            if NumOutliers > 0:
                outliers = [ARR[idx] for idx in r[1]]

                #print('List of Outliers', outliers )
                #print("   R(G_value)    Lambda(G_critical)")
                #for i in range(len(r[2])):
                #print("%2d  %8.5f  %8.5f" % ((i+1), r[2][i], r[3][i]))

                values_passed  = np.array([x for idx, x in enumerate(ARR) if idx not in r[1]])

                outliers_below_values_passed = [x for x in outliers if x < min(values_passed)]

                outliers_above_values_passed = [x for x in outliers if x > max(values_passed)]

                # if there is any outlier to the left of values_passed:
                if len(outliers_below_values_passed) > 0:
                    OL = max(outliers_below_values_passed) # First Outlier to the left of values_passed.
                    if OL > Lowerlimit: L = OL
                    else: L = Lowerlimit

                else: L = Lowerlimit

                # if there is any outlier to the right of data points
                if len(outliers_above_values_passed) > 0:
                    OU = min(outliers_above_values_passed)  # First Outlier to the right of values_passed.
                    if OU < Upperlimit: U = OU
                    else: U = Upperlimit

                else: U = Upperlimit


            else:
                L = Lowerlimit
                U = Upperlimit
        else:
            L = Lowerlimit
            U = Upperlimit

        OutliersDict[ID] = {L2: L, U2: U}

    OutliersDF  = pd.DataFrame.from_dict(OutliersDict, orient='index')
    OutliersDF = OutliersDF[[L2,U2]]   # ---> rearranging OutliersDF columns
    return OutliersDF, Series
