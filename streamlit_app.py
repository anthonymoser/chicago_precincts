import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import json
import plotly.express as px
named_colorscales = list(px.colors.named_colorscales())

with open("data/Precincts (current).geojson") as data:
    geo = json.load(data)


def google_sheet(sheet_url:str)->str:
  url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")
  return url

# Add title and header
st.title("Chicago Precincts")
st.write("A PublicDataTools project by Anthony Moser")
instructions = st.sidebar.checkbox(label="Show instructions", value=1)
if instructions:
    st.markdown("""
        This is a tool for making maps of Chicago voting data by precinct.  
          
        To get started, paste the URL of a publicly viewable Google Sheet of precinct level data into the box.  
        Then choose the field you want to visualize, and if you want to use the existing value, count the records, or sum/average the values.  
          
        To work, the sheet must have either a precinct_id ("full text") column, or a ward column and a precinct column. 
          
        The filter box lets you use logical expressions like "ward > 1" or "precinct == 12345"  
          
        For an example, here's the url of precinct data from the 2020 Democratic Primary:  
        https://docs.google.com/spreadsheets/d/1lm-mRnS8doF9xoLZ8qT8RJNu-SWxXqRsbLlUgP-N35g/edit#gid=631255818  
          
        Use the two column index and select "Ward" and "Precinct" as the columns.
    """)
data_url = st.sidebar.text_input("Google Sheet URL")
data_fields = []

if data_url:

    df = pd.read_csv(google_sheet(data_url))
    ef = df.copy()
    table = st.dataframe(ef, width=800)
    fields = list(df.columns)
    selected_field = st.sidebar.selectbox(label="Data field", options=fields)
    operation = st.sidebar.selectbox(label="What to do with the data field?", options= ["Use values", "Count records", "Sum values", "Avg values"], index=0)
    index = st.sidebar.radio("Index type", options=['Precinct_id (one column)', 'Ward and precinct (two columns)'])
    if index == "Precinct_id (one column)":
        precinct_id = st.sidebar.selectbox(label="Field with full text precinct id", options = fields)
        indexed = True
    elif index == 'Ward and precinct (two columns)':
        try:
            precinct_id = "precinct_id"

            ward_field = st.sidebar.selectbox('Field with ward number', options=fields, index = 0)
            precinct_field = st.sidebar.selectbox('Field with precinct number', options=fields)
            ef = ef[(ef[ward_field].notna()) & (ef[precinct_field].notna())].copy()
            ef[ward_field] = ef[ward_field].astype('int64')
            ef[precinct_field] = ef[precinct_field].astype('int64')

            ef[precinct_id] = ef.apply(lambda row: f"{row[ward_field]:02}{row[precinct_field]:03}", axis = 1)
            table.dataframe(ef, width=800)
            indexed = True
        except Exception as e:
            indexed = False
            st.sidebar.markdown("*Are these columns correct?*")
            st.write(e)

    query = st.sidebar.text_input('Optional: Filter the data with a query')
    if query:
        ef = ef.query(query)
        table.dataframe(ef, width=1000, height=200)

    if indexed:
        if operation != "Use values":
            if operation == "Count records":
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

        color_scale = st.selectbox('Color scale', options=named_colorscales, index=19)

        # Geographic Map
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson=geo,
                locations=ef[precinct_id],
                featureidkey="properties.full_text",
                z=ef[selected_field],
                colorscale=color_scale,
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


