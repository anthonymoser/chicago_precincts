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
        Then choose the field you want to visualize.
          
        To work, the sheet must have either a precinct_id ("full text") column, or a ward column and a precinct column. 
          
        The filter box lets you use logical expressions like "ward > 1" or "precinct == 12345"  
          
        For an example, here's the url of precinct data from the 2022 Primary:  
        https://docs.google.com/spreadsheets/d/14z36VYfeqhBksXlwgShmvPe1QcK7xLtmJuzhquDaqpQ/edit#gid=419264076  
    """)

data_url = st.sidebar.text_input("Google Sheet URL", key="sheet_url", placeholder="https://docs.google.com/spreadsheets/d/14z36VYfeqhBksXlwgShmvPe1QcK7xLtmJuzhquDaqpQ/edit#gid=419264076")
data_fields = []

if data_url:

    df = pd.read_csv(google_sheet(data_url)).convert_dtypes()
    ef = df.copy()
    table = st.dataframe(ef, width=800)
    fields = list(df.columns)

    lowercase = [f.lower() for f in fields]
    ward_field_index = 0
    precinct_field_index = 0
    full_text_index = 0
    data_field_index = 0
    percent = ""

    for f in lowercase:
        if "ward" in f:
            ward_field_index = lowercase.index(f)
        if "precinct" in f:
            precinct_field_index = lowercase.index(f)
        if "full_text" in f:
            full_text_index = lowercase.index(f)
        if f not in ["county", "state", "precinct", "ward"]:
            data_field_index = lowercase.index(f)

    # operation = st.sidebar.selectbox(label="What do you want to do with the data?", options=["Use values", "Count records", "Sum values", "Avg values"], index=0)
    index = st.sidebar.radio("Identify precincts using", options=['Precinct_id (one column)', 'Ward and precinct (two columns)'], index = 1)

    if index == "Precinct_id (one column)":
        precinct_id = st.sidebar.selectbox(label="Field with full text precinct id", options = fields, index = full_text_index)
        indexed = True
    elif index == 'Ward and precinct (two columns)':
        try:
            precinct_id = "precinct_id"

            ward_field = st.sidebar.selectbox('Which column has the ward number?', options=fields, index = ward_field_index)
            precinct_field = st.sidebar.selectbox('Which column has the precinct number?', options=fields, index = precinct_field_index)
            ef = ef[(ef[ward_field].notna()) & (ef[precinct_field].notna())].copy()

            ef[precinct_id] = ef.apply(lambda row: f"{int(row[ward_field]):02}{int(row[precinct_field]):03}", axis = 1)
            table.dataframe(ef, width=800)
            indexed = True
        except Exception as e:
            indexed = False
            st.sidebar.markdown("*Are these columns correct?*")
            st.write(e)

    selected_field = st.sidebar.selectbox(label="Which column do you want to visualize?", options=fields, index=data_field_index)

    if "%" in ef.iloc[0][selected_field]:
        ef[selected_field] = ef[selected_field].apply(lambda x: float(x.replace("%","")))
        percent = "%"

    query = st.sidebar.text_input('Optional: Filter the data with a query')
    if query:
        ef = ef.query(query)
        table.dataframe(ef, width=1000, height=200)

    if indexed:
        # if operation != "Use values":
        #     if operation == "Count records":
        #         ef = (ef
        #                 .groupby(precinct_id)
        #                 [selected_field].count()
        #                 .reset_index())
        #     elif operation == "Sum values":
        #         ef = (ef
        #                 .groupby(precinct_id)
        #                 [selected_field].sum()
        #                 .reset_index())
        #     elif operation == "Avg values":
        #         ef = (ef
        #                 .groupby(precinct_id)
        #                 [selected_field].mean()
        #                 .reset_index())
        table.dataframe(ef, width=800)
        field_name = selected_field if "%" not in selected_field else selected_field.replace("%", "")
        ef['hover_text'] = ef.apply(lambda row: f"Ward: {row[ward_field]}\nPrecinct: {row[precinct_field]}\n{field_name}:{row[selected_field]}{percent}", axis=1)
        color_scale = st.selectbox('Color scale', options=named_colorscales, index=19)

        # Geographic Map
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson=geo,
                locations=ef[precinct_id],
                featureidkey="properties.full_text",
                z=ef[selected_field],
                colorscale=color_scale,
                text = ef['hover_text'],
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


