
import numpy as np
import pandas as pd
from matplotlib.mlab import griddata
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from EventStationDataGenerator import generate_events


def generate_figure():
    # set up plot
    plt.clf()
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, axisbg='w', frame_on=False)
    norm = Normalize()
    lllon = min(longitudeValues) - 1
    lllat = min(latitudeValues) - 1
    urlon = max(longitudeValues) + 1
    urlat = max(latitudeValues) + 1
    scale_min = min(magnitudeValues)
    scale_max = max(magnitudeValues)

    # Set up Basemap instance
    m = Basemap(
        projection = 'merc',
        llcrnrlon = lllon, llcrnrlat = lllat, urcrnrlon = urlon, urcrnrlat = urlat,
        resolution='h')

    # transform lon / lat coordinates to map projection
    projected_lon, projected_lat = m(*(longitudeValues, latitudeValues))

    # grid data
    numcols, numrows = 1000, 1000
    xi = np.linspace(min(projected_lon), max(projected_lon), numcols)
    yi = np.linspace(min(projected_lat), max(projected_lat), numrows)
    xi, yi = np.meshgrid(xi, yi)

    # interpolate
    x, y, z = projected_lon, projected_lat, magnitudeValues
    zi = griddata(x, y, z, xi, yi, interp='linear')

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
        projected_lon,
        projected_lat,
        color='#000054',
        edgecolor='#fffddf',
        alpha=.75,
        s=100 * norm(magnitudeValues),
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
    #plt.show()


def generate_event_contours(sc, eventList, stationMagnitudes):
    global magnitudeValues
    global longitudeValues
    global latitudeValues
    magnitudeValues = []
    longitudeValues = []
    latitudeValues = []
    out_res = generate_events(sc, eventList)
    for each_entry in out_res:
        stationMagnitudes.append(out_res.split())

    for each_station in stationMagnitudes:
        if each_station[0] not in eventList:
            continue
        magnitudeValues.append(float(each_station[4]))
        latitudeValues.append(float(each_station[2]))
        longitudeValues.append(float(each_station[3]))
    generate_figure()


'''def main():
    eventList = [4768129]
    stationMagnitudes = [[4768129,'CI.USC',34.55,-117.43,6.79828624427],[4768129,'CI.BAR',33.55,-118.43,5.40686620848],\
                         [4768129,'UU.BYP',40.86,-112.18,8.0669225385]]
    generate_event_contours(eventList, stationMagnitudes)

if __name__ == "__main__":
    main()'''



