import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import json



with open("data/Precincts (current).geojson") as data:
    geo = json.load(data)


def google_sheet(sheet_url:str)->str:
  url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")
  return url

# Add title and header
st.title("Chicago Precincts")
data_url = st.sidebar.text_input("Google Sheet URL")
data_fields = []

if data_url:

    df = pd.read_csv(google_sheet(data_url)).dropna()
    ef = df.copy()
    table = st.dataframe(ef, width=800)

    selected_field = st.sidebar.selectbox(label="Data field", options=list(df.columns))
    operation = st.sidebar.selectbox(label="What to do with the data field?", options= ["Use values", "Count values", "Sum values", "Avg values"], index=0)

    precinct_id = st.sidebar.text_input(label="Field with full text precinct id", value="FULL_TEXT")
    ward_and_precinct = st.sidebar.checkbox('Use ward and precinct instead of precinct id')
    if ward_and_precinct:
        ward_field = st.sidebar.text_input('Field with ward number', value="WARD")
        precinct_field = st.sidebar.text_input('Field with precinct number', value= "PRECINCT")
        ef[precinct_id] = ef.apply(lambda row: f"{int(row[ward_field]):02}{int(row[precinct_field]):03}", axis = 1)
        table.dataframe(ef, width=800)

    query = st.sidebar.text_input('Optional: Filter the data with a query')
    if query:
        ef = ef.query(query)
        table.dataframe(ef, width=800)

    if operation != "Use values":
        if operation == "Count values":
            ef = (ef
                    .groupby(precinct_id)
                    [selected_field].count()
                    .reset_index())
        elif operation == "Sum values":
            ef = (ef
                    .groupby(precinct_id)
                    [selected_field].sum()
                    .reset_index())
        elif operation == "Avg values":
            ef = (ef
                    .groupby(precinct_id)
                    [selected_field].mean()
                    .reset_index())
        table.dataframe(ef, width=800)

    # Geographic Map
    fig = go.Figure(
        go.Choroplethmapbox(
            geojson=geo,
            locations=ef[precinct_id],
            featureidkey="properties.full_text",
            z=ef[selected_field],
            # colorscale="sunsetdark",
            # zmin=1,
            # zmax=50,
            marker_opacity=0.5,
            marker_line_width=0,
        )
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=10.6,
        mapbox_center={"lat":41.8823348, "lon": -87.6282938},
        width=800,
        height=800,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig)