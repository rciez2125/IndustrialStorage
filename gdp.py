import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import re
from datetime import date
import numpy as np

def getStateLevelData(startYr, endYr):
	gdp = pd.read_csv('Data/SAGDP9N__ALL_AREAS_1997_2019.csv')
	gdp = gdp.iloc[:-4]
	states = gdp.GeoName.unique()
	states = states[:-8]
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

	seriesNames = 	['CAPUTLG321S', 	'CAPUTLG327S', 	'CAPUTLG331S', 	'CAPUTLG332S', 	'CAPUTLG333S', 	'CAPUTLHITEK2S','CAPUTLG335S', 	'CAPUTLG3361T3S', 	'CAPUTLG3364T9S', 	'CAPUTLG337S', 	'CAPUTLG339S', 	'CAPUTLG311A2S', 	'CAPUTLG313A4S', 	'CAPUTLG315A6S', 	'CAPUTLG322S', 		'CAPUTLG323S', 	'CAPUTLG324S', 	'CAPUTLG325S', 	'CAPUTLG326S', 	'CAPUTLG21S', 	'CAPUTLG2211A2S']
	seriesNames2 = 	['IPG321S', 		'IPG327S', 		'IPG331S', 		'IPG332S', 		'IPG333S', 		'IPHITEK2S', 	'IPG335S', 		'IPG3361T3S', 		'IPG3364T9S', 		'IPG337S', 		'IPG339S',		'IPG311A2S', 		'IPG313A4S', 		'IPG315A6S', 		'IPG322S', 			'IPG323S', 		'IPG324S', 		'IPG325S', 		'IPG326S', 		'IPMINE', 		'IPG2211A2N']
	NAICS = 		['321', 			'327', 			'331', 			'332', 			'333', 			'334', 			'335', 			'3361-3363', 		'3364-3369', 		'337', 			'339', 			'311-312', 			'313-314', 			'315-316', 			'322', 				'323', 			'324', 			'325', 			'326', 			'21', 			'22']

	print(len(seriesNames), len(seriesNames2), len(NAICS))

	uData = pd.read_csv('Data/Fred/'+seriesNames[0]+'.csv')
	uData.DATE = pd.to_datetime(uData.DATE, format = '%Y-%m-%d')
	uData = uData.set_index('DATE')

	iData = pd.read_csv('Data/Fred/IndProduction/'+seriesNames2[0]+'.csv')
	iData.DATE = pd.to_datetime(iData.DATE, format = '%Y-%m-%d')
	iData = iData.set_index('DATE')

	x = uData.loc[startYr+'-01-01':endYr+'-12-01']

	stateCapUtilization = pd.DataFrame(index = x.index)
	stateIndustrialProduction = pd.DataFrame(index = x.index)
	for s in range(len(states)):
		capUt = []
		indProd = []
		GDP = gdp[gdp.GeoName == states[s]] 
		for y in np.linspace(int(startYr), int(endYr), int(endYr)-int(startYr)+1): #(1997, 2019, 23):
			for q in range(12):
				gdpNum = 0
				d = 0
				ip = 0
				sampleDate = str(int(y))+'-'+str(q+1)+'-01'
				for n in range(len(NAICS)):
					g = float(GDP[GDP.IndustryClassification == NAICS[n]][sampleDate[0:4]].values)*1000000
					
					uData = pd.read_csv('Data/Fred/'+seriesNames[n]+'.csv')
					uData.DATE = pd.to_datetime(uData.DATE, format = '%Y-%m-%d')
					uData = uData.set_index('DATE')

					print(seriesNames2[n])
					iData = pd.read_csv('Data/Fred/IndProduction/'+ seriesNames2[n]+'.csv')
					iData.DATE = pd.to_datetime(iData.DATE, format = '%Y-%m-%d')
					iData = iData.set_index('DATE')

					gdpNum = gdpNum + g
					d = d + g/(uData.loc[sampleDate].values)
					print(iData.loc[sampleDate])
					ip = ip + g/(iData.loc[sampleDate].values)


				capUt = np.append(capUt, gdpNum/d)
				indProd = np.append(indProd, gdpNum/ip)

		stateCapUtilization[stateCodes[s]] = capUt
		stateIndustrialProduction[stateCodes[s]] = indProd
		del(capUt)
		del(indProd)

	stateCapUtilization.to_csv('StateCapacityUtilization.csv')
	stateIndustrialProduction.to_csv('stateIndustrialProductionIndex.csv')

getStateLevelData('1997', '2019') #data for 1997 - 2019

