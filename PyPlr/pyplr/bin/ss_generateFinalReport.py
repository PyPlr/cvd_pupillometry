import pandas
import sys
import os 

import numpy as np
df1 = pandas.read_csv(sys.argv[2] + 'correspondence_table.csv')
df1['Frame #']+1

df2 = pandas.read_csv(sys.argv[2] + '/exports/000/pupil_positions.csv')
pupildata = df2['diameter_3d'][df1['Frame #']+1]
pupildata_mask = df2['confidence'][df1['Frame #']+1]
pupildata = pupildata.reset_index(drop=True)
pupildata = pandas.DataFrame(np.where(np.asarray(pupildata)==0, np.nan, np.asarray(pupildata)))
pupildata = pupildata.rename(columns={0 : 'diameter_3d'})
pupildata.insert(1, 'confidence', np.asarray(pupildata_mask))
pupildata

import spectres

# Read calibration information
calPerWl = np.asarray(pandas.read_csv(os.path.dirname(os.path.realpath(__file__)) +'/oo_calibration.csv', header=-1))
sensorAreaCm2 = float(pandas.read_csv(os.path.dirname(os.path.realpath(__file__)) + '/oo_sensorArea.csv', header=-1).iloc[0, 0])

# Read in CMFs
cies026 = np.transpose(np.asarray(pandas.read_csv(os.path.dirname(os.path.realpath(__file__)) + '/cies026.csv', usecols=[1, 2, 3, 4, 5])))
#cie1931xyz2deg = 683*np.transpose(np.asarray(pandas.read_csv('code/lin2012xyz10e_1_7sf.csv', usecols=[1, 2, 3], header=-1)))
cie1931xyz2deg = 683*np.transpose(np.asarray(pandas.read_csv(os.path.dirname(os.path.realpath(__file__)) + '/cie1931xyz2.csv', header=-1)))

# Read dark calibration
darkcal = pandas.read_csv('darkcalibr_poly31_V2.txt', sep='\t', header=5, index_col=False)


# Create empty data frame
lightdata = pandas.DataFrame()
for afile in (df1["Original file"].str.split('.', expand=True)[0]+'.csv').iteritems():
    spechead = pandas.read_csv(sys.argv[1] + '/spectra/' + afile[1], nrows=4, header=-1)
    integrationTime = float(spechead.iloc[2,1])/(1000*1000)
    temperature = float(spechead.iloc[3,1])
    specdf = pandas.read_csv(sys.argv[1] + '/spectra/' + afile[1], header=4)
    
    x = temperature
    y = integrationTime*1000

    darkSpd = []
    for ii in range(0, darkcal.shape[0]):
        p00 = darkcal.iloc[ii, 3]
        p10 = darkcal.iloc[ii, 4]
        p01 = darkcal.iloc[ii, 5]
        p20 = darkcal.iloc[ii, 6]
        p11 = darkcal.iloc[ii, 7]
        p30 = darkcal.iloc[ii, 8]
        p21 = darkcal.iloc[ii, 9]
        darkSpd = np.append(darkSpd, p00 + p10*x + p01*y + p20*x*x + p11*x*y + p30*x*x*x + p21*x*x*y)

    # Remove poorly fitted pixels
    FIT_RMSE_THRESHOLD = 3.25
    darkSpd = np.where(darkcal.FIT_RMSE > FIT_RMSE_THRESHOLD, np.nan, darkSpd)
    SELECT_RMSE_THRESHOLD = 25.0
    darkSpd = np.where(darkcal.SELECT_RMSE > SELECT_RMSE_THRESHOLD, np.nan, darkSpd)
    intensitySpd = specdf['Intensity (counts)']
    
    # Also remove saturated spectra !? 
    if any(intensitySpd > 16379):
        intensitySpd = np.nan

    uJPerPixel = np.asarray(intensitySpd-darkSpd) * np.transpose(calPerWl)
    #uJPerPixel = np.asarray(specdf['Intensity (counts)']-specdf['Dark (counts)']) * np.transpose(calPerWl)
    NmPerPixel = np.median(np.diff(specdf['Wavelengths (nm)']))
    uJPerNm = uJPerPixel[0]/NmPerPixel
    uJPerCm2PerNm = uJPerNm/sensorAreaCm2
    uWPerCm2PerNm = uJPerCm2PerNm/integrationTime
    # Resample
    uWPerCm2PerNm = spectres.spectres(np.arange(380, 781), np.asarray(specdf["Wavelengths (nm)"]), uWPerCm2PerNm)
    uWPerCm2PerNm = np.where(uWPerCm2PerNm < 0, 0, uWPerCm2PerNm)
    WPerM2PerNm = uWPerCm2PerNm*0.01
    
    # Save calibrated spectrum
    outFile = afile[1].split('.')[0]+'_calibrated.csv'
    np.savetxt(sys.argv[1] + '/spectra/' + outFile, WPerM2PerNm)

    #WPerM2PerNm = np.transpose(eew)
    # Read in the CIE curves
    alphaopicIrradiance = np.dot(np.nan_to_num(cies026), np.nan_to_num(WPerM2PerNm)*1000)
    XYZ = np.dot(np.nan_to_num(cie1931xyz2deg), np.nan_to_num(WPerM2PerNm))
    xyz = XYZ/np.sum(XYZ)
    xyY = np.array([xyz[0], xyz[1], XYZ[1]])
    theVals = pandas.Series(np.append(xyY, alphaopicIrradiance))
    lightdata = lightdata.append(theVals, ignore_index=True)

# Rename light data
lightdata = lightdata.rename(columns={0 : 'CIE 1931 x', 1 : 'CIE 1931 y', 2 : 'CIE 1931 Y', 3 : 'SConeIrrad', 4 : 'MConeIrrad', 5 : 'LConeIrrad', 6 : 'RodIrrad', 7 : 'MelIrrad'})
df = pandas.concat([df1, pupildata, lightdata], axis=1)
df.to_csv(sys.argv[1] + '/results.csv')
print('>>> ANALYSIS COMPLETED!')
