import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt 

d = pd.read_csv('Data/MCUMFN.csv')
d.DATE = pd.to_datetime(d.DATE)
d = d.set_index('DATE')

x = d.loc['2010-01-01':'2018-12-01']
print(np.average(x.MCUMFN))

d2 = pd.read_csv('Data/INDPRO.csv')
d2.DATE = pd.to_datetime(d2.DATE)
d2 = d2.set_index('DATE')

a = d.tail(1).index.format()
r1 = ['1973-11-01',  '1980-01-01', '1981-07-01', '1990-07-01', '2001-03-01', '2007-12-01', '2020-02-01']
r2 = ['1975-03-01', '1980-07-01', '1982-11-01', '1991-03-01', '2001-11-01', '2009-06-01']
r2.append(a[0])

r = pd.DataFrame(({'Start': r1, 'End': r2}))
r.Start = pd.to_datetime(r.Start)
r.End = pd.to_datetime(r.End)


plt.figure(figsize=(6,2))
ax = plt.subplot(position = [0.08, 0.18, 0.8, 0.75])
plt.plot(d.index, d.MCUMFN)
plt.plot(d2.index, d2.INDPRO)
for n in range(len(r)):
	plt.fill_between([r.Start[n], r.End[n]], [0,0], [120,120], facecolor = [0.5, 0.5, 0.5], alpha = 0.5)
plt.xlabel('Year', fontsize = 8)
plt.text('2020-06-01', d.MCUMFN[-1], 'Capacity\nUtilization', color = 'C0', fontsize = 8, verticalalignment = 'center')
plt.text('2020-06-01', d2.INDPRO[-1], 'Indexed\nProduction\n2012=100', color = 'C1', fontsize = 8, verticalalignment = 'center')
#plt.ylabel('Monthly Manufacturing\nCapacity Utilization', fontsize = 8)
plt.ylim(0, 120); plt.yticks(fontsize = 8)
plt.xticks(fontsize = 8); plt.xlim(d.head(1).index, '2020-01-01')

plt.savefig('Figures/Fig1MonthlyMfgCapacityDataFRED.png')

#calculate average output from 2010-2018 
print('Average from 2010-end of 2018', np.average(d.loc['2010-01-01':'2018-12-01'].MCUMFN))