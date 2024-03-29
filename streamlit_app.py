import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import json
import plotly.express as px
named_colorscales = list(px.colors.named_colorscales())

@st.cache_data
def get_precincts() ->dict:
    precincts = {}
    
    with open("data/Precincts 2012-2022.geojson") as data:
        precincts['2012-2022']= json.load(data)
        
    with open("data/Precincts 2023-.geojson") as data:
        precincts['2023-']= json.load(data)
        
    return precincts 

def clean_columns(df:pd.DataFrame)->pd.DataFrame:
    df = df.convert_dtypes()
    lowercase = { 
        c: c.lower().strip().replace(' ', '_') 
        for c in df.columns }
    df = df.rename(columns=lowercase)
    return df

def make_pretty(styler):
    # styler.set_caption("Weather Conditions")
    # styler.format(rain_condition)
    # styler.format_index(lambda v: v.strftime("%A"))
    styler.background_gradient(cmap="YlGnBu")
    return styler

def google_sheet(sheet_url:str)->str:
  parts = sheet_url.split("/edit")
  url = f'{parts[0]}/export?format=csv'
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
          
        For an example, here's the url of precinct data from the 2023 February Municipal election:  
        https://docs.google.com/spreadsheets/d/1uQ0utEkv4KWj1u_xb-KwybEchboEoahOEZJ6G8_E3dQ/edit?usp=sharing  
    """)

demo_url = "https://docs.google.com/spreadsheets/d/1uQ0utEkv4KWj1u_xb-KwybEchboEoahOEZJ6G8_E3dQ/edit?usp=sharing"
data_url = st.sidebar.text_input("Google Sheet URL", key="sheet_url", value=demo_url)
data_fields = []
precincts = get_precincts()
precinct_years = st.sidebar.selectbox('Choose precinct boundaries to use', options=[*list(precincts.keys())], index=1)
geo = precincts[precinct_years]

if data_url:
    df = pd.read_csv(google_sheet(data_url), low_memory=True).convert_dtypes()
    ef = df.copy()
    table = st.empty()
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
            ef[precinct_id] = ef[precinct_id].astype('str')
            
            indexed = True
        except Exception as e:
            indexed = False
            st.sidebar.markdown("*Are these columns correct?*")
            st.write(e)

    col1, col2, col3 = st.columns(3)

    selected_field = col1.selectbox(label="Which column do you want to see?", options=fields, index=data_field_index)
    color_scale = col2.selectbox('Color scale', options=named_colorscales, index=19)
    query = col3.text_input('Optional: Filter the data with a query', placeholder="Ward == 12")

    if "%" in str(ef.iloc[0][selected_field]) or "_pct" in str(ef.iloc[0][selected_field]) :
        ef[selected_field] = ef[selected_field].apply(lambda x: float(x.replace("%","")))
        percent = "%"

    if query:
        ef = ef.query(query)

    if indexed:
        table.dataframe(ef.style.pipe(make_pretty), width=800)
        field_name = selected_field if "%" not in selected_field else selected_field.replace("%", "")
        ef['hover_text'] = ef.apply(lambda row: f"Ward: {row[ward_field]}\nPrecinct: {row[precinct_field]}\n{field_name}:{row[selected_field]}{percent}", axis=1)
        ef['precinct_id'] = ef.precinct_id.astype('str')

        # Geographic Map
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson=geo,
                locations=ef[precinct_id],
                featureidkey="properties.full_text",
                z=ef[selected_field],
                colorscale=color_scale,
                text = ef['hover_text'],
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
