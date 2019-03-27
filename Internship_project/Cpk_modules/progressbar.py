"""
@file progressbar.py
This module defines function to print a Progress Bar on console during program execution.
The Bar(kwargs**) is called only in main.py file.
"""


import sys
import math


def Bar(i=0, total=1, text= '', size= 10):
    """
    This function print the progress bar on console.
    @param i integer value. Use update the bar.
    @param total integer value. Use update the bar.
    @param text Its optional argument. If a string is passed it will show up at the right side of progress bar.
    @param size it is the size of bar. The default value is 50 characters.
    @return progress bar
    """
    percent = float(i) / float(total)
    sys.stdout.write( "\r" + str(int(percent*100)).rjust(3, ' ') +"%"  +' [' + '='*math.ceil(percent*size) +' '  *math.floor((1-percent)*size)+']'  + ' 100%' + ' ' + text.ljust(135))
    sys.stdout.flush()



# factor: len(dirs), iteration over dirctories
# This function is outdated.
def Bar2(factor= 1.0, iteration=0.0, size=50, text = '' ):
    percent = float(iteration)/ float(factor)
    sys.stdout.write("\r" + str(int(percent * 100)).rjust(3, ' ') + "%" + ' [' + '=' * math.ceil(percent * size) + ' ' * math.floor((1 - percent) * size) + ']' + ' 100%' + ' ' + text)

"""
# Usage Example:
total = 1500
print('getting files names....')
for i in range(total):
    Bar(i, total)
"""
