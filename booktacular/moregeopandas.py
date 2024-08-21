'''
Requires:
pip3 install pandas geopandas shapely pyarrow

"Pyarrow will become a required dependency of pandas in the next major
release of pandas (pandas 3.0), (to allow more performant data types,
such as the Arrow string type, and better interoperability with other
libraries)"
-pandas
'''
# import sys
import logging

# from collections import OrderedDict
# See <https://stackoverflow.com/a/53233489/4541104> (answered by Xiaoyu Lu)
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame
import matplotlib.pyplot as plt


from booktacular.irlmapping import (
    clean_coords,
)

logger = logging.getLogger(__name__)


def generate_map(waypoints_path):
    """Generate a map from a CSV file.
    The Zah Yest research CSV file has:
    Name for Campaign,Old Name (? for skip),ModernName,
    DescURL,LocationURL,AncientContinent,ModernCoords,LocationDesc,
    Description


    Args:
        waypoints_path (str): A CSV file with coordinates in various
            formats in the ModernCoords column.

    Raises:
        NotImplementedError: clean_coords returned an unexpected number
            of coords (expected 2 or 3).
    """
    # coords_path = "Long_Lats.csv"
    # with open(waypoints_path, 'r') as ins:
    coords_df = pd.read_csv(waypoints_path, delimiter=',', skiprows=0,
                            low_memory=False)
    # with open(coords_path, 'w') as outs:
    pairs = []
    longs = []
    lats = []
    cities = []
    names = []
    max = None
    skip = None
    count = 0
    for index, row in coords_df.iterrows():
        if max and len(cities) >= max:
            break
        _raw = row['ModernCoords']
        modern_name = row['ModernName']
        name = row['CustomName']
        old_name = row['OldName']
        if isinstance(old_name, str):
            if "(skip)" in old_name:
                print("* skipped OldName=\"{}\"".format(old_name))
                continue
        # if (not name) or (name == float('nan')):
        if not isinstance(name, str):
            print("* name={}({})=\"_____\"".format(type(name).__name__, name))
            name = "_____"
        else:
            print("* name={}({})".format(type(name).__name__, name))
        coords = None
        if not isinstance(_raw, str):
            # raise TypeError("Expected str got {}({})"
            #                 .format(type(coords).__name__, coords))
            logger.warning("  skipped ModernCoords={}({})"
                           .format(type(_raw).__name__, _raw))
            continue
        try:
            coords = clean_coords(_raw)
        except ValueError:
            logger.warning("  skipped ModernCoords=\"{}\"".format(_raw))
            continue
        # elevation = None
        if len(coords) == 3:
            # elevation = coords[2]
            coords = coords[:2]
        elif len(coords) != 2:
            raise NotImplementedError(
                "Expected 2 or 3 (N,E,[,elevation]) coords,"
                " got {}".format(coords))
        if skip is not None and count == skip:
            count += 1
            continue
        print("  {}={}".format(modern_name, coords))
        pairs.append(coords)
        lats.append(coords[0])
        longs.append(coords[1])
        cities.append(modern_name)
        names.append(name)
        count += 1
    # return 0
    # coords_df.insert(0, 'Longitude', longs, True)
    # coords_df.insert(1, 'Latitude', lats, True)
    # coords_df = pd.DataFrame(lists)
    # coords_df.to_csv(coords_path, index=False)

    # Fields: See docstring.
    coords_df = pd.DataFrame({
        # "Name": names,
        "Name": cities,
        "Latitude": lats,
        "Longitude": longs,
    })

    # coords_df = pd.read_csv(coords_path, delimiter=',', skiprows=0,
    #   low_memory=False)

    # geometry = \
    # [Point(xy) for xy in zip(coords_df['Longitude'], coords_df['Latitude'])]
    geometry = [Point(xy) for xy in zip(longs, lats)]  # switch them!
    gdf = GeoDataFrame(coords_df, geometry=geometry)

    # this is a simple map that goes with geopandas
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    result = gdf.plot(ax=world.plot(figsize=(10, 6)), marker='o', color='red',
                      markersize=15)
    for idx, dat in coords_df.iterrows():
        # print(dat.city, dat.lng, dat.lat)
        # result.scatter(dat.Longitude, dat.Latitude, s=10, color='red')
        result.annotate(dat.Name, (dat.Longitude, dat.Latitude))

    plt.show()
