import numpy as np
import pandas as pd
import matplotlib
import sys, os
from urllib.error import URLError, HTTPError
from urllib.request import urlopen
import json
import EIAgov
from datetime import datetime 
import json

f = open('eiaToken.json') # points to json file, need an api key: https://www.eia.gov/opendata/
tok = json.load(f)['token']

def collectEIAdata(dfName, seriesNameStart, seriesNameEnd, outfileName, states):
	for n in states:
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

def getIndData():
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

	allIndEnergy = pd.DataFrame()
	collectEIAdata(allIndEnergy, 'SEDS.TNICB.', '.A', 'Data/EIA_IndEnergy.csv', stateCodes) #billion btu, exlcuding electricity system losses

	allIndElec = pd.DataFrame()
	collectEIAdata(allIndElec,'ELEC.SALES.', '-IND.M', 'Data/EIA_IndElec.csv', stateCodes) # million kWh

	allIndNG = pd.DataFrame()
	collectEIAdata(allIndNG, 'NG.N3035', '2.M', 'Data/EIA_IndNG.csv', stateCodes) # million cubic feet

	allIndElecLosses = pd.DataFrame()
	collectEIAdata(allIndElecLosses, 'SEDS.LOICB.', '.A', 'Data/EIA_IndElecLosses.csv', stateCodes) #billion btu

	allIndNGA = pd.DataFrame()
	collectEIAdata(allIndNGA, 'SEDS.NGICP.', '.A', 'Data/EIA_IndNGA.csv', stateCodes) # million cubic feet, annual data

	allIndNGAB = pd.DataFrame()
	collectEIAdata(allIndNGAB, 'SEDS.NGICB.','.A', 'Data/EIA_IndNGAB.csv', stateCodes) #billion btu, annual data 

	allIndElecA = pd.DataFrame()
	collectEIAdata(allIndElecA, 'SEDS.ESICP.', '.A', 'Data/EIA_IndElecA.csv', stateCodes) # million kWh, annual data
getIndData()

def getOverallElecData():
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
	allElec = pd.DataFrame()
	collectEIAdata(allElec, 'ELEC.GEN.ALL-','-99.M', 'Data/EIA_allElec.csv', stateCodes)
getOverallElecData()

def getStateElecSalesAll(): 
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
	allElecMonth = pd.DataFrame()
	collectEIAdata(allElecMonth, 'ELEC.SALES.', '-ALL.M', 'Data/EIA_MonthlyElecSales.csv', stateCodes)

	allEnergyMonthly = pd.DataFrame()
#getStateElecSalesAll()

def getNGData():
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
	leasePlantDrop = ['US', 'CT', 'DC', 'GA', 'HI', 'IA', 'ME', 'MA', 'NJ', 'NC', 'SC', 'VT', 'MN', 'NH', 'WI', 'DE', 'ID', 'RI', 'WA']
	leaseStates = [e for e in stateCodes if e not in leasePlantDrop]
	leaseNGA = pd.DataFrame()
	plantNGA = pd.DataFrame()
	collectEIAdata(leaseNGA, 'NG.NA1840_S', '_2.A', 'EIA_LeasePlantNG.csv', leaseStates) # million cubic feet

	plantStates = ['AL', 'AK', 'AR', 'CA', 'CO', 'FL', 'IL', 'KS', 'KY', 'LA', 'MI', 'MS', 'MT', 'NE', 'NM',  'ND', 'OH', 'OK', 'PA', 'TN', 'TX', 'UT', 'WV', 'WY']
	collectEIAdata(plantNGA, 'NG.NA1850_S', '_2.A', 'EIA_PlantNG.csv', plantStates)
getNGData()

def collectCoalData():
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
	coalDrop = ['CT', 'DC', 'DE', 'NH', 'NJ', 'RI', 'VT']
	coalStates = [e for e in stateCodes if e not in coalDrop]

	allIndCoal = pd.DataFrame()

	for n in coalStates:
		indCoal1 = ['COAL.CONS_TOT.'+n+'-10.Q']
		data = EIAgov.EIAgov(tok, indCoal1)
		C1 = data.GetData()
		if 'Date' in allIndCoal:
			allIndCoal[n] = C1[indCoal1]
		else:
			allIndCoal['Date'] = C1.Date
			allIndCoal[n] = C1[indCoal1]

	allIndCoal.to_csv('Data/EIA_IndCoal1.csv')

	cokeStates = ['US', 'AL', 'IL', 'IN', 'MI', 'NY', 'OH', 'PA', 'VA', 'WV']
	for n in cokeStates:
		indCoal2 = ['COAL.CONS_TOT.'+n+'-9.Q']
		data = EIAgov.EIAgov(tok, indCoal2)
		C2 = data.GetData()
		x = allIndCoal[n].values + C2[indCoal2].values[0]
		allIndCoal[n] = x
		
	allIndCoal.to_csv('Data/EIA_IndCoal2.csv')
collectCoalData()

def getNationalMonthlyData():
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
	naphtha = pd.DataFrame()
	collectEIAdata(naphtha, 'SEDS.FNICP.', '.A', 'Data/EIA_StateNaphtha.csv', stateCodes) # thousand barrels 

	monthlyNaphtha =pd.DataFrame()
	data = EIAgov.EIAgov(tok, ['PET.MNFUPUS1.M'])
	monthlyNaphtha = data.GetData() #thousand barrels
	monthlyNaphtha.Date = pd.to_datetime(monthlyNaphtha.Date, format = '%Y%m')
	monthlyNaphtha = monthlyNaphtha.sort_values(by = 'Date')
	monthlyNaphtha = monthlyNaphtha.set_index('Date')
	monthlyNaphtha = monthlyNaphtha.rename(columns = {"PET.MNFUPUS1.M": 'US'})
	monthlyNaphtha.to_csv('Data/monthlyNaphtha.csv')

	data = EIAgov.EIAgov(tok, ['PET.MNFUPUS1.A'])
	yearlyNaphtha = data.GetData() #thousand barrels
	yearlyNaphtha.Date = pd.to_datetime(yearlyNaphtha.Date, format = '%Y')
	yearlyNaphtha = yearlyNaphtha.sort_values(by = 'Date')
	yearlyNaphtha = yearlyNaphtha.set_index('Date')
	yearlyNaphtha = yearlyNaphtha.rename(columns = {"PET.MNFUPUS1.A": 'US'})
	yearlyNaphtha.to_csv('Data/yearlyNaphtha.csv')

	ethane = pd.DataFrame()
	collectEIAdata(ethane, 'SEDS.EQICP.', '.A', 'Data/EIA_StateEthane.csv', stateCodes) # thousand barrels 
	monthlyEthane = pd.read_excel('Data/M_EPLLEA_VPP_NUS_MBBLm.xls', sheet_name = 'Data 1', skiprows = 2, header = 0) # thousand barrels 
	monthlyEthane.Date = pd.to_datetime(monthlyEthane.Date, format = '%Y%m')
	monthlyEthane = monthlyEthane.sort_values(by = 'Date')
	monthlyEthane.Date = monthlyEthane.Date.apply(lambda dt: dt.replace(day=1))
	monthlyEthane = monthlyEthane.set_index('Date')
	monthlyEthane = monthlyEthane.rename(columns = {"U.S. Product Supplied of Ethane (Thousand Barrels)": 'US'})
	monthlyEthane.to_csv('Data/monthlyEthane.csv')

	propane = pd.DataFrame()
	collectEIAdata(propane, 'SEDS.PQICB.','.A', 'Data/EIA_StatePropane.csv', stateCodes)
	data = EIAgov.EIAgov(tok, ['TOTAL.PQICBUS.M'])
	monthlyPropane = data.GetData()
	monthlyPropane.Date = pd.to_datetime(monthlyPropane.Date, format = '%Y%m')
	monthlyPropane = monthlyPropane.sort_values(by = 'Date')
	monthlyPropane = monthlyPropane.set_index('Date')
	monthlyPropane = monthlyPropane * 1000 # convert from trillion to billion btu
	monthlyPropane = monthlyPropane.rename(columns = {'TOTAL.PQICBUS.M': 'US'})
	monthlyPropane.to_csv('Data/monthlyPropane.csv')
	
	propylene = pd.DataFrame()
	collectEIAdata(propylene, 'SEDS.PYICB.', '.A', 'Data/EIA_StatePropylene.csv', stateCodes)
	data = EIAgov.EIAgov(tok, ['TOTAL.PYICBUS.M'])
	monthlyPropylene = data.GetData()
	monthlyPropylene.Date = pd.to_datetime(monthlyPropylene.Date, format = '%Y%m')
	monthlyPropylene = monthlyPropylene.sort_values(by = 'Date')
	monthlyPropylene = monthlyPropylene.set_index('Date')
	monthlyPropylene = monthlyPropylene*1000 #convert from trillion to billion btu
	monthlyPropylene = monthlyPropylene.rename(columns = {'TOTAL.PYICBUS.M': 'US'})
	monthlyPropylene.to_csv('Data/monthlyPropylene.csv')

	stillGas = pd.DataFrame()
	collectEIAdata(stillGas, 'SEDS.SGICP.', '.A', 'Data/EIA_StateStillGas.csv', stateCodes)
	data = EIAgov.EIAgov(tok, ['PET.MSGUPUS1.M'])
	monthlyStillGas = data.GetData()
	monthlyStillGas.Date = pd.to_datetime(monthlyStillGas.Date, format = '%Y%m')
	monthlyStillGas = monthlyStillGas.sort_values(by = 'Date')
	monthlyStillGas = monthlyStillGas.set_index('Date')
	monthlyStillGas = monthlyStillGas.rename(columns = {'PET.MSGUPUS1.M': 'US'})
	monthlyStillGas.to_csv('Data/monthlyStillGas.csv')

	asphalt = pd.DataFrame()
	collectEIAdata(asphalt, 'SEDS.ARICB.', '.A', 'Data/EIA_StateAsphalt.csv', stateCodes)
	data = EIAgov.EIAgov(tok, ['TOTAL.ARNFBUS.M'])
	monthlyAsphalt = data.GetData()
	monthlyAsphalt.Date = pd.to_datetime(monthlyAsphalt.Date, format = '%Y%m')
	monthlyAsphalt = monthlyAsphalt.sort_values(by = 'Date')
	monthlyAsphalt = monthlyAsphalt.set_index('Date')
	monthlyAsphalt = monthlyAsphalt.rename(columns = {'TOTAL.ARNFBUS.M': 'US'})
	monthlyAsphalt = monthlyAsphalt*1000000 #convert from quad to billion btu 
	monthlyAsphalt.to_csv('Data/monthlyAsphalt.csv')

	specialNap = pd.DataFrame()
	collectEIAdata(specialNap, 'SEDS.SNICB.', '.A', 'Data/EIA_StateSpecialNap.csv', stateCodes)
	data = EIAgov.EIAgov(tok, ['TOTAL.SNNFBUS.M'])
	monthlySpecialNap = data.GetData()
	monthlySpecialNap.Date = pd.to_datetime(monthlySpecialNap.Date, format = '%Y%m')
	monthlySpecialNap = monthlySpecialNap.sort_values(by = 'Date')
	monthlySpecialNap = monthlySpecialNap.set_index('Date')
	print(monthlySpecialNap.columns)
	monthlySpecialNap = monthlySpecialNap.rename(columns = {'TOTAL.SNNFBUS.M': 'US'})
	monthlySpecialNap = monthlySpecialNap*1000000 #convert from quad to billion btu 
	monthlySpecialNap.to_csv('Data/monthlySpecialNap.csv')

	miscPet = pd.DataFrame()
	collectEIAdata(miscPet, 'SEDS.MSICB.', '.A', 'Data/EIA_StateMiscPet.csv', stateCodes)
	data = EIAgov.EIAgov(tok, ['TOTAL.OTNFBUS.M'])
	monthlyMiscPet = data.GetData()
	monthlyMiscPet.Date = pd.to_datetime(monthlyMiscPet.Date, format = '%Y%m')
	monthlyMiscPet = monthlyMiscPet.sort_values(by = 'Date')
	monthlyMiscPet = monthlyMiscPet.set_index('Date')
	monthlyMiscPet = monthlyMiscPet.rename(columns = {'TOTAL.OTNFBUS.M': 'US'})
	monthlyMiscPet = monthlyMiscPet*1000000 #convert from quad to billion btu 
	monthlyMiscPet.to_csv('Data/monthlyMiscPet.csv')
getNationalMonthlyData()


