import numpy as np
import pandas as pd
import matplotlib
import sys, os
from urllib.error import URLError, HTTPError
from urllib.request import urlopen
import json
import EIAgov

#if __name__ == '__main__':
tok = 'ba1be1ff6d258c3b793079d6fbc47131'
stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

def collectEIAdata(dfName, seriesNameStart, seriesNameEnd, outfileName):
	for n in stateCodes:
		print(n)
		ser = [seriesNameStart+n+seriesNameEnd]
		print(ser)
		data = EIAgov.EIAgov(tok, ser)
		D = data.GetData()

		if 'Date' in ser:
			dfName[n] = D[ser]
		else:
			dfName['Date'] = D.Date
			dfName[n] = D[ser]

	dfName.to_csv(outfileName)

allIndEnergy = pd.DataFrame()
#collectEIAdata(allIndEnergy, 'SEDS.TEICB.', '.A', 'EIA_IndEnergy.csv')# billion btu

allIndElec = pd.DataFrame()
#collectEIAdata(allIndElec,'ELEC.SALES.', '-IND.M', 'EIA_IndElec.csv') # million kWh

allIndNG = pd.DataFrame()
collectEIAdata(allIndNG, 'NG.N3035', '2.M', 'EIA_IndNG.csv') # million cubic feet

allIndElecLosses = pd.DataFrame()
collectEIAdata(allIndElecLosses, 'SEDS.LOICB.', '.A', 'EIA_IndElecLosses.csv') #billion btu

allIndNGA = pd.DataFrame()
collectEIAdata(allIndNGA, 'SEDS.NGICP.', '.A', 'EIA_IndNGA.csv') # million cubic feet

allIndElecA = pd.DataFrame()
collectEIAdata(allIndElecA, 'SEDS.ESICP.', '.A', 'EIA_IndElecA.csv') # million kWh

stateCodes.remove('US')
stateCodes.remove('CT')
stateCodes.remove('DC')
stateCodes.remove('GA')
stateCodes.remove('HI')
stateCodes.remove('IA')
stateCodes.remove('ME')
stateCodes.remove('MA')
stateCodes.remove('NJ')
stateCodes.remove('SC')
stateCodes.remove('VT')
stateCodes.remove('MN')
stateCodes.remove('NH')
stateCodes.remove('WI')
stateCodes.remove('DE')
stateCodes.remove('ID')
stateCodes.remove('RI')
stateCodes.remove('WA')
leaseNGA = pd.DataFrame()
plantNGA = pd.DataFrame()
#collectEIAdata(leaseNGA, 'NG.NA1840_S', '_2.A', 'EIA_LeasePlantNG.csv') # million cubic feet

stateCodes = ['AL', 'AK', 'AR', 'CA', 'CO', 'FL', 'IL', 'KS', 'KY', 'LA', 'MI', 'MS', 'MT', 'NE', 'NM',  'ND', 'OH', 'OK', 'PA', 'TN', 'TX', 'UT', 'WV', 'WY']
#collectEIAdata(plantNGA, 'NG.NA1850_S', '_2.A', 'EIA_PlantNG.csv')

def collectCoalData():
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
	stateCodes.remove('CT')
	stateCodes.remove('DC')
	stateCodes.remove('DE')
	stateCodes.remove('NH')
	stateCodes.remove('NJ')
	stateCodes.remove('RI')
	stateCodes.remove('VT')

	allIndCoal = pd.DataFrame()

	for n in stateCodes:
		indCoal1 = ['COAL.CONS_TOT.'+n+'-10.Q']
		data = EIAgov.EIAgov(tok, indCoal1)
		C1 = data.GetData()
		if 'Date' in allIndCoal:
			allIndCoal[n] = C1[indCoal1]
		else:
			allIndCoal['Date'] = C1.Date
			allIndCoal[n] = C1[indCoal1]

	allIndCoal.to_csv('EIA_IndCoal1.csv')

	cokeStates = ['US', 'AL', 'IL', 'IN', 'MI', 'NY', 'OH', 'PA', 'VA', 'WV']
	for n in cokeStates:
		indCoal2 = ['COAL.CONS_TOT.'+n+'-9.Q']
		data = EIAgov.EIAgov(tok, indCoal2)
		C2 = data.GetData()
		x = allIndCoal[n].values + C2[indCoal2].values[0]
		allIndCoal[n] = x
		
	allIndCoal.to_csv('EIA_IndCoal2.csv')
#collectCoalData()

def checkMonthvsYear(monthlyData, yearlyData, *args):
	m = pd.read_csv(monthlyData)
	m.Date = pd.to_datetime(m.Date, format = '%Y%m')
	m = m.sort_values(by = 'Date')
	m = m.set_index('Date')
	m = m.drop('Unnamed: 0', axis = 1)

	y = pd.read_csv(yearlyData)
	y.Date = pd.to_datetime(y.Date, format = '%Y')
	y = y.sort_values(by = 'Date') #
	y = y.set_index('Date')
	y = y.drop('Unnamed: 0', axis = 1)

	for ar in args:
		print(ar)
		z = pd.read_csv(ar)
		z.Date = pd.to_datetime(z.Date, format = '%Y')
		z = z.sort_values(by = 'Date')
		z = z.set_index('Date')
		z = z.drop('Unnamed: 0', axis = 1)
		a = np.intersect1d(np.asarray(z.index.year.unique()), np.asarray(y.index.year.unique()))
		y = y.loc[str(min(a))+'-01-01':str(max(a))+'-01-01']
		z = z.loc[str(min(a))+'-01-01':str(max(a))+'-01-01']
		for c in z.columns:
			y[c] = y[c] - z[c]
			
	a = np.intersect1d(np.asarray(m.index.year.unique()), np.asarray(y.index.year.unique()))
	t = 0
	for n in a:
		mt = m.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
		for c in m.columns:
			if np.absolute((mt[c]-y.loc[str(n)][c].values)/y.loc[str(n)][c].values)>0.05:
				if c != 'US':
					print(n, c, mt[c], y.loc[str(n)][c].values)
					t = t+1
	print(t, 'done!')	

#checkMonthvsYear('EIA_IndElec.csv', 'EIA_IndElecA.csv')
#checkMonthvsYear('EIA_IndNG.csv', 'EIA_IndNGA.csv') # lots of stuff doesn't match 
#checkMonthvsYear('EIA_IndNG.csv', 'EIA_IndNGA.csv', 'EIA_LeasePlantNG.csv') # lots of stuff doesn't match 
#checkMonthvsYear('EIA_IndNG.csv', 'EIA_IndNGA.csv', 'EIA_LeasePlantNG.csv', 'EIA_PlantNG.csv') # lots of stuff doesn't match 

