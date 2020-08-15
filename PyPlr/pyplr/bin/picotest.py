# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 10:37:03 2020

@author: engs2242
"""


#from picosdk.library import Library


from picosdk.discover import find_all_units

scopes = find_all_units()

for scope in scopes:
    print(scope.info)
    scope.close()