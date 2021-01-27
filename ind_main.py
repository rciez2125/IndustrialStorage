import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import date
import matplotlib.ticker as ticker
import ind_output as ind
import EIAgov
from scipy import stats

# FRED capacity data goes back monthly to 1997 - 2019
# EIA natural gas and electricity data goes back to 2001 - 2020
# EIA annual energy data goes to 2018

def process(naics):
    cap = ind.Fred_data(naics)
    capacity, all_fred = cap.getData()
    capacity = capacity.mean(axis=0)

    emi = ind.EPA_data(naics)
    emissions, all_epa = emi.getData()
    emissions = emissions.sum(axis=0, numeric_only=True) / 1000
    emissions = emissions.sort_index()

    #gdp = ind.BEA_data()
    gdp_percent = ind.BEA_getData()

    fred_num = all_fred.drop(columns = ['Industry', 'Series ID'])
    sum_fred = pd.DataFrame()
    annual_fred = pd.DataFrame()

    #Takes average of repeat NAICS codes in FRED data, then gets average of monthly data for each year.
    count = 0
    for id in fred_num.index:
        if id not in annual_fred.columns:
            sum_fred[id] = fred_num.iloc[fred_num.index.get_loc(id), :].mean()
        while count < len(fred_num.columns):
            annual_fred.loc[fred_num.columns[count].year, id] = sum_fred.iloc[count:count+12, sum_fred.columns.get_loc(id)].mean()
            count += 12
        count = 0

    annual_fred = annual_fred.transpose()
    annual_fred = annual_fred[annual_fred.index.notnull()] #Drops rows with unknown NAICS code
    state_cap = gdp_percent

    #Gets product of national capacity data and state gdp percentage to find state level capacity.
    for id in annual_fred.index:
        if int(id) in gdp_percent.index:
            for year in annual_fred.columns:
                state_cap.loc[int(id), str(year)] = annual_fred.loc[id, year] * gdp_percent.loc[int(id), str(year)]

    return capacity, emissions, all_fred, all_epa, state_cap

#Gets data for the three energy categories, finds percentage of total energy for sales and gas,
#and finds monthly average of total energy

def readEnergyData(fileName, dateFormat):
	d = pd.read_csv(fileName)
	d.Date = pd.to_datetime(d.Date, format = dateFormat)
	d = d.sort_values(by = 'Date')
	d = d.set_index('Date')
	d = d.drop('Unnamed: 0', axis = 1)
	return d

def correlateElecLosses(lossData, s):
	lm = pd.DataFrame()
	for n in lossData.index:
		sales = s.loc[str(n.year)+'-01-01':str(n.year)+'-12-01'].sum(axis=0)
		for q in range(12):
			if q<9:
				x = lossData.loc[n] * (s.loc[str(n.year)+'-0'+str(q+1)+'-01']/sales)
			else:
				x = lossData.loc[n] * (s.loc[str(n.year)+'-'+str(q+1)+'-01']/sales)
			lm = lm.append(pd.DataFrame(data = np.atleast_2d(x.values), columns = s.columns, index=[str(n.year)+'-'+str(q+1)+'-01']))
	lm.index = pd.to_datetime(lm.index, format = '%Y-%m-%d')
	lm.index.name = 'Date'
	return(lm)

def convertCoalMonthly():
	c = pd.read_csv('EIA_IndCoal2.csv')
	c = c.drop('Unnamed: 0', axis = 1)
	c=c.rename(columns = {'Date':'Quarter'})
	c['Date'] = pd.PeriodIndex(c['Quarter'], freq='Q').to_timestamp()
	c = c.set_index('Date')
	c = c.drop('Quarter', axis = 1)
	c = c.fillna(0)
	c = c*0.02009 # convert from short tons to billion btu

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

def energy_process():
	# load annual total energy consumed
	e = readEnergyData('EIA_IndEnergy.csv', '%Y')
	e = e.loc['2001-01-01':'2018-01-01'] # annual data

	s = readEnergyData('EIA_IndElec.csv', '%Y%m')
	s = s*3.412 # convert to Btu
	s = s.loc['2001-01-01':'2018-12-01'] # monthly data

	l = readEnergyData('EIA_IndElecLosses.csv', '%Y')
	l = l.loc['2001':'2018'] #already in Billion Btu
	lm = correlateElecLosses(l, s)
	
	g = readEnergyData('EIA_IndNG.csv', '%Y%m')
	g = g*1.027 #convert to BTU
	g = g.loc['2001-01-01':'2018-12-01'] # monthly data

	leaseGas = readEnergyData('EIA_LeasePlantNG.csv', '%Y')
	leaseGas = leaseGas*1.027
	plantGas = readEnergyData('EIA_PlantNG.csv', '%Y')
	plantGas = plantGas*1.027

	monthly = s + g + lm

	cm = convertCoalMonthly()
	for x in cm.columns:
		monthly[x] = monthly[x]+cm[x]

	leaseGas = leaseGas.loc['2001-01-01':'2018-01-01'] # annual data
	plantGas = plantGas.loc['2001-01-01':'2018-01-01'] # annual data

	for n in range(len(e.columns)):
		if leaseGas.columns[n] != e.columns[n]:
			if n == 0:
				leaseGas.insert(n, e.columns[n], leaseGas.sum(axis=1))
			else:
				leaseGas.insert(n, e.columns[n], np.zeros(len(leaseGas)))
		if plantGas.columns[n] != e.columns[n]:
			if n == 0:
				plantGas.insert(n, e.columns[n], plantGas.sum(axis=1))
			else: 
				plantGas.insert(n, e.columns[n], np.zeros(len(plantGas)))

	x = e.subtract(leaseGas, fill_value = 0)
	y = x.subtract(plantGas, fill_value = 0)

	#end new 
	percent =  pd.DataFrame(index = e.index, columns = e.columns)
	for n in np.linspace(2001, 2018, 18):
		n = int(n)
		sales = s.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
		losses = l.loc[str(n)+'-01-01']
		gas = g.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
		coal = cm.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0)
		
		combo = sales.add(gas, fill_value = 0)
		combo = combo.add(coal, fill_value = 0)
		combo = combo.add(losses, fill_value = 0)

		print(n, sales.AK, losses.AK, gas.AK, coal.AK, y.loc[str(n)+'-01-01'].AK)

		p = combo/y.loc[str(n)+'-01-01'] # change e to y 
		monthly_avg = (y.loc[str(n)+'-01-01']-combo)/12 #Average total energy not in electricity sales, electricity losses, natural gas, or coal data 
		monthly_avg = np.tile(monthly_avg.values, (12,1))
		monthly[str(n)+'-01-01':str(n)+'-12-01'] = monthly[str(n)+'-01-01':str(n)+'-12-01'] + monthly_avg#+ monthly_avg.values
		for q in y.columns:
			percent[q][str(n)+'-01-01'] = p[q] 
	
	return monthly, percent, y

#Makes plots for Capacity Utilization and Emissions of specified NAICS code, Capacity Utilization vs energy use,
#state energy use accounted by electricity and nat. gas, and state level capacity by NAICS code
def plotData(naics, category, yr):

	#Gets EIA data
    monthly_energy, percent, e = energy_process()

    #Gets FRED, EPA, and BEA data and organizes. Finds overall capacity data for 2018.
    #capacity, emissions, all_fred, _, state_cap = process(naics)
    #all_fred.to_csv(r'/Users/John/Documents/Energy Research/all_capacity.csv')
    overall_cap = pd.read_csv('StateCapacityUtilization.csv')
    print(overall_cap.columns)
    overall_cap.DATE = pd.to_datetime(overall_cap.DATE, format = '%Y-%m-%d')
    overall_cap = overall_cap.set_index('DATE')
    overall_cap = overall_cap.loc['2001-01-01':'2018-12-01']
    stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    #Plots
    #plt.figure(figsize=(5,3))
    #fig1, ax1 = plt.subplots(2)
    #fig1.autofmt_xdate()
    #fig1.suptitle('Industrial Output 2011-2018 for NAICS Code %i' %int(naics[0]), y = .97)

    #ax1[0].plot(capacity.index,capacity.values)
    #ax1[0].set_title('Capacity Utilization')
    #ax1[0].set_ylabel('Percent of Capacity')

    #ax1[1].plot(emissions.index,emissions.values)
    #ax1[1].set_title('Reported Emissions')
    #ax1[1].set_xlabel('Date')
    #ax1[1].set_ylabel('Emissions (kt CO2)')

    #fig1.tight_layout()
    #plt.savefig("Figures/Ind_production.png", dpi=300)
    
    plt.figure(figsize=(6,3))
    fig2, ax2 = plt.subplots()
    fig2.autofmt_xdate()
    fig2.suptitle('2018 National Industrial Capacity Utilization and Energy Use', y = .97)

    annualCap = overall_cap.loc['2018-01-01':'2018-12-01']
    annualMonthlyEnergy = monthly_energy.loc['2018-01-01':'2018-12-01']
    ax2.scatter(annualCap.US.values, annualMonthlyEnergy.US.values)
    ax2.set_xlabel('Percent of Capacity')
    ax2.set_ylabel('Energy Use (Billion Btu)')
    plt.savefig("Figures/Ind_cap_energy.png", dpi=300)
    
    plt.figure(figsize=(25,3))
    fig3, ax3 = plt.subplots()
    fig3.suptitle('2018 Percentage of Energy Use from Electricity and Natural Gas by State', y = .95)
    p = percent.loc['2018-01-01']
    ax3.bar(np.linspace(1,52,52), p.values)
    ax3.set_xlabel('State')
    ax3.set_ylabel('Percent of Total Energy')
    plt.xticks(ticks = np.linspace(2,52, 51), labels = stateCodes[1:], rotation = 90, fontsize = 6)
    plt.savefig("Figures/State_sales_gas.png", dpi=300)

    plt.figure(figsize=(5,3))
    fig4, ax4 = plt.subplots()
    fig4.suptitle('2018 Total Industrial Energy Consumed by State', y = .95)
    b = e.loc['2018-01-01'].values
    #cols = e.columns
    ax4.bar(np.transpose(np.linspace(1,51,51)), b[1:])
    plt.xticks(ticks = np.linspace(1,51,51), labels = e.columns[1:], rotation = 90, fontsize = 6)
    plt.xlim(0.5, 50.5)
    plt.savefig("Figures/State_cap.png", dpi=300)

    # scatter plot of monthly energy vs capacity utilization: monthly energy data starts at 2001 and goes through 2018
    stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    for s in range(50):
    	plt.figure()
    	state = stateCodes[s+1]
    	for y in np.linspace(2014, 2018, 5):
    	#plt.subplot(5,5,s+1)
    		m = monthly_energy[state].loc[str(int(y))+'-01-01':str(int(y))+'-12-01']
    		plt.scatter(overall_cap[state].loc[str(int(y))+'-01-01':str(int(y))+'-12-01'], m)
    	#plt.legend(('2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018'))
    	plt.legend(('2014', '2015', '2016', '2017', '2018'))
    	plt.xlim(50,100)
    	#plt.ylim(ymin = 0)
    	#plt.ylim(0,1.5)
    	plt.ylabel('Industrial Energy Consumption [Btu]')
    	plt.xlabel(state + ' Industrial Capacity Utilization')
    	#plt.ylim(0, 200000)
    	plt.savefig('Figures/States/states_capacity_scatter'+state+'.png', dpi=300)
    	plt.close()

#Checks if NAICS codes match in FRED and EPA data
def codecheck(naics):

    _, _, _, all_fred, all_epa = process(naics)
    #print(all_fred)
    fr_code = all_fred.index.tolist()
    epa_code = all_epa.index.tolist()

    unmatched = []
    for id in epa_code:
         if id not in fr_code and id not in unmatched:
             unmatched.append(id)
    unmatched.sort()
    return unmatched



naics = [321] #Selects the Naics code to use. 321 is Naics code for wood product manufacturing
category = [40211,1004,480691] #EIA Category IDs for Total Industrial Energy, Industrial electricity sales,
#and Industrial natural gas consumption
plotData(naics, category, '2018')

def monthlyToAnnual(d):
	da = pd.DataFrame()
	for n in d.index.year.unique():
		x = d.loc[str(n)+'-01-01':str(n)+'-12-01'].sum(axis=0).values
		da = da.append(pd.DataFrame(data = np.atleast_2d(x), columns = d.columns, index = [str(n)+'-01-01']))
	da.index = pd.to_datetime(da.index, format = '%Y-%m-%d')
	da.index.name = 'Date'
	return(da)

def plotPercentages():
	e = readEnergyData('EIA_IndEnergy.csv', '%Y') # total energy annual
	l = readEnergyData('EIA_IndElecLosses.csv', '%Y') #annual electricity losses already in billion Btu
		
	s = readEnergyData('EIA_IndElec.csv', '%Y%m') # monthly electricity sales
	s = s*3.412 # convert to Btu 
	g = readEnergyData('EIA_IndNG.csv', '%Y%m') # monthly natural gas sales
	g = g*1.027 #convert to BTU
	cm = convertCoalMonthly() #monthly coal consumption 

	leaseGas = readEnergyData('EIA_LeasePlantNG.csv', '%Y')
	leaseGas = leaseGas*1.027
	plantGas = readEnergyData('EIA_PlantNG.csv', '%Y')
	plantGas = plantGas*1.027

	sa = monthlyToAnnual(s)
	ga = monthlyToAnnual(g)
	c = monthlyToAnnual(cm)

	

	e = e.loc['2001-01-01':'2018-01-01']
	l = l.loc['2001-01-01':'2018-01-01']
	sa = sa.loc['2001-01-01':'2018-01-01']
	ga = ga.loc['2001-01-01':'2018-01-01']

	leaseGas = leaseGas.loc['2001-01-01':'2018-01-01']
	plantGas = plantGas.loc['2001-01-01':'2018-01-01']
	print('e', e.columns, 'l', l.columns, 'sa', sa.columns, 'ga', ga.columns, 'c', c.columns, leaseGas.columns, plantGas.columns)

	print(e.index.year.unique(), l.index.year.unique(), sa.index.year.unique(), ga.index.year.unique(), c.index.year.unique())

	for n in range(len(e.columns)):
		if leaseGas.columns[n] != e.columns[n]:
			if n == 0:
				leaseGas.insert(n, e.columns[n], leaseGas.sum(axis=1))
			else:
				leaseGas.insert(n, e.columns[n], np.zeros(len(leaseGas)))
		if plantGas.columns[n] != e.columns[n]:
			if n == 0:
				plantGas.insert(n, e.columns[n], plantGas.sum(axis=1))
			else: 
				plantGas.insert(n, e.columns[n], np.zeros(len(plantGas)))
	
	#leaseGas.insert(0, "US", np.zeros(len(leaseGas)))
	#leaseGas.insert()

	x = e.subtract(leaseGas, fill_value = 0)
	print(x.columns)
	#print(x.loc['2018-01-01'])
	#print(x)
	
	y = x.subtract(plantGas, fill_value = 0)
	#print(y) # adjusted total 

	#z = y.subtract(l, fill_value = 0)
	#print(z)

	monthlyCombo = sa.add(ga, fill_value = 0)
	#combo = sa.add(ga, fill_value = 0)
	#combo = combo.add(l, fill_value = 0)
	#combo = combo.add(c, fill_value = 0)

	#print(combo)
	#diff = combo/y #total energy 

	#print(diff)
	yr = 2018
	print(monthlyCombo.tail(), l.tail(), c.tail(), y.tail())
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
	plt.figure(figsize=(25,3))
	
	fig3, ax3 = plt.subplots()
	fig3.suptitle('2018 Percentage of Energy Accounted for', y = .95)
	#p = diff.loc['2018-01-01']
	ax3.bar(np.linspace(1,52,52), (monthlyCombo.loc['2018-01-01']/y.loc['2018-01-01']).values)
	ax3.bar(np.linspace(1,52,52), (l.loc['2018-01-01']/y.loc['2018-01-01']).values, bottom = (monthlyCombo.loc['2018-01-01']/y.loc['2018-01-01']).values)
	ax3.bar(np.linspace(1,52,52), (c.loc['2018-01-01']/y.loc['2018-01-01']).values, bottom = ((monthlyCombo.loc['2018-01-01']+l.loc['2018-01-01'])/y.loc['2018-01-01']).values)
	#ax3.bar(np.linspace(1,51,51), p.values)
	ax3.set_xlabel('State')
	ax3.set_ylabel('Percent of Total Energy')
	plt.xticks(ticks = np.linspace(1,52, 52), labels = stateCodes, rotation = 90, fontsize = 6)
	plt.savefig("Figures/State_percentageAccounted.png", dpi=300)

def runCorrelationChecks():
	monthly_energy, percent, e = energy_process()
	overall_cap = pd.read_csv('StateCapacityUtilization.csv')
	overall_cap.DATE = pd.to_datetime(overall_cap.DATE, format = '%Y-%m-%d')
	overall_cap = overall_cap.set_index('DATE')
	overall_cap = overall_cap.loc['2001-01-01':'2018-12-01']
	stateCodes = ['US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NY', 'NC','ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
	# pearson correlation
	for n in range(50):
		state = stateCodes[n+1]
		o = overall_cap.loc['2014-01-01':'2018-12-01']
		m = monthly_energy.loc['2014-01-01':'2018-12-01']
		pear = stats.pearsonr(o[state], m[state])
		ken = stats.kendalltau(o[state], m[state], initial_lexsort=True)
		rho, pval = stats.spearmanr(o[state], m[state])
		#print(state, rho, pval)
		if pval>0.1:
			print(state, rho, pval)

#plotPercentages()
#print(monthly_energy['DC'])
runCorrelationChecks()
