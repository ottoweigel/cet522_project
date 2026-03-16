import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import branca.colormap as cm


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="Micromobility Explorer",
    page_icon="🛴",
    layout="wide",
)

# ----------------------------
# Data loading
# ----------------------------
@st.cache_data
def load_data_from_path(path):
    df = pd.read_csv(path)
    return  (df)

@st.cache_data
def load_geodata_from_path(path):
    gdf = gpd.read_file(path, engine="pyogrio")
    return  (gdf)

CENSUS_DATA = load_geodata_from_path("census_data.geojson") # includes count data already
GRID_DATA = load_geodata_from_path("grid_data.geojson") # includes count data already
seattle_micro_streets = load_geodata_from_path("seattle_micro_streets.geojson").dropna(subset=["count"])
spokane_micro_streets = load_geodata_from_path("spokane_micro_streets.geojson").dropna(subset=["count"])


# ----------------------------
# Sidebar controls
# ----------------------------
st.sidebar.header("Analyis Filters")

all_cities = ("Seattle", "Spokane")
agg_city = st.sidebar.multiselect(
    "Select cities:",
    options=all_cities,
    default=all_cities,
)
agg_map = st.sidebar.selectbox("Analysis Unit:", ["Census", "Grid",], index=0)

# selects data frame for analysis
if (agg_map == "Grid"):
    data = GRID_DATA
else:
    data = CENSUS_DATA

if list(set(["POP_DENSITY_aw", "log_POP_DENSITY_aw", 'MED_HH_INCOME_aw']) & set(data.columns)):
    data.rename(columns={"POP_DENSITY_aw":"POP_DENSITY", "log_POP_DENSITY_aw":"log_POP_DENSITY", "MED_HH_INCOME_aw":"MED_HH_INCOME"}, inplace=True)



# ----------------------------
# Intro Page
# ----------------------------
def intro():
    st.title("Micromobility Explorer 🛴 🗺️ 🔭")
    st.caption("Explore micromobility in Seattle and Spokane!") 
    
    # additional data
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Seattle, Average Micromobility Segement Count", f"{seattle_micro_streets["count"].mean():,.0f}")
    col2.metric("Spokane, Average Micromobility Segement Count", f"{spokane_micro_streets["count"].mean():,.0f}")

    king_county_tract_num = (CENSUS_DATA["COUNTYFP"]=="033").sum()
    spokane_county_track_num = (CENSUS_DATA["COUNTYFP"]=="063").sum()
    col3.metric("King County, Number of Census Tracks", f"{king_county_tract_num:,.0f}")
    col4.metric("Spokane County, Number of Census Tracks", f"{spokane_county_track_num:,.0f}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("City of Seattle, Median Income", "$123,860")
    col6.metric("City of Spokane, Median Income", "$86,206")

    st.write("Shared micromobility systems such as dockless e-scooters and bike-share programs have expanded rapidly in many U.S. cities and are often promoted as flexible, low-cost transportation options that improve first- and last-mile connectivity and reduce reliance on private automobiles. Because these services are typically deployed by private operators and influenced by market demand, their availability may not be evenly distributed across neighborhoods. Prior research has raised concerns that micromobility systems may concentrate in higher-income or central areas, potentially creating inequities in access to these new mobility options.")
    st.write("This project examines the spatial distribution of shared micromobility in Seattle and Spokane. Seattle represents a large coastal metropolitan area with a dense urban core and a more developed network of bicycles and micromobility infrastructure, while Spokane is a mid-sized inland city with a lower-density urban form and comparatively more limited cycling infrastructure. Comparing these two cities provides an opportunity to explore how micromobility availability varies across different urban contexts in Washington State. The goal of this analysis is to evaluate whether shared micromobility access is distributed equitably across neighborhoods and how patterns differ between the two cities.")


# ----------------------------
# Visualization Page
# ----------------------------
def visualization():
    st.title("Visualizing Data with Maps")

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
            available_variables = ["MED_HH_INCOME", "POP_DENSITY", "log_POP_DENSITY", "max_count", "avg_count", "log_max_count", "log_avg_count"]
            variable_select = ["Median Household Income", "Population Density", "Populatation Density (log-transformed)", "Maximum Micromobility Count", "Average Micromobility Count", "Maximum Micromobility Count (log-transformed)", "Average Micromobility Count (log-transformed)"]
            agg_variable = st.selectbox(
                "Which variable do you want to inspect?",
                variable_select
            )
            # maps each city selected
            for city in agg_city:
                var = available_variables[variable_select.index(agg_variable)]
                filtered_data = data[data["COUNTYFP"]==get_city_id(city)].dropna(subset=var)
                make_map_from(var, "title", filtered_data)
    else:
        st.write("<- No city is selected for analysis! Select one (or more) in the sidebar to the left! ")


# ----------------------------
# ML Page
# ----------------------------
def machine_learning():
    st.title("Machine Learning and Regression")

    def make_plots(x, y, cats):
        fig, ax = plt.subplots(figsize = (12, 4))
        color_map = {'Seattle': 'blue', 'Spokane': 'green'}
        ax.scatter(x, y, c=[color_map[cat] for cat in cats])
        b, a = np.polyfit(x, y, deg = 1)
        xseq = np.linspace(x.min(), x.max(), num = 100)
        ax.plot(xseq, a + b * xseq, color = "r", lw = 2.5)
        return fig, ax
    
    st.subheader("Association of population density and median household income with micromobility usage")
    selected_areas = data.dropna(subset=["avg_count", "log_POP_DENSITY", "MED_HH_INCOME", "log_avg_count", "log_POP_DENSITY"]).copy()
    selected_areas["City"] = ["Seattle" if x == "033" else "Spokane" for x in selected_areas["COUNTYFP"]]

    x_sea = selected_areas[selected_areas["City"] == "Seattle"]["avg_count"]
    x_spo = selected_areas[selected_areas["City"] == "Spokane"]["avg_count"]

    fig, ax = plt.subplots(figsize = (12, 3))
    ax.boxplot([x_sea, x_spo], tick_labels = ["Seattle", "Spokane"], orientation = "horizontal")
    ax.set(
        ylabel = "City", 
        xlabel = "Average Micromobility Counts",
        title = "Distribution of Average Micromobility Usage by City"
    )
    st.pyplot(fig, clear_figure=False)

    if "Seattle" in agg_city and "Spokane" not in agg_city:
        selected_areas = selected_areas[selected_areas["City"] == "Seattle"]
    elif "Spokane" in agg_city and "Seattle" not in agg_city:
        selected_areas = selected_areas[selected_areas["City"] == "Spokane"]

    if agg_city:
        c21, c22 = st.columns(2)
        cat = selected_areas["City"]
        with c21:
            x = selected_areas["POP_DENSITY"]
            y = selected_areas["avg_count"]

            fig, ax = make_plots(x,y,cat)
            ax.set(
                xlabel = "Population Density", 
                ylabel = "Average Micromobility Counts",
                title = "Average Micromobility Usage by Population Density"
            )
            st.pyplot(fig)
            
            
            x = selected_areas["MED_HH_INCOME"]
            y = selected_areas["avg_count"]

            fig, ax = make_plots(x,y,cat)
            ax.set(
                xlabel = "Median Household Income", 
                ylabel = "Average Micromobility Counts",
                title = "Average Micromobility Usage by Median Household Income"
            )
            st.pyplot(fig)
            
        with c22:
            x = selected_areas["log_POP_DENSITY"]
            y = selected_areas["log_avg_count"]

            fig, ax = make_plots(x,y,cat)
            ax.set(
                xlabel = "Log Population Density", 
                ylabel = "Log Average Micromobility Counts",
                title = "Log Average Micromobility Usage by Log Population Density"
            )
            st.pyplot(fig)
            
            x = selected_areas["MED_HH_INCOME"]
            y = selected_areas["log_avg_count"]

            fig, ax = make_plots(x,y,cat)
            ax.set(
                xlabel = "Median Household Income", 
                ylabel = "Log Average Micromobility Counts",
                title = "Log Average Micromobility Usage by Median Household Income"
            )
            st.pyplot(fig)
    else:
        st.write("<- No city is selected for analysis! Select one (or more) in the sidebar to the left! ")

# ----------------------------
# Summary Page
# ----------------------------
def summary():
    st.title("Summary and Data")
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

    st.subheader("E/R Diagram")
    st.image("er_diagram.jpg", width="stretch")

    st.subheader("Limitations")
    st.write("This analysis is subject to several data limitations. The micromobility dataset provides aggregated trip counts by street segment but does not distinguish between mode types such as e-bikes or scooters, nor does it identify specific service providers. As a result, differences in deployment patterns across micromobility modes cannot be evaluated. In addition, the dataset represents cumulative trip counts across the observation period and does not include temporal detail such as daily or hourly activity. This prevents analysis of potential differences in weekday versus weekend usage patterns.")
    st.write("The geographic scope is also limited to Seattle and Spokane, so findings may not generalize to cities with different urban forms or transportation systems.")

    st.subheader("Download Data")
    # Convert DataFrame to CSV
    Cesnus_csv_data = CENSUS_DATA.to_csv(index=False).encode('utf-8')
    Grid_csv_data = CENSUS_DATA.to_csv(index=False).encode('utf-8')
    seattle_steets_data = seattle_micro_streets.to_csv(index=False).encode('utf-8')
    spokane_steets_data = spokane_micro_streets.to_csv(index=False).encode('utf-8')

    # Create a download button
    st.download_button(
        label="Download Census",
        data=Cesnus_csv_data,
        file_name="data.csv",
        mime="text/csv"
    )
    st.download_button(
        label="Download Grid",
        data=Grid_csv_data,
        file_name="data.csv",
        mime="text/csv"
    )
    st.download_button(
        label="Download Seattle Streets",
        data=seattle_steets_data,
        file_name="data.csv",
        mime="text/csv"
    )
    st.download_button(
        label="Download Spokane Streets",
        data=spokane_steets_data,
        file_name="data.csv",
        mime="text/csv"
    )


# ----------------------------
# make the pages
# ----------------------------
# create pages and define navigation
intro_page = st.Page(intro, title="Introduction")
visual_page = st.Page(visualization, title="Visualizing Data with Maps")
ml_page = st.Page(machine_learning, title="Machine Learning and Regression")
summary_page = st.Page(summary, title="Summary and Data")

pg = st.navigation([intro_page, visual_page, ml_page, summary_page])
pg.run()
