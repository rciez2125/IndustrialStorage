import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import date
import matplotlib.ticker as ticker
#import ind_output as ind
import EIAgov
from scipy import stats
import json

f = open('eiaToken.json') # points to json file, need an api key: https://www.eia.gov/opendata/
tok = json.load(f)['token']

def collectEIAdataOil(dfName, seriesNameStart, seriesNameEnd, outfileName, states):
	for n in states:
		if n == 'ID': ser = ['PET.M_EPC0_FPF_SID_MBBLD.M'] # some states have weird file names
		elif n == 'MI': ser = ['PET.MCRFP_SMI_1.M']
		else: ser = [seriesNameStart+n+seriesNameEnd]
		data = EIAgov.EIAgov(tok, ser)
		D = data.GetData()
		if 'Date' in dfName: dfName[n] = D[ser]
		else:
			dfName['Date'] = D.Date
			dfName[n] = D[ser]
	dfName.to_csv(outfileName)

def getData():
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'FL', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MS', 'MO', 'MT', 'NE', 'NV', 'NM', 'NY', 'ND', 'OH', 'OK', 'PA', 'SD', 'TN', 'TX', 'UT', 'VA', 'WV', 'WY']
	oilProdData = pd.DataFrame()
	collectEIAdataOil(oilProdData, 'PET.MCRFP', '1.M', 'Data/EIA_CrudeProduction.csv', stateCodes) #thousand barrels per month --> convert to millions 
	allOil = pd.read_csv('Data/EIA_CrudeProduction.csv')
	allOil = allOil.drop(['Unnamed: 0'], axis = 1)
	allOil.Date = pd.to_datetime(allOil.Date, format = '%Y%m')
	allOil = allOil.sort_values(by = 'Date')
	allOil = allOil.set_index('Date') * 0.005698*1000 # convert from thousands of barrels to billion btu 
	allOil = allOil.loc['2000-01-01':'2019-12-01']

	tightOil = pd.read_csv('Data/US-tight-oil-production.csv') # this isn't in the api, need to have it downloaded from 
	tightOil = tightOil.drop(['Unnamed: 11', 'Unnamed: 12'], axis = 1)
	tightOil.Date = pd.to_datetime(tightOil.Date)
	tightOil = tightOil.sort_values(by = 'Date')
	tightOil = tightOil.set_index('Date')
	tightOil = tightOil.loc['2000-01-01':'2019-12-01']
	return allOil, tightOil

allOil, tightOil = getData()

# convert data from million barrels per day to just million barrels per month 
def convertToMillionBarrels():
	shortMos = [2, 4, 6, 9]
	longMos = list(range(1,13))
	longMos = [x for x in longMos if x not in shortMos]
	tightOil.loc[tightOil.index.month == shortMos[0]] = tightOil.loc[tightOil.index.month == shortMos[0]]*28
	for n in range(len(shortMos)-1):
		tightOil.loc[tightOil.index.month == shortMos[n+1]] = tightOil.loc[tightOil.index.month == shortMos[n+1]]*30
	for n in range(len(longMos)):
		tightOil.loc[tightOil.index.month == longMos[n]] = tightOil.loc[tightOil.index.month == longMos[n]]*31
	return(tightOil)
tightOil = convertToMillionBarrels()
tightOil = tightOil*0.005698*1000000 # convert from millions of barrels to billion Btu

# make a plot of tight oil vs total oil production 
def plotTightOil():
	plt.figure()
	labs = ['All US Oil'] + list(tightOil.columns)
	plt.plot(allOil.index, allOil.US, '-k')
	plt.stackplot(tightOil.index, [tightOil['Eagle Ford (TX) '], tightOil['Spraberry (TX Permian)'], tightOil['Bakken (ND & MT)'], 
		tightOil['Wolfcamp (TX & NM Permian)'], tightOil['Bonespring (TX & NM Permian)'], tightOil['Niobrara-Codell (CO & WY)'], 
		tightOil['Mississippian (OK)'], tightOil['Austin Chalk (LA & TX)'], tightOil['Woodford (OK)'], tightOil[tightOil.columns[-1]]])

	plt.xlim('2000-01-01', '2020-01-01')
	plt.legend(labs, loc = 'upper left')
	plt.xlabel('Year')
	plt.ylabel('Monthly Production [Billion Btu]')
	plt.savefig("Figures/tightOilMonthly.png", dpi=300)
plotTightOil()

def monthlyToAnnual(d):
	da = pd.DataFrame()
	for n in d.index.year.unique():
		x = d.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
		da = da.append(pd.DataFrame(data = np.atleast_2d(x), columns = d.columns, index = [str(n)+'-01-01']))
	da.index = pd.to_datetime(da.index, format = '%Y-%m-%d')
	da.index.name = 'Date'
	return(da)
tightOilAnnual = monthlyToAnnual(tightOil)

onlyTX = [col for col in tightOil.columns if 'TX' in col]
sharedTX = [col for col in tightOil.columns if 'TX &' in col]
sharedTX.extend([col for col in tightOil.columns if '& TX' in col])
onlyTX = [x for x in onlyTX if x not in sharedTX]
txt = tightOil[onlyTX].sum(axis=1)
ok_cols = [col for col in tightOil.columns if 'OK' in col]
okt = tightOil[ok_cols].sum(axis=1) #no shared resources for ok 
okr = allOil['OK'] - okt

# split up the texas shared data 
def TXshared(tx):
	# new mexico --> shared tight oil exceeds nm total oil production 
	nm_cols = [col for col in tightOil.columns if 'NM' in col]
	nm = tightOil[nm_cols].sum(axis=1)
	maxShared = pd.concat([nm, allOil['NM']], axis=1).min(axis=1)
	nmt = np.random.uniform(low=0, high=maxShared) #tight oil in new mexico, drawn from a uniform distribution 
	nmr = allOil['NM']-nmt # regular oil from new mexico
	txShared = nm - nmt #texas existing tight oil + the share that has to be attributed to texas because of limitations + the share that isn't in new mexico (max shared cancels out)
	
	NMT = pd.Series(index = nmr.index, data = nmt)

	#louisiana 
	maxShared = pd.concat([tightOil['Austin Chalk (LA & TX)'], allOil['LA']], axis=1).min(axis=1)
	lat = np.random.uniform(low=0, high = maxShared)
	lar = allOil['LA'] - lat
	tx = txShared + tightOil['Austin Chalk (LA & TX)'] - lat # texas tight oil + the share that has to be attributed to texas because of limits

	LAT = pd.Series(index = lar.index, data = lat)
	return tx, NMT, nmr, LAT, lar 
txtight, nmt, nmr, lat, lar = TXshared(txt)

txt = txt + txtight
txr = allOil.TX - txt
plt.figure()
plt.plot(txt)
plt.plot(allOil.TX)
plt.legend(('tight oil', 'all oil'))
plt.savefig('Figures/txOilCheck.png', dpi = 300)

def otherShared():
	# figure out a split for ND & MT
	b = tightOil['Bakken (ND & MT)']
	a = allOil.ND + allOil.MT
	plt.figure()
	plt.plot(b)
	plt.plot(a)
	plt.plot(allOil.ND)
	plt.plot(allOil.MT)
	plt.legend(('tight oil', 'all oil', 'ND', 'MT'))
	plt.savefig("Figures/bakken.png", dpi=300)

	# most of the oil is from ND, only a little is from MT
	maxShared = pd.concat([b, allOil['MT']], axis=1).min(axis=1)
	mtt = np.random.uniform(maxShared)
	mtr = allOil['MT'] - mtt

	MTT = pd.Series(index = mtr.index, data = mtt)

	ndt = b-maxShared + maxShared - mtt
	ndr = allOil['ND'] - ndt

	check = a - mtt - mtr - ndt - ndr

	plt.figure()
	plt.plot(check)
	plt.savefig('Figures/bakkencheck.png', dpi = 300)

	# figure out a split for CO&WY
	n = tightOil['Niobrara-Codell (CO & WY)']
	a = allOil.CO + allOil.WY
	plt.figure()
	plt.plot(n)
	plt.plot(a)
	plt.plot(allOil.CO)
	plt.plot(allOil.WY)
	plt.legend(('tight oil', 'all oil', 'CO', 'WY'))
	plt.savefig("Figures/niobrara.png", dpi=300)

	maxShared = pd.concat([n, allOil['WY']], axis=1).min(axis=1)
	wyt = np.random.uniform(maxShared)
	wyr = allOil.WY - wyt

	WYT = pd.Series(index = wyr.index, data = wyt)

	cot = n - wyt
	cor = allOil.CO - cot

	check = a - wyt - wyr - cot - cor 
	plt.figure()
	plt.plot(check)
	plt.savefig('Figures/niobraracheck.png', dpi = 300)
	return cot, cor, WYT, wyr, MTT, mtr, ndt, ndr
cot, cor, wyt, wyr, mtt, mtr, ndt, ndr = otherShared()

#load actual lease gas data:
leaseGas = pd.read_csv('Data/EIA_LeasePlantNG.csv')
leaseGas.Date = pd.to_datetime(leaseGas.Date, format = '%Y')
leaseGas = leaseGas.sort_values(by = 'Date')
leaseGas = leaseGas.set_index('Date')
leaseGas = leaseGas.drop(['Unnamed: 0'], axis = 1)
leaseGas = leaseGas*1.027 # convert to billion btu 

# run check
def runLeaseGasCheck(monthlyTightOil, monthlyRegularOil, stateCode):
	assumedLease = monthlyTightOil*14/1000 #+ monthlyRegularOil/11# lease gas estimate from paper maybe make this a draw from a distribution 
	assumedLease = assumedLease.to_frame(name = 'AssumedLease')
	assumedLeaseAnnual = monthlyToAnnual(assumedLease)

	plt.figure()
	plt.plot(assumedLeaseAnnual)
	plt.plot(leaseGas[stateCode])
	#plt.savefig('Figures/'+stateCode+'leasegascheck.png', dpi = 300)

runLeaseGasCheck(txt, txr, 'TX')
runLeaseGasCheck(okt, okr, 'OK')
runLeaseGasCheck(nmt, nmr, 'NM')
runLeaseGasCheck(lat, lar, 'LA')
runLeaseGasCheck(cot, cor, 'CO')
runLeaseGasCheck(wyt, wyr, 'WY')
runLeaseGasCheck(mtt, mtr, 'MT')
runLeaseGasCheck(ndt, ndr, 'ND')

tightOilStates = ['TX', 'OK', 'NM', 'LA', 'CO', 'WY', 'MT', 'ND']
avgUSEROI = np.average((550,100,100,1.5,11.25,4.5,95,11,250))

oilPetroleumConsumed = pd.DataFrame(index = allOil.index)
for n in allOil.columns:
	if n in tightOilStates:
		if n == 'TX': oilPetroleumConsumed[n] = txt*0.001 + txr/avgUSEROI
		elif n == 'OK': oilPetroleumConsumed[n] = okt*0.001 + okr/avgUSEROI
		elif n == 'NM': oilPetroleumConsumed[n] = nmt*0.001 + nmr/avgUSEROI
		elif n == 'LA': oilPetroleumConsumed[n] = lat*0.001 + lar/avgUSEROI
		elif n == 'CO': oilPetroleumConsumed[n] = cot*0.001 + cor/avgUSEROI
		elif n == 'WY': oilPetroleumConsumed[n] = wyt*0.001 + wyr/avgUSEROI
		elif n == 'MT': oilPetroleumConsumed[n] = mtt*0.001 + mtr/avgUSEROI
		else: oilPetroleumConsumed[n] = ndt*0.001 + ndr/avgUSEROI
	elif n == 'AK': oilPetroleumConsumed[n] = allOil[n]/80 #ANS average
	else: oilPetroleumConsumed[n]= allOil[n]/avgUSEROI 


oilPetroleumConsumed = oilPetroleumConsumed.drop('US', axis = 1)
oilPetroleumConsumed.insert(0, 'US', oilPetroleumConsumed.sum(axis = 1)) 
oilPetroleumConsumed.to_csv('Data/OilDieselConsumptionMonthly.csv')
oilPetroleumConsumedAnnual = monthlyToAnnual(oilPetroleumConsumed)
oilPetroleumConsumedAnnual.to_csv('Data/OilDieselConsumptionAnnual.csv')
