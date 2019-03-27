"""
@file getExcelFile.py
This module define functions that generate values for parameters i.e table_labels, options.
These parameters are passed to worksheet.add_table() function in main.py file.
"""
import pandas as pd
import xlsxwriter
import re

DEBUG = True

def getExcelLabel(N):
    """
    This function converts the column number to an excel equivalent column Label eg: 1 = A
    @param N string number as eg: '1'
    @return excel column label
    """
    return xlsxwriter.utility.xl_col_to_name(N)

def getSheetName(testName, table_Num):
    """
    This function will return work sheet name which should be less than 31 characters.
    @param testName: str testName of log files
    @param table_Num: str Excel Table number
    @return: str sheetName
    """
    table_Num = '.T'+ table_Num
    len_table_Num = len(table_Num)

    # Defining worksheet name
    sheetName = '.'.join([i[:3] for i in testName.split('.')])
    len_sheetName = len(sheetName)

    if len_sheetName >= 31: sheetName = sheetName[0:30]

    # Remove charaters from sheetName equal to the number of characters in table_Num string, and add table_Num string to it.
    new_len = len(sheetName) - len_table_Num
    sheetName = sheetName[0:new_len] + table_Num
    return sheetName


def getCellsIndices(all_cols, selected_cols, lastRow):
    """
    This function returns the selected columns equivalent excel cell range along row eg: AA3:AA30
    @param all_cols lsit of all columns in Table.
    @param selected_cols list of selected columns.
    @param lastRow  last row index in Table.
    @return list of cells indices
    """
    cells_indices = []
    for idx, col in enumerate(all_cols):
        if col in selected_cols:
            col_label = getExcelLabel(idx)
            firstCell = col_label + '3'
            lastCell  = col_label + lastRow
            cells_range = firstCell + ':' + lastCell  # ---> AA3:AA30
            cells_indices.append(cells_range)
    return cells_indices

def getgroupedCells(cols_lst):
    """
    This function returns the selected columns equivalent excel cell range along columns
    eg: STATS_0 range from E1:G1
    The output of this function is passed to Worksheet.set_column() function in main.py file
    @param cols_lst list of columns in Table
    @return list of selected columns cellsRange
    """
    cellsRange_lst = []
    lastCol = len(cols_lst)
    groupedCols_idx = []
    groupedCols = re.findall('(?:STATS_|HIST_|LIMIT_|SAMPLES_)[0-9]|SETTINGS', str(cols_lst))
    for idx, col in enumerate(cols_lst):
        if col in groupedCols:
            groupedCols_idx.append(idx)
    groupedCols_idx.append(lastCol)

    # Convert columns indcies to excel columns labels
    for i in range(len(groupedCols)):
        g1 = getExcelLabel(groupedCols_idx[i]+1)
        g2 = getExcelLabel(groupedCols_idx[i+1] - 1)
        cellsRange = g1 +':'+g2
        cellsRange_lst.append(cellsRange)
    return cellsRange_lst

# In future if user want to give multiple groups in config file.
# STATS_0 formulas can be dynamical build using tis approach.

def Mean_A(groups):

    cols = ['[@[Mean_'+str(x)+']]' for x in range(1,groups+1)]  # for groups = 2 ---> ['[@[Mean_1]]', '[@[Mean_2]]', '[@[Mean_3]]']
    mean_cols = ','.join(cols)                                                 # ---> '[@[Mean_1]],[@[Mean_2]],[@[Mean_3]]'
    formula = '=AVERAGE('+mean_cols+')'                                        # ---> '=AVERAGE([@[Mean_1]],[@[Mean_2]],[@[Mean_3]])'
    return formula


# idx = Table number
def getExcelfile(finalDF, groups, idx):
    """
    This function take Dataframe as argument and generate the parameters for worksheet.add_table(table_labels, options) as:
        - options = {'data': DATA, 'columns': HEADER}
        - table_labels = 'B3:F7'

    @param finalDF It is final merged dataframe.
    @param groups number of groups specified in Configuration file.
    @param idx Table number
    @return  table_range, options, cpkCells_lst
    """

# Step 2: Convert transformed DataFrame into excel table.
#(a) Preparing Data ( by converting finalDF in to list of list as DATA) and Header parameters for 'worksheet.add_table':

    """
    example:
    options = {'data': DATA, 'columns': [{'header': 'Product'},
                                         {'header': 'Quarter 1'},
                                         {'header': 'Quarter 2'},
                                         {'header': 'Year', 'formula': '=SUM(Table10[@[Quarter 1]:[Quarter 2]]), 'format': format1'}]}
    worksheet.add_table('B3:F7', options)
    """
    # DATA      -->  list of lists.
    # columns   -->  list of dicts.

    # The following two will be  final commands:

    # options = {'data': DATA, 'columns': HEADER}
    # worksheet.add_table(table_labels, options)
    # Variables to specify : DATA, HEADER, table_labels

    finalDF.fillna('', inplace=True)
    # Get Data by converting each row in dataframe as list and combine them into list of lists. eg: print(DATA[0]).

    DATA = finalDF.values
    col_names = finalDF.columns.tolist()
    # print(col_names)
    HEADER = [{'header': x} for x in col_names]

    # initalizing std_lst that will contain dict items for 'write_array_formula()' method:

    std_lst = []                                          # std_lst = [{'Y3:Y100':formula_1},{'BE3:BE100':formula_2}]
    std_formula = []                                      # std_formula = [Std_1_formula, Std_2_formula]
                                                          # stdCells_Indices = ['Y3:Y100', 'BE3:BE100']


#(b) Creating excel table(Table1) from DATA and Header.
    # Update Header formulas
    for i in range(groups):
        N = str(i+1)
        Type   =  'Type_'+ N
        Factor =  'Factor_'+ N
        U1     =  'U1_'+ N
        L1     =  'L1_' + N
        U2     =  'U2_' + N
        L2     =  'L2_' + N
        U      =  'U_'+ N
        L      =  'L_'+ N
        Range  =  'Range_'+ N
        Fails  =  'FailsCounts_'+ N
        Min    =  'Min_'+ N
        Max    =  'Max_'+ N
        Mean   =  'Mean_'+ N
        Std    =  'Std_'+ N
        Cp     =  'Cp_'+ N
        Cpk    =  'Cpk_'+ N

        # (1) Specify columns samples columns range to perform calculations.

        col_list = re.findall('[S]{1}[0-9]{1,}[_' + N + ']{2,}', str(col_names))
        start = col_list[0]
        end = col_list[-1]
        col_range = 'Table' + idx + '[@[' + start + ']:[' + end + ']]'  # ---> eg: Table1[@[S0_1]:[S13_1]]

        # (2) Specify the statistic functions:
        cfg_formulas =  [{'label': Type,         'formula': '=1'},
                         {'label': Factor,       'formula': '=1'},
                         {'label': U,            'formula': '=IF([@['+Factor+']]>0,IF([@['+Type+']]=1,IF([@['+U1+']]>0,[@['+U1+']]*[@['+Factor+']],2*[@['+U1+']]-[@['+U1+']]*[@['+Factor+']]),IF([@['+U2+']]>0,[@['+U2+']]*[@['+Factor+']],2*[@['+U2+']]-[@['+U2+']]*[@['+Factor+']])),0)'},
                         {'label': L,            'formula': '=IF([@['+Factor+']]>0,IF([@['+Type+']]=1,IF([@['+L1+']]<0,[@['+L1+']]*[@['+Factor+']],2*[@['+L1+']]-[@['+L1+']]*[@['+Factor+']]),IF([@['+L2+']]<0,[@['+L2+']]*[@['+Factor+']],2*[@['+L2+']]-[@['+L2+']]*[@['+Factor+']])),0)'},
                         {'label': Range,        'formula': '=[@['+U+']]-[@['+L+']]'},
                         {'label': Fails,        'formula': 'COUNTIF'},    #  =COUNTIF(Table1[@[S0_1]:[S13_1]],">"&[@[U_1]])+COUNTIF(Table1[@[S0_1]:[S13_1]],"<"&[@[L_1]])
                         {'label': Min,          'formula': '=_xlfn.MINIFS('+col_range+','+col_range+',">="&[@['+L+']],'+col_range+',"<="&[@['+U+']])'},
                         {'label': Max,          'formula': '=_xlfn.MAXIFS('+col_range+','+col_range+',">="&[@['+L+']],'+col_range+',"<="&[@['+U+']])'},
                         {'label': Mean,         'formula': '=IF(AND([@['+U+']]=0,[@['+L+']]=0),AVERAGE('+col_range+'),AVERAGEIFS('+col_range+','+col_range+',">="&[@['+L+']],'+col_range+',"<="&[@['+U+']]))'},
                         {'label': Std,          'formula': '=_xlfn.STDEV.S((IF([@['+L+']]=0,TRUE,'+col_range+'>=[@['+L+']]))*(IF([@['+U+']]=0,TRUE,'+col_range+'<=[@['+U+']]))*('+col_range+'))'},
                         {'label': Cp,           'formula': '=IF([@['+Std+']]>0,ROUND([@['+Range+']]/(6*[@['+Std+']]),2),0)'},
                         {'label': Cpk,          'formula': '=IF([@['+Std+']]>0,ROUND(MIN(ABS([@['+U+']]-[@['+Mean+']])/(3*[@['+Std+']]),ABS([@['+Mean+']]-[@['+L+']])/(3*[@['+Std+']])),2),0)'}
                         ]


        #def getStats_formula(key, col_range):
        # Outdated
        #    return '=' + key + '(' + col_range + ')'  # ---> eg:   =MAX(Table1[@[S0_1]:[S13_1]])


        # (3) Updating the HEADER list with formulas from cfg_formulas:
        for header in HEADER:
            for obj in cfg_formulas:
                if header['header'] == obj['label']:
                    if obj['label'] == Type:
                        formula = obj['formula']
                    elif obj['label'] == Factor:
                        formula = obj['formula']
                    elif obj['label'] == L:
                        formula = obj['formula']
                    elif obj['label'] == U:
                        formula = obj['formula']
                    elif obj['label'] == Range:
                        formula = obj['formula']
                    elif obj['label'] == Fails:
                        formula = '=' + obj['formula'] + '(' + col_range + ',">"&[@['+U+']])+' + obj['formula'] + '(' + col_range + ',"<"&[@['+L+']])'
                    elif obj['label'] == Min:
                        formula = obj['formula']
                    elif obj['label'] == Max:
                        formula = obj['formula']
                    elif obj['label'] == Mean:
                        formula = obj['formula']
                    elif obj['label'] == Std:
                        std_formula.append(obj['formula'])
                        formula = obj['formula']
                    elif obj['label'] == Cp:
                        formula = obj['formula']
                    elif obj['label'] == Cpk:
                        formula = obj['formula']
                    header.update({'formula': formula})

    # Updating STATS_0 columns formulas in HEADER:
    # If there are two groups or more than two groups in config file, then there will be STATS_0 columns in Header.
    # STATS_0 = ['Mean_A', 'Mean_R', 'Stdev_R', 'Cpk_R']
    if groups == 2:
        STATS_0_formulas = [{'label': 'Mean_A',   'formula': '=[@[Mean_1]]-[@[Mean_2]]'},
                            {'label': 'Mean_R',   'formula': '=ABS(([@[Mean_1]]-[@[Mean_2]])/([@[Mean_1]])*100)'},
                            {'label': 'Stdev_R',  'formula': '=ABS(([@[Std_1]]-[@[Std_2]])/([@[Std_1]])*100)'},
                            {'label': 'Cpk_R',    'formula': '=ABS(([@[Cpk_1]]-[@[Cpk_2]])/[@[Cpk_1]])'}]

        for header in HEADER:
            for obj in STATS_0_formulas:
                if header['header'] == obj['label']:
                    stats0_formula = obj['formula']
                    header.update({'formula': stats0_formula})

    # (4) Define a table range by converting column index to excel column labels:
    # excel_col_label = letter+Number eg: A20
    # Notice that xlsxwriter.utility.xl_col_to_name(col_number) uses zero-indexing.

    first_col_index = 0
    last_col_index = len(HEADER) - 1
    rows, cols = finalDF.shape

    # For Table: firstRow and lastRow in excel Worksheet

    firstRow = '2'
    lastRow  = str(rows+2)
    first_box_label = getExcelLabel(first_col_index) + firstRow           # ---->  eg: A3
    last_box_label  = getExcelLabel(last_col_index) + lastRow             # ---->  eg: L85
    table_range    = first_box_label + ':' + last_box_label              # --->   eg: A3:L85

    options = {'data': DATA, 'columns': HEADER}

    # Get list of Cpk columns indices equivalent to excel labels eg:  ['AA3:AA30', 'BZ3:BZ30']
    cpk_cols = re.findall('Cpk_[1-9]{1,}', str(col_names))
    cpkCells_lst  = getCellsIndices(col_names, cpk_cols, lastRow)

    return table_range, options, cpkCells_lst