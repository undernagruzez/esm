import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from folium import plugins
from scipy.spatial import distance_matrix

if __name__ == "__main__":

    data_STA = pd.read_csv('data/no2/stachus.csv', delimiter=';', header=None)
    data_LHA = pd.read_csv('data/no2/landshuter_allee.csv', delimiter=';', header=None)
    data_LOT = pd.read_csv('data/no2/lothstrasse.csv', delimiter=';', header=None)
    data_JOH = pd.read_csv('data/no2/johanneskirchen.csv', delimiter=';', header=None)
    data_ALL = pd.read_csv('data/no2/allach.csv', delimiter=';', header=None)

    for data in [data_STA, data_LHA, data_LOT, data_JOH, data_ALL]:
        data[0] = pd.to_datetime(data[0] + ' ' + data[1], format="%d.%m.%Y %H:%M")

    avg_STA = data_STA[2].mean()
    avg_LHA = data_LHA[2].mean()
    avg_LOT = data_LOT[2].mean()
    avg_JOH = data_JOH[2].mean()
    avg_ALL = data_ALL[2].mean()

    # Define coordinates for each station
    coord_STA = (48.13732, 11.56481)
    coord_LHA = (48.14955, 11.53653)
    coord_LOT = (48.15455, 11.55466)
    coord_JOH = (48.17319, 11.64804)
    coord_ALL = (48.18165, 11.46444)

    # Calculate average coordinate as the center of the 20km x 20km area
    center_lat = np.mean([coord_STA[0], coord_LHA[0], coord_LOT[0], coord_JOH[0], coord_ALL[0]])
    center_lon = np.mean([coord_STA[1], coord_LHA[1], coord_LOT[1], coord_JOH[1], coord_ALL[1]])


    # Define the coordinates and average concentrations of the stations
    stations = np.array([coord_STA, coord_LHA, coord_LOT, coord_JOH, coord_ALL])
    avg_concentrations = np.array([avg_STA, avg_LHA, avg_LOT, avg_JOH, avg_ALL])

    grid_size = 20  # km
    resolution = 1  # km
    n_points = int(grid_size / resolution)

    # Create the grid
    grid_lats = np.linspace(center_lat - grid_size / 2 / 111.2, center_lat + grid_size / 2 / 111.2, n_points)
    grid_lons = np.linspace(center_lon - grid_size / 2 / (111.2*np.cos(np.radians(center_lat))), center_lon + grid_size / 2 / (111.2*np.cos(np.radians(center_lat))), n_points)
    grid_lats, grid_lons = np.meshgrid(grid_lats, grid_lons)
    grid = np.dstack((grid_lats, grid_lons)).reshape(-1, 2)

    distances = distance_matrix(grid, stations) * 111.2  # convert degrees to km

    # Calculate the weights for the IDW interpolation
    weights = 1.0 / distances

    # Handle division by zero (if a grid point is exactly at a station location)
    weights[weights == np.inf] = np.nan

    estimated_concentrations = np.nansum(weights * avg_concentrations, axis=1) / np.nansum(weights, axis=1)
    estimated_concentrations = estimated_concentrations.reshape((n_points, n_points))


    m = folium.Map(location=[center_lat, center_lon],tiles='cartodbdark_matter', zoom_start=30)


    # Create a list of [lat, lon, value] for each point in the grid
    heatmap_data = [[grid_lats[i, j], grid_lons[i, j], estimated_concentrations[i, j]]
                    for i in range(n_points) for j in range(n_points)]


    plugins.HeatMap(heatmap_data, radius=0).add_to(folium.FeatureGroup(name='Heat Map').add_to(m))
    folium.LayerControl().add_to(m)

    # normalize estimated_concentrations between 0 and 1
    normed_conc = (estimated_concentrations - np.min(estimated_concentrations)) / (np.max(estimated_concentrations) - np.min(estimated_concentrations))

    # Create a colormap
    cmap = plt.get_cmap("YlOrRd")

    colored_conc = cmap(normed_conc)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # Add the colored concentration data as an image overlay
    img = folium.raster_layers.ImageOverlay(
        image=colored_conc,
        bounds=[[np.min(grid_lats), np.min(grid_lons)], [np.max(grid_lats), np.max(grid_lons)]],
        opacity=0.6,
        pixelated=True
    )
    img.add_to(m)

    station_names = [
        "Stachus",
        "Landshuter Allee",
        "Lothstrasse",
        "Johanneskirchen",
        "Allach"
    ]

    # Add markers for each station with station names as popups
    for station, avg_concentration, station_name in zip(stations, avg_concentrations, station_names):
        lat, lon = station
        popup_text = f"{station_name} - Average NO2 Concentration: {avg_concentration:.2f} ppb"
        folium.Marker(location=[lat, lon], popup=popup_text).add_to(m)

    map_filename = "output_map.html"
    m.save(map_filename)

    fig, ax = plt.subplots(figsize=(20, 20))
    cmap = plt.get_cmap("YlOrRd")
    colored_conc = cmap(estimated_concentrations)

    plt.imshow(estimated_concentrations, cmap=cmap, extent=[
        np.min(grid_lons) - 0.005,
        np.max(grid_lons) + 0.005,
        np.min(grid_lats) - 0.005,
        np.max(grid_lats) + 0.005
    ])
    plt.colorbar(label="NO2 Concentration (ppb)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("NO2 Concentration Heatmap")

    for i in range(n_points):
        for j in range(n_points):
            lat, lon = grid_lats[i, j], grid_lons[i, j]
            concentration = estimated_concentrations[i, j]
            plt.text(lon, lat, f"{concentration:.2f}", ha='center', va='center', fontsize=8, color='black')

    heatmap_filename = "heatmap.png"
    plt.savefig(heatmap_filename, dpi=300, bbox_inches="tight")
    plt.close()