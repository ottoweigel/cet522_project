# seattle_geo = load_geo_data("https://drive.google.com/uc?export=view&id=172kqatuR-BAc9LqpkkpFq8o7DB1bO3t0")
# st.write('## Seattle Roads', seattle_geo.plot())

import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import matplotlib.colors as mcolors
import branca.colormap as cm


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
col1, col2, col3, col4 = st.columns(4)

col1.metric("Seattle, Average Micromobility Count", f"${seattle_micro_streets["count"].mean():,.0f}")
col2.metric("Spokane, Average Micromobility Count", f"${spokane_micro_streets["count"].mean():,.0f}")

king_county_tract_num = (CENSUS_DATA["COUNTYFP"]=="033").sum()
spokane_county_track_num = (CENSUS_DATA["COUNTYFP"]=="063").sum()
col3.metric("KING COUNTY, Number of Census Tracks", f"{king_county_tract_num:,.0f}")
col4.metric("SPOKANE COUNTY, Number of Census Tracks", f"{spokane_county_track_num:,.0f}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("City of Seattle, Median Income", "$123,860")
col6.metric("City of Spokane, Median Income", "$86,206")

# ----------------------------
# Tabs
# ----------------------------
tab1, tab2, tab3 = st.tabs(["Visualizing Data with Maps", "Machine Learning and Regression", "Summary",])

# selects data frame for analysis
if (agg_map == "Grid"):
    data = GRID_DATA
else:
    data = CENSUS_DATA

if list(set(["POP_DENSITY_aw", "log_POP_DENSITY_aw", 'MED_HH_INCOME_aw']) & set(data.columns)):
    data.rename(columns={"POP_DENSITY_aw":"POP_DENSITY", "log_POP_DENSITY_aw":"log_POP_DENSITY", "MED_HH_INCOME_aw":"MED_HH_INCOME"}, inplace=True)

# ----------------------------
# Tab 1
# ----------------------------
with tab1:
    # make a map from variables
    def make_map_from(value, title, df):
        minx, miny, maxx, maxy = df.total_bounds
        m = folium.Map(location=[((maxy+miny)/2), ((maxx+minx)/2)], zoom_start=9)
        m.fit_bounds([[miny, minx], [maxy, maxx]])
        
        folium.Choropleth(
            geo_data=df.dropna(subset=value),
            data=df,
            columns=[df.index, value],
            key_on="feature.id",
            fill_color="YlGnBu",
            fill_opacity=0.7,
            line_opacity=0.2,
            #legend_name=title TODO add title to all that revence this?
        ).add_to(m)

        st_folium(m, width=600, height=550, key=str(df.count())+"_map")

    # make a line map from variables
    def make_line_map_from(value, title, df):
        minx, miny, maxx, maxy = df.total_bounds
        m = folium.Map(location=[((maxy+miny)/2), ((maxx+minx)/2)], zoom_start=9)
        m.fit_bounds([[miny, minx], [maxy, maxx]]) 

        cmap = cm.LinearColormap(
            colors=["#440154", "#31688e", "#35b779", "#fde725"],
            vmin=df[value].min(), vmax=df[value].max()
        )
        folium.GeoJson(
            df.to_crs(4326),
            style_function=lambda f: {
                "color": cmap(f["properties"][value]),
                "weight": 4,
                "opacity": 0.9
            }
        ).add_to(m)
        cmap.add_to(m)

        st_folium(m, width=600, height=550, key=str(df.count())+"_map")
        
    
    # gets tract id from city name
    def get_city_id(city_name):
        match city_name:
            case "Seattle":
                return "033"
            case "Spokane":
                return "063"
            case _:
                return "no id implemented"
    

    st.subheader("Let's visualize data with maps!")
    c11, c12 = st.columns(2)
    if (agg_city):
        # ----------------------------
        # MAPS OF the street data
        # ----------------------------
        with c11:
            st.subheader("Visualize the Micromobility Counts by Segment")
            #TODO ADD switch for log values
            min_percent = st.slider("Minimum percent of max count to show:", 0, 100, 10)
            for city in agg_city:
                if ("Seattle" == city):
                    max = seattle_micro_streets["count"].max()
                    make_line_map_from("count", "title", seattle_micro_streets[seattle_micro_streets["count"]>max*(min_percent/100.0)])
                if ("Spokane" == city):
                    max = spokane_micro_streets["count"].max()
                    make_line_map_from("count", "title", spokane_micro_streets[spokane_micro_streets["count"]>max*(min_percent/100.0)])


        # ----------------------------
        # MAPS OF the census/grid data
        # ----------------------------
        with c12:
            st.subheader("Visualize a variable on the map")
            # allow the user to pick a variable
            available_variables = ["MED_HH_INCOME", "max_count", "avg_count", "log_max_count", "log_avg_count","POP_DENSITY", "log_POP_DENSITY"]
            agg_variable = st.selectbox(
                "Which variable do you want to inspect?",
                available_variables
            )
            # maps each city selected
            for city in agg_city:

                filtered_data = data[data["COUNTYFP"]==get_city_id(city)].dropna(subset=agg_variable)
                make_map_from(agg_variable, "title", filtered_data)
    else:
        st.write("<- No city is selected for analysis! Select one (or more) in the sidebar to the left! ")

# ----------------------------
# Tab 2
# ----------------------------
with tab2:
    st.subheader("Association of population density and median household income with micromobility usage")
    selected_areas = data.dropna(subset=["avg_count", "POP_DENSITY", "MED_HH_INCOME", "log_avg_count"])
    selected_areas["Seattle"] = [1 if x == "033" else 0 for x in selected_areas["COUNTYFP"]]

    x_sea = selected_areas[selected_areas["Seattle"] == 1]["avg_count"]
    x_spo = selected_areas[selected_areas["Seattle"] == 0]["avg_count"]

    fig, ax = plt.subplots(figsize = (12, 4))
    ax.boxplot([x_sea, x_spo], tick_labels = ["Seattle", "Spokane"], orientation = "horizontal")
    ax.set(
        ylabel = "City", 
        xlabel = "Average Micromobility Counts",
        title = "Distribution of Average Micromobility Usage by City"
        )
    st.pyplot(fig)

    c21, c22 = st.columns(2)

    with c21:
        x = selected_areas["POP_DENSITY"]
        y = selected_areas["avg_count"]

        fig, ax = plt.subplots(figsize = (12, 4))
        ax.scatter(x, y)
        b, a = np.polyfit(x, y, deg = 1)
        xseq = np.linspace(0, x.max(), num = 100)
        ax.plot(xseq, a + b * xseq, color = "r", lw = 2.5)
        ax.set(
            xlabel = "Population Density", 
            ylabel = "Average Micromobility Counts",
            title = "Average Micromobility Usage by Population Density"
            )
        st.pyplot(fig)
        
        x = selected_areas["MED_HH_INCOME"]
        y = selected_areas["avg_count"]

        fig, ax = plt.subplots(figsize = (12, 4))
        ax.scatter(x, y)
        b, a = np.polyfit(x, y, deg = 1)
        xseq = np.linspace(0, x.max(), num = 100)
        ax.plot(xseq, a + b * xseq, color = "r", lw = 2.5)
        ax.set(
            xlabel = "Household Income", 
            ylabel = "Average Micromobility Counts",
            title = "Average Micromobility Usage by Median Household Income"
            )
        st.pyplot(fig)
        
    with c22:
        x = selected_areas["POP_DENSITY"]
        y = selected_areas["log_avg_count"]

        fig, ax = plt.subplots(figsize = (12, 4))
        ax.scatter(x, y)
        b, a = np.polyfit(x, y, deg = 1)
        xseq = np.linspace(0, x.max(), num = 100)
        ax.plot(xseq, a + b * xseq, color = "r", lw = 2.5)
        ax.set(
            xlabel = "Population Density", 
            ylabel = "Log Average Micromobility Counts",
            title = "Log Average Micromobility Usage by Population Density"
            )
        st.pyplot(fig)
        
        x = selected_areas["MED_HH_INCOME"]
        y = selected_areas["log_avg_count"]

        fig, ax = plt.subplots(figsize = (12, 4))
        ax.scatter(x, y)
        b, a = np.polyfit(x, y, deg = 1)
        xseq = np.linspace(0, x.max(), num = 100)
        ax.plot(xseq, a + b * xseq, color = "r", lw = 2.5)
        ax.set(
            xlabel = "Population Density", 
            ylabel = "Log Average Micromobility Counts",
            title = "Log Average Micromobility Usage by Median Household Income"
            )
        st.pyplot(fig)

# ----------------------------
# Tab 3
# ----------------------------
with tab3:
    st.subheader("Here's a summary!")
    def top_ten_counts(df):
        idx = df.dropna(subset=["name","count"]).groupby("name")["count"].idxmax()
        result = df.loc[idx].reset_index(drop=True)
        result = result[result["name"]!=""][["name", "count"]].nlargest(10, "count")
        st.write(result.reset_index(drop=True))
    
    col31, col32 = st.columns(2)

    with col31:
        # Seattle 
        st.subheader("Seattle Top 10 Streets and Trails for Micromobility Use")
        top_ten_counts(seattle_micro_streets)

    with col32:
        # Spokane
        st.subheader("Spokane Top 10 Streets and Trails for Micromobility Use")
        top_ten_counts(spokane_micro_streets)

    # ig?
    st.subheader("Selected Unit Data")
    st.write(data)