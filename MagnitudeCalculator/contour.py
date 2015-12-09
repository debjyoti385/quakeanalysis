import numpy as np
import pandas as pd
from matplotlib.mlab import griddata
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
#matplotlib inline

# set up plot
plt.clf()
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, axisbg='w', frame_on=False)

# grab data
data = pd.read_csv('out', sep=',')
norm = Normalize()

# define map extent
# EventID,NETSTATIONID,LATITUDE,LONGITUDE,MAGNITUDE

lllon = min(data.LONGITUDE.values) - 1
lllat = min(data.LATITUDE.values) - 1
urlon = max(data.LONGITUDE.values) + 1
urlat = max(data.LATITUDE.values) + 1 

scale_min = min(data.MAGNITUDE.values)
scale_max = max(data.MAGNITUDE.values)

# Set up Basemap instance
m = Basemap(
    projection = 'merc',
    llcrnrlon = lllon, llcrnrlat = lllat, urcrnrlon = urlon, urcrnrlat = urlat,
    resolution='h')

# transform lon / lat coordinates to map projection
data['projected_lon'], data['projected_lat'] = m(*(data.LONGITUDE.values, data.LATITUDE.values))

# grid data
numcols, numrows = 1000, 1000
xi = np.linspace(data['projected_lon'].min(), data['projected_lon'].max(), numcols)
yi = np.linspace(data['projected_lat'].min(), data['projected_lat'].max(), numrows)
xi, yi = np.meshgrid(xi, yi)

# interpolate
x, y, z = data['projected_lon'].values, data['projected_lat'].values, data.MAGNITUDE.values
zi = griddata(x, y, z, xi, yi)

# draw map details
m.drawmapboundary(fill_color = '#3f6077')
m.fillcontinents(color='#ffbfa7', lake_color='#7093DB')
m.drawcountries(
    linewidth=.75, linestyle='solid', color='#000073',
    antialiased=True,
    ax=ax, zorder=3)

m.drawparallels(
    np.arange(lllat, urlat, 2.),
    color = 'black', linewidth = 0.5,
    labels=[True, False, False, False])
m.drawmeridians(
    np.arange(lllon, urlon, 2.),
    color = '0.25', linewidth = 0.5,
    labels=[False, False, False, True])

levels = np.linspace(scale_min,scale_max ,20)
# contour plot
con = m.contourf(xi, yi, zi, zorder=4, alpha=0.6, cmap='RdPu', levels=levels)
# scatter plot
m.scatter(
    data['projected_lon'],
    data['projected_lat'],
    color='#000054',
    edgecolor='#fffddf',
    alpha=.75,
    s=100 * norm(data['MAGNITUDE']),
    cmap='RdPu',
    ax=ax,
    vmin=zi.min(), vmax=zi.max(), zorder=10)

# add colour bar and title
# add colour bar, title, and scale
cbar = plt.colorbar(con, orientation='vertical', fraction=.057, pad=0.05)
cbar.set_label("Richter Scale - Mw")

m.drawmapscale(
    24., -9., 28., -13,
    100,
    units='km', fontsize=10,
    yoffset=None,
    barstyle='fancy', labelstyle='simple',
    fillcolor1='w', fillcolor2='#000000',
    fontcolor='#000000',
    zorder=5)

plt.title("Earthquake Contour Map")
plt.savefig("contour.png", format="png", dpi=300, transparent=True)
plt.show()
