"""
@file regex.py
This module defines a function to generate a regular expression based on configuration file.

"""
import sys

def Transition_len(Filter, Type):
    try:
        length = len(Filter['TRANSITION'][Type])
    except:
        length = len(Filter['TRANSITION'])

    return length

def getRegex(Filter):
    """
    This funtion generates the regular expression based on configuration file
    @param Filter Dictionary object.
    @return Regular expression.
    """
    #ProductName = '.+' if False else Filter['PRODUCT_NAME']
    Variant     = '[A-Za-z]+' if len(Filter['VARIANT']) == 0 else '(' + '|'.join(Filter['VARIANT']) + ')'
    Hw          = '[A-Za-z]+' if len(Filter['HW']) == 0 else '(' + '|'.join(Filter['HW']) + ')'
    Task        = '[A-Za-z]+' if len(Filter['TASK']) == 0 else '(' + '|'.join(Filter['TASK']) + ')'
    Type1       = '[A-Za-z]+' if Transition_len(Filter, 'Type1') == 0 else '(' + '|'.join(Filter['TRANSITION']['Type1']) + ')'
    Type2       = '[A-Za-z]+' if Transition_len(Filter, 'Type2') == 0 else '(' + '|'.join(Filter['TRANSITION']['Type2']) + ')'
    Test        = '(?:[A-Za-z]+)(?:.+)?)?.' if len(Filter['TEST']) == 0 else '(' + '|'.join(Filter['TEST']) + ')).'
    Year        = '[0-9]{4}' if len(Filter['YEAR']) == 0 else '(' + '|'.join(Filter['YEAR']) + ')'
    Month       = '[0-9]{2}' if len(Filter['MONTH']) == 0 else '(' + '|'.join(Filter['MONTH']) + ')'


    VARIANT    = '(?P<Variant>' + Variant + ').'
    HW         = '(?P<HW>' + Hw + ').'
    TASK       = '(?P<Task>' + Task + ').'
    TRANSITION = '(?P<Transition>(?P<Type1>' + Type1 + ').(?P<Type2>' + Type2 + ')).'
    TEST       = '?(?P<Test>' + Test
    TIMESTAMP  = '(?:(?P<Timestamp>(?P<Years>' + Year + ').(?P<Months>' + Month + ').(?P<Days>[0-9]{2}).(?P<Time>[a-z0-9]{9}))).'
    ID         = '(?P<ID>([a-z0-9]+)).log'

    regex = VARIANT + HW + TASK + TRANSITION + TEST + TIMESTAMP + ID

    return regex


def logfilenames():
    regex = '(?P<Variant>[A-Za-z]+).(?P<HW>[A-Za-z]+).(?P<Task>.+).(?P<Transition>(?P<Type1>(Diagnostic|Calibration|Reference|Verification|Misc)).(?P<Type2>(AtSpeed|Connect|DefaultData|Factory|Init|Regular|Reset|TroubleShooting))).?(?P<Test>(?:[A-Za-z]+)(?:.+)?)?.(?:(?P<Timestamp>(?P<Date>[0-9.]{10}).(?P<Time>[a-z0-9]{9}))).(?P<Undefined>([a-z0-9]+)).log'
    return regex

