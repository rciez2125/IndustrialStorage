# this script loads cleaned up EIA, gdp, and manufacturing utilization data to analyze state-level trends
# to use it correctly, run the "loadEIAdata" script, the "oilCorrection" script to remove oil drilling energy consumption
# and  ensure that GDP data and FRED data for capacity utilization are available

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import date
import EIAgov
from scipy import stats
from sklearn.linear_model import LinearRegression

stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

def readEnergyData(fileName, dateFormat):
	# reads csv files 
	d = pd.read_csv(fileName)
	d.Date = pd.to_datetime(d.Date, format = dateFormat)
	d = d.sort_values(by = 'Date')
	d = d.set_index('Date')
	if "Unnamed: 0" in d:
		d = d.drop('Unnamed: 0', axis = 1)
	return d

def convertCoalMonthly():
	c = pd.read_csv('Data/EIA_IndCoal2.csv')
	c = c.drop('Unnamed: 0', axis = 1); c=c.rename(columns = {'Date':'Quarter'})
	c['Date'] = pd.PeriodIndex(c['Quarter'], freq='Q').to_timestamp()
	c = c.set_index('Date'); c = c.drop('Quarter', axis = 1); c = c.fillna(0)*0.02009 # convert from short tons to billion btu

	cm = pd.DataFrame()
	for n in c.index:
		h = c.loc[n]/3 # divide into equal amounts per month
		cm = cm.append(pd.DataFrame(data =np.atleast_2d(h.values), columns = c.columns, index=[str(n.year)+'-'+str(n.month+2)+'-01']))
		cm = cm.append(pd.DataFrame(data =np.atleast_2d(h.values), columns = c.columns, index=[str(n.year)+'-'+str(n.month+1)+'-01']))
		cm = cm.append(pd.DataFrame(data =np.atleast_2d(h.values), columns = c.columns, index=[str(n.year)+'-'+str(n.month)+'-01']))
	cm.index = pd.to_datetime(cm.index, format = '%Y-%m-%d')
	cm.index.name = 'Date'
	cm = cm.sort_values(by = 'Date')
	cm = cm.loc['2001-01-01':'2018-12-01']
	return(cm)

def energy_process(assumptions):
	# load annual total energy consumed, without electricity losses 
	e = readEnergyData('Data/EIA_IndEnergy.csv', '%Y')
	e = e.loc['2001-01-01':'2018-01-01'] # annual data

	#load monthly electricity consumption 
	s = readEnergyData('Data/EIA_IndElec.csv', '%Y%m') *3.412 # electricity to Btu
	s = s.loc['2001-01-01':'2018-12-01'] 
	
	# load monthly natural gas consumption 
	g1 = readEnergyData('Data/EIA_IndNG.csv', '%Y%m').loc['2001-01-01':'2018-12-01'] # million cubic feet, monthly data by state, no lease, plant gas 
	g2 = readEnergyData('Data/EIA_IndNGA.csv', '%Y').loc['2001-01':'2019-01'] # million cubic feet, annual data by state
	g3 = readEnergyData('Data/EIA_IndNGAB.csv', '%Y').loc['2001-01':'2019-01'] # billion btu, annual data by state
	g4 = g3/g2
	g5 = g4.resample('MS').pad().loc['2001-01-01':'2018-12-01']
	g = g1*g5
	
	# load annual lease gas and plant gas consumption 
	leaseGas = readEnergyData('Data/EIA_LeasePlantNG.csv', '%Y').loc['2001-01':'2018-01']
	plantGas = readEnergyData('Data/EIA_PlantNG.csv', '%Y').loc['2001-01':'2018-01']
	leaseGas.insert(0, 'US', leaseGas.sum(axis = 1))
	plantGas.insert(0, 'US', plantGas.sum(axis = 1))
	crudeOilEnergy = pd.read_csv('Data/OilDieselConsumptionAnnual.csv')
	crudeOilEnergy.Date = pd.to_datetime(crudeOilEnergy.Date)
	crudeOilEnergy = crudeOilEnergy.sort_values(by='Date')
	crudeOilEnergy = crudeOilEnergy.set_index('Date').loc['2001-01-01':'2018-01-01']

	cm = convertCoalMonthly()
	monthly = s+g
	monthly = monthly.add(cm, fill_value=0)

	if assumptions != 'none':
		#load extra data
		stateNaphtha = readEnergyData('Data/EIA_StateNaphtha.csv', '%Y') * 5.25 # convert to billion btu
		stateEthane = readEnergyData('Data/EIA_StateEthane.csv', '%Y') * 2.78 # convert to billion btu 
		monthlyNaphtha = readEnergyData('Data/monthlyNaphtha.csv', '%Y-%m-%d').loc['2010-01-01':'2018-12-01'] * 5.25#convert to btu
		monthlyEthane = readEnergyData('Data/monthlyEthane.csv', '%Y-%m-%d').loc['2010-01-01':'2018-12-01'] *2.78 # convert to btu 

		statePropane = readEnergyData('Data/EIA_StatePropane.csv', '%Y') #already in billion btu
		statePropylene = readEnergyData('Data/EIA_StatePropylene.csv', '%Y') #already in billion btu
		monthlyPropane = readEnergyData('Data/monthlyPropane.csv', '%Y-%m-%d').loc['2010-01-01':'2018-12-01']
		monthlyPropylene = readEnergyData('Data/monthlyPropylene.csv', '%Y-%m-%d').loc['2010-01-01':'2018-12-01']
		stateStillGas = readEnergyData('Data/EIA_StateStillGas.csv', '%Y') * 6.287 #convert to billion btu
		monthlyStillGas = readEnergyData('Data/monthlyStillGas.csv', '%Y-%m-%d').loc['2010-01-01':'2018-12-01'] * 6.287 #convert to billion btu

		stateAsphalt = readEnergyData('Data/EIA_StateAsphalt.csv', '%Y')
		stateSpecialNap = readEnergyData('Data/EIA_StateSpecialNap.csv', '%Y')
		stateMiscPet = readEnergyData('Data/EIA_StateMiscPet.csv', '%Y')
		monthlyAsphalt = readEnergyData('Data/monthlyAsphalt.csv', '%Y-%m-%d').loc['2010-01-01':'2018-12-01']
		monthlySpecialNap = readEnergyData('Data/monthlySpecialNap.csv', '%Y-%m-%d').loc['2010-01-01':'2018-12-01']
		monthlyMiscPet = readEnergyData('Data/monthlyMiscPet.csv', '%Y-%m-%d').loc['2010-01-01':'2018-12-01']
		
		addCols1 = [e for e in stateNaphtha if e not in monthlyNaphtha]
		for z in range(len(addCols1)): monthlyNaphtha[str(addCols1[z])] = np.nan
		addCols2 = [e for e in stateEthane if e not in monthlyEthane]
		for z in range(len(addCols2)): monthlyEthane[str(addCols2[z])] = np.nan

		addCols3 = [e for e in statePropane if e not in monthlyPropane]
		for z in range(len(addCols3)): monthlyPropane[str(addCols3[z])] = np.nan
		
		addCols4 = [e for e in statePropylene if e not in monthlyPropylene]
		for z in range(len(addCols4)): monthlyPropylene[str(addCols4[z])] = np.nan

		addCols5 = [e for e in stateStillGas if e not in monthlyStillGas]
		for z in range(len(addCols5)): monthlyStillGas[str(addCols5[z])] = np.nan

		addCols6 = [e for e in stateAsphalt if e not in monthlyAsphalt]
		for z in range(len(addCols6)): monthlyAsphalt[str(addCols6[z])] = np.nan
		addCols7 = [e for e in stateSpecialNap if e not in monthlySpecialNap]
		for z in range(len(addCols7)): monthlySpecialNap[str(addCols7[z])] = np.nan
		addCols8 = [e for e in stateMiscPet if e not in monthlyMiscPet]
		for z in range(len(addCols8)): monthlyMiscPet[str(addCols8[z])] = np.nan

	e = e.subtract(crudeOilEnergy, fill_value = 0); e = e.subtract((leaseGas*g4), fill_value = 0);  e = e.subtract((plantGas*g4), fill_value = 0)
	monthlyPercent =  pd.DataFrame(index = e.index, columns = e.columns); quarterlyPercent = pd.DataFrame(index = e.index, columns = e.columns)

	for n in np.linspace(2010, 2018, 9):#(2001, 2018, 18):
		n = int(n)
		sales = s.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
		gas = g1.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)*g4.loc[str(n)+'-01-01']
		coal = cm.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
		monthlyCombo = sales.add(gas, fill_value = 0)
		combo = monthlyCombo.add(coal, fill_value = 0)

		if assumptions != 'none': 
			for z in range(len(addCols1)): monthlyNaphtha[str(addCols1[z])].loc[str(n)+'-01-01':str(n)+'-12-01'] = monthlyNaphtha.US.loc[str(n)+'-01-01':str(n)+'-12-01'] *stateNaphtha[str(addCols1[z])].loc[str(n)].values/monthlyNaphtha.US.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
			for z in range(len(addCols2)): monthlyEthane[str(addCols2[z])].loc[str(n)+'-01-01':str(n)+'-12-01'] = monthlyEthane.US.loc[str(n)+'-01-01':str(n)+'-12-01'] * stateEthane[str(addCols2[z])].loc[str(n)].values/monthlyEthane.US.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
			monthlyCombo = monthlyCombo.add(monthlyNaphtha.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis = 0), fill_value = 0)
			monthlyCombo = monthlyCombo.add(monthlyEthane.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0), fill_value = 0)
			combo = monthlyCombo.add(coal, fill_value = 0)
			if assumptions == 'ethanenaphthaprop':
				for z in range(len(addCols4)): monthlyPropylene[str(addCols4[z])].loc[str(n)+'-01-01':str(n)+'-12-01'] = monthlyPropylene.US.loc[str(n)+'-01-01':str(n)+'-12-01'] * statePropylene[str(addCols4[z])].loc[str(n)].values/monthlyPropylene.US.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
				#monthlyCombo = monthlyCombo.add(monthlyNaphtha.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis = 0), fill_value = 0)
				#monthlyCombo = monthlyCombo.add(monthlyEthane.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0), fill_value = 0)
				monthlyCombo = monthlyCombo.add(monthlyPropylene.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0), fill_value = 0)
				combo = monthlyCombo.add(coal, fill_value = 0)
			elif assumptions == 'allextra':
				for z in range(len(addCols3)):monthlyPropane[str(addCols3[z])].loc[str(n)+'-01-01':str(n)+'-12-01'] = monthlyPropane.US.loc[str(n)+'-01-01':str(n)+'-12-01'] *statePropane[str(addCols3[z])].loc[str(n)].values/monthlyPropane.US.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
				monthlyCombo = monthlyCombo.add(monthlyPropane.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0), fill_value = 0)
				for z in range(len(addCols4)): monthlyPropylene[str(addCols4[z])].loc[str(n)+'-01-01':str(n)+'-12-01'] = monthlyPropylene.US.loc[str(n)+'-01-01':str(n)+'-12-01'] * statePropylene[str(addCols4[z])].loc[str(n)].values/monthlyPropylene.US.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
				monthlyCombo = monthlyCombo.add(monthlyPropylene.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0), fill_value = 0)
				for z in range(len(addCols5)): monthlyStillGas[str(addCols5[z])].loc[str(n)+'-01-01':str(n)+'-12-01'] = monthlyStillGas.US.loc[str(n)+'-01-01':str(n)+'-12-01'] * stateStillGas[str(addCols5[z])].loc[str(n)].values/monthlyStillGas.US.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
				monthlyCombo = monthlyCombo.add(monthlyStillGas.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0), fill_value = 0)
				for z in range(len(addCols6)): monthlyAsphalt[str(addCols6[z])].loc[str(n)+'-01-01':str(n)+'-12-01'] = monthlyAsphalt.US.loc[str(n)+'-01-01':str(n)+'-12-01'] * stateAsphalt[str(addCols6[z])].loc[str(n)].values/monthlyAsphalt.US.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
				monthlyCombo = monthlyCombo.add(monthlyAsphalt.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0), fill_value = 0)
				for z in range(len(addCols7)): monthlySpecialNap[str(addCols7[z])].loc[str(n)+'-01-01':str(n)+'-12-01'] = monthlySpecialNap.US.loc[str(n)+'-01-01':str(n)+'-12-01'] * stateSpecialNap[str(addCols7[z])].loc[str(n)].values/monthlySpecialNap.US.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
				monthlyCombo = monthlyCombo.add(monthlySpecialNap.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0), fill_value = 0)
				for z in range(len(addCols8)): monthlyMiscPet[str(addCols8[z])].loc[str(n)+'-01-01':str(n)+'-12-01'] = monthlyMiscPet.US.loc[str(n)+'-01-01':str(n)+'-12-01'] * stateMiscPet[str(addCols8[z])].loc[str(n)].values/monthlyMiscPet.US.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
				monthlyCombo = monthlyCombo.add(monthlyMiscPet.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0), fill_value = 0)
				combo = monthlyCombo.add(coal, fill_value = 0)
		
		p = combo/e.loc[str(n)+'-01-01']

		monthly_avg = np.tile((e.loc[str(n)+'-01-01']-combo)/12, (12,1)) #Average total energy not in electricity sales, electricity losses, natural gas, or coal data 
		monthly[str(n)+'-01-01':str(n)+'-12-01'] = monthly[str(n)+'-01-01':str(n)+'-12-01'] + monthly_avg #+ monthly_avg.values
		monthlyPercent.loc[str(n)+'-01-01'] = monthlyCombo/e.loc[str(n)+'-01-01']
		quarterlyPercent.loc[str(n)+'-01-01'] = coal/e.loc[str(n)+'-01-01']
	
	if assumptions =='ethanenaphtha': monthly = monthly + monthlyNaphtha + monthlyEthane
	elif assumptions == 'ethanenaphthaprop': monthly = monthly + monthlyNaphtha + monthlyEthane + monthlyPropylene
	elif assumptions == 'allextra': monthly = monthly + monthlyNaphtha + monthlyEthane + monthlyPropylene + monthlyPropane + monthlyStillGas + monthlySpecialNap + monthlyMiscPet + monthlyAsphalt

	return monthly, monthlyPercent, quarterlyPercent, e

def plotStateConsumptionvCapacity(bigStateCodes, overall_cap, monthly_energy, e, C):
    plt.figure(figsize = (6.5, 6.5))
    fig1, ax = plt.subplots()
    for q in range(12): 
        state = bigStateCodes[q]
        
        if q < 1: h = .6
        elif q < 2: h = 0.4
        elif q < 4: h = 0.2
        else: h = 0.1
        plt.subplot(position = [0.08+(q%4)*0.235, 0.37-(q//4)*0.14, 0.2, h])
        z = (overall_cap[state].loc['2014-01-01':'2018-12-01'] - np.mean(overall_cap[state].loc['2014-01-01':'2018-12-01']))#/np.std(overall_cap[state].loc['2014-01-01':'2018-12-01'])
        l2 = stats.linregress(x=z, y = monthly_energy[state].loc['2014-01-01':'2018-12-01'])
        linpred = l2.intercept + l2.slope*(np.linspace(50,100,10)-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01']))#/np.std(overall_cap[state].loc['2014-01-01':'2018-01-01'])
        plt.plot((np.linspace(50,100,10)-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01'])), linpred, '-', color = C)
        plt.scatter(((overall_cap[state].loc['2014-01-01':'2018-12-01']-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01']))), monthly_energy[state].loc['2014-01-01':'2018-12-01'], color = C, s = 1)

        l4 = LinearRegression().fit(z.to_numpy().reshape(-1,1), monthly_energy[state].loc['2014-01-01':'2018-12-01'].to_numpy().reshape(-1,1))
        y_pred = l4.predict(z.to_numpy().reshape(-1,1))
        mse = sum((monthly_energy[state].loc['2014-01-01':'2018-12-01'].to_numpy().reshape(-1,1) - y_pred)**2)/60
        z2 = np.linspace(50,100,10)-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01'])
        b2 = np.sqrt(mse*(1+(1/60)+((z2**2)/sum(z2**2))))
        y_pred2 = l4.predict(z2.reshape(-1,1))

        plt.fill_between(z2, np.concatenate(y_pred2 - 1.96*b2.reshape((10,1))), np.concatenate(y_pred2 + 1.96*b2.reshape((10,1))), color = C, alpha = 0.5)
        plt.title(bigStateCodes[q], fontsize = 8, pad = 0.5)
        plt.xlim(-10,10)

        plt.ylim(bottom = 0)
        if q >7: plt.xticks(fontsize = 8)
        else: plt.xticks([-10, 0, 10], labels = ('', '', ''))
        if q == 0: 
        	plt.yticks([0, 100000, 200000, 300000, 400000, 500000,600000], labels = ('0', ' ', '200', '', '400','', '600'), fontsize = 8)
        	plt.ylim(0, 600000)
        elif q == 1: plt.yticks([0, 100000, 200000, 300000, 400000], labels = (' ', ' ', ' ', ' ', ' '), fontsize = 8)
        elif q<4: plt.yticks([0, 100000, 200000], labels = (' ', ' ', ' '), fontsize = 8)
        else: plt.yticks([0, 100000], labels = (' ', ' '), fontsize = 8)
        if q in (4,8): plt.yticks([0, 100000], labels = ('0', '100'), fontsize = 8)
        if q == 4: plt.ylabel('                                      Monthly Estimated Energy Consumption [Trillion Btu]', fontsize = 8)
        elif q==9: plt.xlabel('                                     Manufacturing Capacity Utilization', fontsize = 8)
        if q < 10: plt.text(-4, 8000, 'Average Capacity\nUtilization =' + str(np.round(np.mean(overall_cap[state].loc['2014-01-01':'2018-12-01']),1))+'%', fontsize = 6)
        else: plt.text(-9, 60000, 'Average Capacity\nUtilization =' + str(np.round(np.mean(overall_cap[state].loc['2014-01-01':'2018-12-01']),1))+'%', fontsize = 6)

    plt.savefig('Figures/Fig3.png', dpi=300)
    plt.close()

    b = e.drop(columns = 'US', axis = 1)
    x = 100*b.loc['2018-01-01']/e.US.loc['2018-01-01']
    c = x.nlargest(51)
    plt.figure()
    fig1, ax = plt.subplots(figsize = (6.5, 8))
    for q in range(51-22-1):
        state = c.keys()[q+22]
        h, b, L = 0.075, 0.88-(q//4)*0.125, 0.08+(q%4)*0.235
        plt.subplot(position = [L,b , 0.2, h])
        z = (overall_cap[state].loc['2014-01-01':'2018-12-01'] - np.mean(overall_cap[state].loc['2014-01-01':'2018-12-01']))#/np.std(overall_cap[state].loc['2014-01-01':'2018-12-01'])
        l2 = stats.linregress(x=z, y = monthly_energy[state].loc['2014-01-01':'2018-12-01'])
        linpred = l2.intercept + l2.slope*(np.linspace(50,100,10)-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01']))#/np.std(overall_cap[state].loc['2014-01-01':'2018-01-01'])
        
        plt.plot((np.linspace(50,100,10)-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01'])), linpred, '-', color = C)
        plt.scatter(((overall_cap[state].loc['2014-01-01':'2018-12-01']-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01']))), monthly_energy[state].loc['2014-01-01':'2018-12-01'], color = C, s = 1)
        
        l4 = LinearRegression().fit(z.to_numpy().reshape(-1,1), monthly_energy[state].loc['2014-01-01':'2018-12-01'].to_numpy().reshape(-1,1))
        y_pred = l4.predict(z.to_numpy().reshape(-1,1))
        mse = sum((monthly_energy[state].loc['2014-01-01':'2018-12-01'].to_numpy().reshape(-1,1) - y_pred)**2)/60
        z2 = np.linspace(50,100,10)-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01'])
        y_pred2 = l4.predict(z2.reshape(-1,1))

        plt.fill_between(z2, np.concatenate(y_pred2 - 1.96*b2.reshape((10,1))), np.concatenate(y_pred2 + 1.96*b2.reshape((10,1))), color = C, alpha = 0.5)
        plt.title(state, fontsize = 8, pad = 0.5); plt.xlim(-10,10)

        plt.ylim(bottom = 0)
        if q >23: plt.xticks(fontsize = 8)
        else: plt.xticks([-10, 0, 10], labels = ('', '', ''))
        if q in (0,4,8,12, 16, 20, 24): plt.yticks([0, 100000], labels = ('0', '100'), fontsize = 8)
        else: plt.yticks([0, 100000], labels = (' ', ' '), fontsize = 8) 
        if q == 12: plt.ylabel('Monthly Estimated Energy Consumption [Trillion Btu]', fontsize = 8)
        elif q==25: plt.xlabel('                                     Manufacturing Capacity Utilization', fontsize = 8)

    plt.gcf().set_size_inches(6.5, 7.02)
    plt.savefig('Figures/Fig3_SI.png', dpi=300)
    plt.close()

    plt.figure()
    fig1, ax = plt.subplots()
    for q in range(22):
        state = c.keys()[q]
        if q < 1: h, b, L = .45, 0.52, 0.08
        elif q < 2: h, b, L = 0.3, 0.52, 0.08+(q%4)*0.235
        elif q < 4: h, b, L = 0.15, 0.67, 0.08+(q%4)*0.235
        elif q < 6: h, b, L = 0.075, 0.52, 0.55+(q%4)*0.235
        else: h, b, L = 0.075, 0.52-((q-2)//4)*0.11, 0.08+((q-2)%4)*0.235
        
        plt.subplot(position = [L,b , 0.2, h])
        z = (overall_cap[state].loc['2014-01-01':'2018-12-01'] - np.mean(overall_cap[state].loc['2014-01-01':'2018-12-01']))#/np.std(overall_cap[state].loc['2014-01-01':'2018-12-01'])
        l2 = stats.linregress(x=z, y = monthly_energy[state].loc['2014-01-01':'2018-12-01'])
        linpred = l2.intercept + l2.slope*(np.linspace(50,100,10)-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01']))#/np.std(overall_cap[state].loc['2014-01-01':'2018-01-01'])
        
        plt.plot((np.linspace(50,100,10)-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01'])), linpred, '-', color = C)
        plt.scatter(((overall_cap[state].loc['2014-01-01':'2018-12-01']-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01']))), monthly_energy[state].loc['2014-01-01':'2018-12-01'], color = C, s = 1)

        l4 = LinearRegression().fit(z.to_numpy().reshape(-1,1), monthly_energy[state].loc['2014-01-01':'2018-12-01'].to_numpy().reshape(-1,1))
        y_pred = l4.predict(z.to_numpy().reshape(-1,1))
        mse = sum((monthly_energy[state].loc['2014-01-01':'2018-12-01'].to_numpy().reshape(-1,1) - y_pred)**2)/60

        z2 = np.linspace(50,100,10)-np.mean(overall_cap[state].loc['2014-01-01':'2018-01-01'])
        b2 = np.sqrt(mse*(1+(1/60)+((z2**2)/sum(z2**2))))
        y_pred2 = l4.predict(z2.reshape(-1,1))
     
        plt.fill_between(z2, np.concatenate(y_pred2 - 1.96*b2.reshape((10,1))), np.concatenate(y_pred2 + 1.96*b2.reshape((10,1))), color = C, alpha = 0.5)
        plt.title(state, fontsize = 8, pad = 0.5); plt.xlim(-10,10)

        plt.ylim(bottom = 0)
        if q >17: plt.xticks(fontsize = 8)
        else: plt.xticks([-10, 0, 10], labels = ('', '', ''))
        if q == 0: 
        	plt.yticks([0, 100000, 200000, 300000, 400000, 500000,600000], labels = ('0', ' ', '200', '', '400','', '600'), fontsize = 8)
        	plt.ylim(0, 600000)
        elif q == 1: plt.yticks([0, 100000, 200000, 300000, 400000], labels = (' ', ' ', ' ', ' ', ' '), fontsize = 8)
        elif q<4: plt.yticks([0, 100000, 200000], labels = (' ', ' ', ' '), fontsize = 8)
        else: plt.yticks([0, 100000], labels = (' ', ' '), fontsize = 8)
        if q in (6,10,14,18): plt.yticks([0, 100000], labels = ('0', '100'), fontsize = 8)
        if q == 6: plt.ylabel('                           Monthly Estimated Energy Consumption [Trillion Btu]', fontsize = 8)
        elif q==19: plt.xlabel('                                     Manufacturing Capacity Utilization', fontsize = 8)

    plt.gcf().set_size_inches(6.5, 8)
    plt.savefig('Figures/Fig3_SI2.png', dpi=300)
    plt.close()

def plotData(assumptions):
	#Gets EIA data
    monthly_energy, monthlyPercent, quarterlyPercent, e = energy_process(assumptions)

    #Gets FRED, EPA, and BEA data and organizes. Finds overall capacity data for 2018.
    overall_cap = pd.read_csv('Data/StateCapacityUtilization.csv')
    overall_cap.DATE = pd.to_datetime(overall_cap.DATE, format = '%Y-%m-%d')
    overall_cap = overall_cap.set_index('DATE').loc['2001-01-01':'2018-12-01']

    overall_prod = pd.read_csv('Data/stateIndustrialProductionIndex.csv')
    overall_prod.DATE = pd.to_datetime(overall_prod.DATE, format = '%Y-%m-%d')
    overall_prod = overall_prod.set_index('DATE').loc['2001-01-01': '2018-12-01']

    annualCap = overall_cap.loc['2018-01-01':'2018-12-01']
    annualMonthlyEnergy = monthly_energy.loc['2018-01-01':'2018-12-01']

    plt.figure(figsize=(3.33,5))
    plt.subplot(position = [0.08, 0.105, 0.4, 0.83])
    E= e.loc['2018-01-01'].nsmallest(52)
    M, Q = monthlyPercent[E.index], quarterlyPercent[E.index]
    E = E.drop(labels = 'US')
    
    plt.barh(E.index, E)
    plt.ylim(-0.5, 51); plt.yticks(fontsize = 7)
    plt.xlim(0, 7000000); plt.xticks([0, 2000000, 4000000, 6000000], labels = ['0', '2000', '4000', '6000'], fontsize = 8)
    plt.text(6300000, 49.5, 'A', fontsize = 8); plt.xlabel('Total Manufacturing Energy\nConsumption [Trillion Btu]', fontsize = 8 )

    plt.subplot(position = [0.56, 0.105, 0.4, 0.83])
    m_us, q_us = M.US.loc['2018-01-01'], Q.US.loc['2018-01-01']
    M = M.drop(columns = 'US', axis = 1); Q = Q.drop(columns = 'US', axis = 1)
    plt.barh(M.columns, M.loc['2018-01-01'], color = 'C2')
    plt.barh(Q.columns, Q.loc['2018-01-01'], left = M.loc['2018-01-01'], color = 'C1')
    plt.plot([m_us, m_us], [-1, 52], '-', color = 'C2', alpha = 0.5)
    plt.yticks(fontsize = 7); plt.ylim(-0.5, 51)
    plt.plot([q_us + m_us, q_us + m_us], [-1, 52], '-', color = 'C1', alpha = 0.5)
    plt.xlim(0,1); plt.xticks([0, 0.25, 0.5, 0.75, 1], labels = ('0', '25%', '50%', '75%', '100%'), fontsize = 7)
    plt.text(.9, 49.5, 'B', fontsize = 8)
    plt.text(m_us, 51.5, 'US Monthly\nAverage', color = 'C2', fontsize = 6, horizontalalignment = 'right')
    plt.text(q_us + m_us, 51.5, 'US Monthly\n+Quarterly\nAverage', color = 'C1', fontsize = 6)
    plt.xlabel('Percentage', fontsize = 8)
    plt.savefig("Figures/fig2.png", dpi=300)
    plt.close()
 
    b = e.drop(columns = 'US', axis = 1)
    x = 100*b.loc['2018-01-01']/e.US.loc['2018-01-01']
    y = x.where(x>1).dropna()
    z = y.nlargest(16)
    bigStateCodes = z.keys()

    plotStateConsumptionvCapacity(bigStateCodes, overall_cap, monthly_energy, e, 'C0')

    plt.figure()
    for s in range(len(bigStateCodes)):
    	state = bigStateCodes[s]
    	plt.subplot(4,4,s+1)
    	plt.plot(overall_prod[state].loc['2014-01-01':'2018-12-01'])
    	plt.plot(overall_cap[state].loc['2014-01-01':'2018-12-01'])
    	plt.plot(100*overall_prod[state].loc['2014-01-01':'2018-12-01']/overall_cap[state].loc['2014-01-01':'2018-12-01'])
    	plt.title(bigStateCodes[s])
    plt.savefig('Figures/StateOutput.png', dpi = 300)
    plt.close()

def monthlyToAnnual(d):
	da = pd.DataFrame()
	for n in d.index.year.unique():
		x = d.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0).values
		da = da.append(pd.DataFrame(data = np.atleast_2d(x), columns = d.columns, index = [str(n)+'-01-01']))
	da.index = pd.to_datetime(da.index, format = '%Y-%m-%d')
	da.index.name = 'Date'
	return(da)

def compareToTotalElec(assumptions):
    allElec = readEnergyData('Data/EIA_MonthlyElecSales.csv', '%Y%m')
    allElec = allElec*3.412 # convert to Btu

    monthly_energy, monthlyPercent, quarterlyPercent, e = energy_process(assumptions)
    b = e.drop(columns = 'US', axis = 1)
    x = 100*b.loc['2018-01-01']/e.US.loc['2018-01-01']
    y = x.where(x>1).dropna()
    z = y.nlargest(12)
    bigStateCodes = z.keys()
    overall_cap = pd.read_csv('Data/StateCapacityUtilization.csv')
    overall_cap.DATE = pd.to_datetime(overall_cap.DATE, format = '%Y-%m-%d')
    overall_cap = overall_cap.set_index('DATE')
    overall_cap = overall_cap.loc['2001-01-01':'2018-12-01']
    allElec = allElec.loc['2014-01-01':'2018-12-01']

    o = overall_cap.loc['2014-01-01':'2018-12-01']
    m = monthly_energy.loc['2014-01-01':'2018-12-01']

    plt.figure(figsize = (6.5,4))
    plt.subplot(position = [0.1, 0.47, 0.85, 0.5])

    plt.plot([-10, -10], [2, 2], color = 'C0')
    plt.plot([-10, -10], [2, 2], color = 'C1')
    plt.plot([-10, -10], [2, 2], color = 'C2')
    
    C0_dict =  {'patch_artist': True,
             'boxprops': dict(color='C0', facecolor='w'),
             'capprops': dict(color='C0'),
             'flierprops': dict(color='C0', markeredgecolor='C0'),
             'medianprops': dict(color='C0'),
             'whiskerprops': dict(color='C0')}

    C1_dict =  {'patch_artist': True,
             'boxprops': dict(color='C1', facecolor='w'),
             'capprops': dict(color='C1'),
             'flierprops': dict(color='C1', markeredgecolor='C1'),
             'medianprops': dict(color='C1'),
             'whiskerprops': dict(color='C1')}

    plt.boxplot(allElec[bigStateCodes], **C0_dict)
    plt.boxplot(m[bigStateCodes], **C1_dict)
    elec_data = np.empty((len(bigStateCodes),3))
    ind_data=np.empty((len(bigStateCodes),3))
    for n in range(len(bigStateCodes)):
        state = bigStateCodes[n]
        z = (o[state] - np.mean(o[state]))

        l4 = LinearRegression().fit(z.to_numpy().reshape(-1,1), m[state].to_numpy().reshape(-1,1))
        
        y_pred = l4.predict(z.to_numpy().reshape(-1,1))
        mse = sum((m[state].to_numpy().reshape(-1,1) - y_pred)**2)/60
        se = np.sqrt((1-l4.score(z.to_numpy().reshape(-1,1), m[state].to_numpy().reshape(-1,1))**2)/(12*5-2))
        a = np.sqrt((1/60)+((z**2)/sum(z**2)))

        ci_upper = y_pred + 2*se*a.values.reshape((60,1))
        ci_lower = y_pred - 2*se*a.values.reshape((60,1))
        b = np.sqrt(mse*(1+(1/60)+((z**2)/sum(z**2))))
        pi_upper = y_pred + 1.96*b.values.reshape((60,1))
        pi_lower = y_pred - 1.96*b.values.reshape((60,1))

        z2 = np.array([1])
        print(mse)
        b2 = np.sqrt(mse*(1+(1/60)+(1)))
        y_pred2 = l4.predict(z2.reshape(-1,1))
        pi2_upper = y_pred2 + 1.96*b2.reshape((1,1))
        pi2_lower = y_pred2 - 1.96*b2.reshape((1,1))
        print(y_pred2, pi2_upper, pi2_lower)

        l2 = stats.linregress(x=z, y = m[state])
        #print(l2.intercept, l2.slope, l2.stderr, l2.intercept_stderr)

        #l2 = stats.linregress(x=z, y = m[state])
        #plt.plot([n+1], [10*l2.slope/np.std(o[state])], 'x')
        plt.plot([n+1], 10*l4.coef_, '.', color = 'C2')

        tval = 1.96
        plt.plot([n+1, n+1], [10*(l2.slope+tval*l2.stderr), 10*(l2.slope-tval*l2.stderr)], '-', color = 'C2')
        t = 0.05

        plt.plot([n+1+t, n+1-t], [10*(l2.slope-tval*l2.stderr), 10*(l2.slope-tval*l2.stderr)], '-', color = 'C2')
        plt.plot([n+1+t, n+1-t], [10*(l2.slope+tval*l2.stderr), 10*(l2.slope+tval*l2.stderr)], '-', color = 'C2')
        plt.plot([-10, 20], [0, 0], '-k')

        
        #print(state, 'elec', 1000*(l4.coef_)/np.mean(allElec[state]), 1000*(l2.slope-tval*l2.stderr)/np.percentile(allElec[state], 97.5), 1000*(l2.slope+tval*l2.stderr)/np.percentile(allElec[state], 2.5), 'ind energy', 1000*l4.coef_/np.mean(m[state]), 1000*(l2.slope-tval*l2.stderr)/np.percentile(m[state], 97.5), 1000*(l2.slope+tval*l2.stderr)/np.percentile(m[state], 2.5))
        elec_data[n,0] = 1000*(l4.coef_)/np.mean(allElec[state])
        elec_data[n,1] = 1000*(l2.slope-tval*l2.stderr)/np.percentile(allElec[state], 2.5)
        elec_data[n,2] = 1000*(l2.slope+tval*l2.stderr)/np.percentile(allElec[state], 97.5)

        ind_data[n,0] = 1000*l4.coef_/np.mean(m[state])
        ind_data[n,1] = 1000*(l2.slope-tval*l2.stderr)/np.percentile(m[state], 2.5)
        ind_data[n,2] = 1000*(l2.slope+tval*l2.stderr)/np.percentile(m[state], 97.5)

    plt.text(len(bigStateCodes)+0.25, 500000, 'A', fontsize = 8)
    plt.legend(labels = ('Monthly Electricity', 'Monthly Industrial Energy', '10% Change in Capacity Utilization'), fontsize = 8, loc = 'upper center')
    plt.xticks(range(1, len(bigStateCodes)+1), labels = bigStateCodes)
    plt.xlim(0.5, len(bigStateCodes)+.5)
    #plt.yscale("log")
    plt.ylim(-10000, 550000)
    plt.yticks([0, 100000, 200000, 300000, 400000, 500000], labels = ('0', '100', '200', '300', '400', '500'), fontsize = 8)
    plt.xticks(fontsize = 8)
   
    plt.ylabel('Monthly Energy [trillion Btu]', fontsize = 8)
    
    plt.subplot(position = [0.1, 0.1, 0.85, 0.3])
    width = 0.35
    export_percentage = pd.DataFrame(data = elec_data, columns = ('Elec-base', 'Elec-low', 'Elec-high'), index = bigStateCodes)
    export_percentage['Ind-base'] = ind_data[:,0]
    export_percentage['Ind-low'] = ind_data[:,1]
    export_percentage['Ind-high'] = ind_data[:,2]
    export_percentage.to_csv('PercentageTable.csv')

    elec_data[:,1] = elec_data[:,0]-elec_data[:,1]
    elec_data[:,2] = elec_data[:,2]-elec_data[:,0]
    ind = np.arange(len(elec_data))
    ind_data[:,1] = ind_data[:,0]-ind_data[:,1]
    ind_data[:,2] = ind_data[:,2]-ind_data[:,0]
    rects1 = plt.bar(ind - width/2, elec_data[:,0], width, yerr = elec_data[:,1:3].T)
    rects2 = plt.bar(ind + width/2, ind_data[:,0], width, yerr = ind_data[:,1:3].T)
    plt.xlim(-0.5, len(bigStateCodes)-0.5)
    plt.xticks(range(0, len(bigStateCodes)), labels = bigStateCodes, fontsize = 8)
    plt.yticks(fontsize = 8)
    plt.yticks([-25, 0, 25, 50, 75, 100, 125, 150], fontsize = 8)
    plt.text(len(bigStateCodes)-0.75, 140, 'B', fontsize = 8)
    plt.ylim(-40, 160)
    plt.legend(('Monthly Electricity', 'Monthly Industrial Energy'), fontsize = 8)
    plt.ylabel('Percentage of Monthly Energy', fontsize = 8)
    plt.xlabel('State', fontsize = 8)
    plt.savefig('Figures/Fig4.png', dpi = 300)

# define extra assumptions about data
scenario = 'none'
plotData(scenario)
compareToTotalElec(scenario)