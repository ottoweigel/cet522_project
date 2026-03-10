# seattle_geo = load_geo_data("https://drive.google.com/uc?export=view&id=172kqatuR-BAc9LqpkkpFq8o7DB1bO3t0")
# st.write('## Seattle Roads', seattle_geo.plot())

import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="Micromobility Explorer",
    page_icon="🛴",
    layout="wide",
)

st.title("Micromobility Explorer 🛴 🗺️ 🔭")
st.caption("Explore micromobility in Seattle and Spokane!")

# ----------------------------
# Data loading
# ----------------------------
@st.cache_data
def load_data_from_path(path):
    df = pd.read_csv(path)
    return  (df)

@st.cache_data
def load_geodata_from_path(path):
    gdf = gpd.read_file(path)
    return  (gdf)

@st.cache_data
def _prepare_data(df):
    return "hi"

CENSUS_DATA = load_geodata_from_path("census_data.geojson") # includes count data already
GRID_DATA = load_geodata_from_path("grid_data.geojson") # includes count data already
seattle_micro_streets = load_geodata_from_path("seattle-routes-data-for-all-vehicles-in-all-time.geojson").dropna(subset=["count"])
spokane_micro_streets = load_geodata_from_path("spokane-routes-data-for-all-vehicles-in-all-time.geojson").dropna(subset=["count"])

# ----------------------------
# Sidebar controls
# ----------------------------
st.sidebar.header("Filters")

all_cities = ("Seattle", "Spokane")
agg_city = st.sidebar.multiselect(
    "Select cities:",
    options=all_cities,
    default=all_cities,
)
agg_map = st.sidebar.selectbox("Analysis Unit:", ["Census", "Grid",], index=0)

# ----------------------------
# Top info + KPI cards
# ----------------------------
col1, col2, col3, col4, col5, col6 = st.columns(6)

# total_vehicles = int(filtered["Vehicles"].sum())
# avg_vehicles = float(filtered["Vehicles"].mean())
# peak_row = filtered.loc[filtered["Vehicles"].idxmax()]
# busiest_junction = filtered.groupby("Junction")["Vehicles"].sum().idxmax()

col1.metric("Seattle, Average Micromobility Count", f"{seattle_micro_streets["count"].mean():,.0f}")
col2.metric("Spokane, Average Micromobility Count", f"{spokane_micro_streets["count"].mean():,.0f}")
# TODO FINISH THESE NUMBERS after adding the census filters for the streets
col3.metric("Seattle, Number of Census Tracks", f"{0.0:,.0f}")
col4.metric("Spokane, Number of Census Tracks", f"{0.0:,.0f}")

# ----------------------------
# Tabs
# ----------------------------
tab1, tab2, tab3 = st.tabs(["Maps", "ML Model", "Data and Summary",])

with tab1:
    st.subheader("Visualize those maps!")
    
    def make_map_from(midpoint, value, title, df):
        m = folium.Map(location=midpoint, zoom_start=9)
        
        folium.Choropleth(
            geo_data=df.dropna(subset=value),
            data=df,
            columns=[df.index, value],
            key_on="feature.id",
            fill_color="YlOrRd",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=title
        ).add_to(m)
        st_folium(m, width=800, height=550, key=city+"_map")
    
    def get_city_id(city_name):
        match city_name:
            case "Seattle":
                return "033"
            case "Spokane":
                return "063"
            case _:
                return "no id implemented"

    if (agg_map == "Grid"):
        data = GRID_DATA
    else:
        data = CENSUS_DATA
    
    # map it!
    if (agg_city):
        for city in agg_city:

            filtered_data = data[data["COUNTYFP"]==get_city_id(city)]
            
            minx, miny, maxx, maxy = filtered_data.total_bounds
            midpoint = [(miny + (maxy-miny)/2), (minx + (maxx-minx)/2)]
            st.write(midpoint)
            
            make_map_from(midpoint, "max_count", "title", filtered_data)
            
    else:
        st.write("No city is selected for analysis!")

with tab2:
    st.subheader("Lets see that ML Model!")
    # TODO by Otto

with tab3:
    st.subheader("Here's a summary!")
    # TODO by Deegan

    st.write(CENSUS_DATA.head())