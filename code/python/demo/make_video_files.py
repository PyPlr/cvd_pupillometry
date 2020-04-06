# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from datetime import datetime
import pandas as pd
import json


def get_header(df, repeats=1):
    
    header_dict = {
            "version":"1",
            "model":"VEGA10",
            "channels":10,
            "spectracount":len(df),
            "transitionsCount":len(df),
            "fluxReference":0,
            "repeats":repeats
            }

    return header_dict

def get_metadata(df, creator='jtm'):
    
    meta_dict = {
            "creationTime":str(datetime.now()),
            "creator":creator
            }

    return meta_dict

def get_spectra(df):
    
    light_cols = df.columns[1:]
    return df[light_cols].values.tolist()

def get_transitions(df):
    
    list_of_dicts = []
    
    for index , row in df.iterrows():
        
        list_of_dicts.append({
            "spectrum":index,
            "power":100,
            "time":int(row['time']),
            "flags":0})
    
    return list_of_dicts

def make_video_file(input_csv_file, repeats=1):
    ''' 
    Reads in a CSV file with columns 'time' , 'primary-1'...'primary-10'
    and returns a json file compatible with spectratune lab device
    '''
    
    df = pd.read_csv(input_csv_file)
    
    d = {
        "header":get_header(df, repeats),
        "metadata":get_metadata(df),
        "spectra":get_spectra(df),
        "transitions":get_transitions(df)
        }
    
    with open(input_csv_file[:-4] + '.dsf', 'w') as outfile:
        json.dump(d, outfile)
        
    return json.dumps(d)

