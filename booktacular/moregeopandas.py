'''
Requires:
pip3 install pandas geopandas shapely pyarrow

"Pyarrow will become a required dependency of pandas in the next major
release of pandas (pandas 3.0), (to allow more performant data types,
such as the Arrow string type, and better interoperability with other
libraries)"
-pandas
'''
import os
import sys
import logging
# from collections import OrderedDict
# See <https://stackoverflow.com/a/53233489/4541104> (answered by Xiaoyu Lu)
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame
import matplotlib.pyplot as plt
from adjustText import adjust_text

from booktacular.irlmapping import clean_coords

logger = logging.getLogger(__name__)

# Importing urllib based on Python version
if sys.version_info.major >= 3:
    import urllib.request
    request = urllib.request
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse, parse_qs, quote as urllib_quote, quote_plus as urllib_quote_plus, urlencode
else:
    import urllib2 as urllib  # type: ignore
    request = urllib
    from urllib2 import HTTPError, URLError  # type: ignore
    from HTMLParser import HTMLParser  # noqa: F401 # type: ignore
    from urlparse import urlparse, parse_qs  # noqa: F401 # type: ignore
    from urllib import quote as urllib_quote  # noqa: F401 # type: ignore
    from urllib import quote_plus as urllib_quote_plus  # noqa: F401,E501 # type: ignore
    from urllib import urlencode  # noqa: F401 # type: ignore
    print("HTMLParser imported.", file=sys.stderr)

# URL to download Natural Earth dataset
NATURAL_EARTH_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
NATURAL_EARTH_PATH = os.path.join(os.getcwd(), "ne_110m_admin_0_countries.zip")

def download_natural_earth():
    """Download the Natural Earth dataset if it doesn't exist locally."""
    if not os.path.exists(NATURAL_EARTH_PATH):
        print("Downloading Natural Earth dataset...")
        try:
            response = request.urlopen(NATURAL_EARTH_URL)
            with open(NATURAL_EARTH_PATH, "wb") as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
            print("Download completed.")
        except (HTTPError, URLError) as e:
            print(f"Failed to download dataset: {e}", file=sys.stderr)
            sys.exit(1)


def generate_map(waypoints_path):
    """Generate a map from a CSV file, avoiding overlapping text labels.
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

    # Ensure the Natural Earth dataset is available
    download_natural_earth()

    # Load world boundaries from Natural Earth dataset
    world = gpd.read_file(f"zip://{NATURAL_EARTH_PATH}")

    coords_df = pd.read_csv(waypoints_path, delimiter=',', skiprows=0,
                            low_memory=False)
    pairs, longs, lats, cities, names = [], [], [], [], []
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

        if isinstance(old_name, str) and "(skip)" in old_name:
            print(f"* skipped OldName=\"{old_name}\"")
            continue
        if not isinstance(name, str):
            print(f"* name={type(name).__name__}({name})=\"_____\"")
            name = "_____"
        try:
            coords = clean_coords(_raw) if isinstance(_raw, str) else None
        except ValueError as ex:
            coords = "ValueError: {}".format(ex)
        if coords and len(coords) in [2, 3]:
            coords = coords[:2]
        else:
            logger.warning(f"  skipped ModernCoords={type(_raw).__name__}({_raw})")
            continue

        pairs.append(coords)
        lats.append(coords[0])
        longs.append(coords[1])
        cities.append(modern_name)
        names.append(name)
        count += 1

    coords_df = pd.DataFrame({
        "Name": cities,
        "Latitude": lats,
        "Longitude": longs,
    })

    geometry = [Point(xy) for xy in zip(longs, lats)]
    gdf = GeoDataFrame(coords_df, geometry=geometry)

    # Plot world map with waypoints
    ax = world.plot(figsize=(10, 6))
    gdf.plot(ax=ax, marker='o', color='red', markersize=15)

    # Avoid overlapping text by adjusting positions
    texts = []
    for idx, row in coords_df.iterrows():
        text = ax.text(row['Longitude'], row['Latitude'], row['Name'], fontsize=8)
        texts.append(text)

    # Use adjust_text to prevent overlaps
    adjust_text(texts, arrowprops=dict(arrowstyle="->", color='gray', lw=0.5))

    plt.show()
