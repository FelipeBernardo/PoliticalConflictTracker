import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import seaborn as sns
st.set_page_config(layout = 'wide')


@st.cache_data  # Add caching decorator to the function
def load_data(allow_output_mutation=True):
    data = pd.read_csv('clean.csv')
    return data

df = load_data()

df['event_date'] = pd.to_datetime(df['event_date'], format="%Y-%m-%d")
df['event_year'] = df['event_date'].dt.year.astype(str)

st.title('Brazil Political Conflict Tracker (2018-2023)')
st.markdown(

'''This is a fully interactive application that tracks both non-violent and violent political conflicts in Brazil between 2018-2023.

All data are official figures from the Armed Conflict Location & Event Data Project (ACLED).''')


with st.expander("Check type of event definitions (codebook)"):
    st.markdown(
'''
- **Battles:** A violent interaction between two organized armed groups at a particular time and location.

- **Protests:** An in-person public demonstration of three or more participants in which the participants do not engage in violence, though violence may be used against them.

- **Riots:** Violent events where demonstrators or mobs of three or more engage in violent or destructive acts, including but not limited to physical fights, rock throwing, property destruction, etc.

- **Explosions/Remote violence:** Incidents in which one side uses weapon types that, by their nature, are at range and widely destructive.

- **Violence against civilians:** Violent events where an organized armed group inflicts violence upon unarmed non-combatants. By definition, civilians are unarmed and cannot engage in political violence.

- **Strategic developments:** Activities of groups that are not recorded as ‘Political violence’ or ‘Demonstrations’ events, yet may trigger future events or contribute to political dynamics within and across states.

To know more about their criteria, check the [ACLED website](https://acleddata.com/).'''
)

# sidebar construction
st.sidebar.write('Choose your global filters')
year = st.sidebar.selectbox('Year', ('All', 2018, 2019, 2020, 2021, 2022, 2023), index = 0)
type_of_event = st.sidebar.selectbox('Type of event', ['All', 'Protests', 'Violence against civilians', 'Battles', 'Riots','Explosions/Remote violence', 'Strategic developments'],
index = 0)
fatalities = st.sidebar.selectbox('Fatalities', ['All events', 'Only fatal events', 'Only non-fatal events'], index = 0)
location_list = ['All', 'Belem', 'Belo Horizonte', 'Belford Roxo', 'Maceio', 'Manaus', 'Rio de Janeiro - Central Zone',
'Rio de Janeiro - North Zone', 'Rio de Janeiro - West Zone', 'Salvador', 'Sao Goncalo']
location = st.sidebar.selectbox('Location', options=location_list, index=0)
map_option = st.sidebar.toggle('3D Map', value = False)
graph_option = st.sidebar.radio('Graph style', ['Stacked', 'Grouped'])

if map_option:
    st.sidebar.write('Feature activated! It may take a few seconds to load...')

filtered_data = df.copy()
#setting up the data according to the inputs

if year != 'All':
    filtered_data = filtered_data.loc[filtered_data['event_date'].dt.year == year]

if fatalities == 'Only fatal events':
    filtered_data = filtered_data.loc[filtered_data['fatalities'] > 0]

elif fatalities == 'Only non-fatal events':
    filtered_data = filtered_data.loc[filtered_data['fatalities'] == 0]

if type_of_event != 'All':
    filtered_data = filtered_data.loc[filtered_data['event_type'] == type_of_event]

if location != 'All':
    filtered_data = filtered_data.loc[filtered_data['location'] == location]


if map_option == True and location == 'All':
    st.header('Where are the conflicts happening?')
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=filtered_data['latitude'].mean()-3,
            longitude=filtered_data['longitude'].mean()-10,
            zoom=3.7,
            pitch=55,
        ),
        layers=[
            pdk.Layer(
               'HexagonLayer',
               data=filtered_data,
               get_position='[longitude, latitude]',
               radius= 5000,
               elevation_scale=1500,
               elevation_range=[0, 550],
               pickable=True,
               extruded=True,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data=filtered_data,
                get_position='[longitude, latitude]',
                get_color='[200, 30, 0, 160]',
                get_radius= 6000,
            ),
        ],
    ))
else:
    if location == 'All':
        st.header('Where are the conflicts happening?')
        st.map(filtered_data, use_container_width=True)

if year == 'All':
    try:
        pivot_df = filtered_data.pivot_table(index='location', columns='event_year', aggfunc='size', fill_value=0)
        pivot_df['total_count'] = pivot_df.sum(axis=1)
        pivot_df['overall_percentage'] = pivot_df['total_count'] / pivot_df['total_count'].sum()
        #pivot_df['overall_percentage'] = pivot_df['overall_percentage'].astype(str) + '%'
        pivot_df.sort_values(by = 'total_count', ascending = False, inplace = True)
        pivot_years = pivot_df[['2018', '2019', '2020', '2021', '2022', '2023']]
        pivot_df['sums'] = pivot_years.values.tolist()
    except:
        pass

if year ==  'All':
    if location == 'All':
        st.dataframe(pivot_df, hide_index = True, use_container_width = True,
        column_config = {'location': 'Location', 'total_count': 'Total',
            'overall_percentage': st.column_config.ProgressColumn('Overall Percentage'),
            'sums': st.column_config.LineChartColumn('Overview')})
    else:
        a = pivot_df.drop('overall_percentage', axis = 1)
        st.dataframe(a, hide_index = True, use_container_width = True,
        column_config = {'location': 'Location', 'total_count': 'Total',
            'overall_percentage': st.column_config.ProgressColumn('Overall Percentage'),
            'sums': st.column_config.LineChartColumn('Overview')})



### event distribution graph
if type_of_event == 'All' and year == 'All':
    st.subheader('Event distribution across the years')
    sub = filtered_data.groupby(['event_year', 'event_type']).size().reset_index(name='count')
    sub['percentage'] = sub.groupby('event_year')['count'].transform(lambda x: (x / x.sum()) * 100)
    sub.loc[sub['percentage'] < 4, 'event_type'] = 'Other'
    sub = sub.groupby(['event_year', 'event_type']).sum().reset_index()
    fig = px.pie(sub, values='count', names='event_type', facet_col='event_year', hole=0.25, labels = {'event_type': 'Type ','event_year': 'Year ', 'count': 'Count '})
    fig.update_traces(textposition='inside', textinfo='percent')
    #fig.update_layout(legend_title_text='Event Type')

    fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=0,
    xanchor="center",
    x=.5
))

    fig.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))

    # Update pie labels to show percentages inside the slices
    fig.update_traces(textposition='inside', textinfo='percent')


    st.plotly_chart(fig, use_container_width=True)


###year graph
if type_of_event != 'All':
    st.subheader('Number of occurences per Year in the selected period')
    sub = filtered_data.groupby('event_year')['sub_event_type'].value_counts().reset_index()
    fig = px.bar(sub, x = 'event_year', y = 'count', color = 'sub_event_type',  labels = {'sub_event_type': 'Sub Type ', 'event_year': 'Year ', 'count': 'Count '})
    fig.update_layout(xaxis={'type': 'category'}, xaxis_title='', yaxis_title='')

    if graph_option == 'Stacked':
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig.update_layout(barmode = 'group')
        st.plotly_chart(fig, use_container_width=True, barmode = 'group')
else:
    st.subheader('Number of occurences per Year in the selected period')
    sub = filtered_data.groupby('event_year')['event_type'].value_counts().reset_index()
    fig = px.bar(sub, x = 'event_year', y = 'count', color = 'event_type',  labels = {'event_type': 'Type ', 'event_year': 'Year ', 'count': 'Count '})
    fig.update_layout(xaxis={'type': 'category'}, xaxis_title='', yaxis_title='')
    if graph_option == 'Stacked':
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig.update_layout(barmode = 'group')
        st.plotly_chart(fig, use_container_width=True, barmode = 'group')

#month graph

b = filtered_data.copy()
b['month'] = b['event_date'].dt.month_name()
months_order = ['January', 'February', 'March', 'April','May', 'June', 'July', 'August', 'September', 'October','November', 'December' ]
b['month'] = pd.Categorical(b['month'], categories = months_order, ordered = True)
st.header('Number of occurences per Month in the selected period')
if type_of_event != 'All':
    b = b.groupby('month')['sub_event_type'].value_counts().reset_index()
    fig = px.bar(b, x = 'month', y = 'count', color = 'sub_event_type',
                     labels = {'sub_event_type': 'Sub Type ', 'count': 'Count ', 'event_date': 'Month '})
    fig.update_layout(xaxis={'type': 'category'}, xaxis_title='', yaxis_title='')
    if graph_option == 'Stacked':
        st.plotly_chart(fig, use_container_width = True)
    else:
        fig.update_layout(barmode = 'group')
        st.plotly_chart(fig,  use_container_width=True)
else:
    b = b.groupby('month')['event_type'].value_counts().reset_index()
    fig = px.bar(b, x = 'month', y = 'count', color = 'event_type',
                     labels = {'event_type': 'Event Type', 'count': '', 'event_date': 'Month'})
    fig.update_layout(xaxis={'type': 'category'}, xaxis_title='', yaxis_title='')
    if graph_option == 'Stacked':
        st.plotly_chart(fig, use_container_width = True)
    else:
        fig.update_layout(barmode = 'group')
        st.plotly_chart(fig,  use_container_width=True)


#day of the week graph
c = filtered_data.copy()
c['day_week'] = c['event_date'].dt.day_name()
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
c['day_week'] = pd.Categorical(c['day_week'], categories=days_order, ordered=True)


if type_of_event == 'All':
    c1 = c.groupby('day_week')['event_type'].value_counts().reset_index()
    fig2 = px.bar(c1, x = 'day_week', y = 'count', color = 'event_type', labels = {'event_type': 'Event Type', 'day': 'Weekday'})
    fig2.update_layout(xaxis={'type': 'category'}, xaxis_title='', yaxis_title='')
    if graph_option == 'Stacked':
        st.subheader('Number of occurences per Weekday in the selected period')
        st.plotly_chart(fig2, use_container_width=True)

    else:
        fig2.update_layout(barmode = 'group')
        st.subheader('Number of occurences per Weekday in the selected period')
        st.plotly_chart(fig2, use_container_width=True)
else:
    c2 = c.groupby(['day_week', 'sub_event_type']).size().reset_index(name = 'count')
    fig2 = px.bar(c2, x = 'day_week', y = 'count', color = 'sub_event_type', labels = {'sub_event_type': 'Sub Type', 'day': 'Weekday'})
    fig2.update_layout(xaxis={'type': 'category'}, xaxis_title='', yaxis_title='')
    if graph_option == 'Stacked':
        st.subheader('Number of occurences per Weekday in the selected period')
        st.plotly_chart(fig2, use_container_width=True)

    else:
        fig2.update_layout(barmode = 'group')
        st.subheader('Number of occurences per Weekday in the selected period')
        st.plotly_chart(fig2, use_container_width=True)


######################

st.subheader('Who are the most relevant actors?')

a = filtered_data.groupby(['event_year', 'event_type','sub_event_type'])[['actor1']].value_counts().reset_index()
b = filtered_data.groupby(['event_year', 'event_type','sub_event_type'])[['actor2']].value_counts().reset_index()
b.rename(columns = {'actor2': 'actor1'}, inplace = True)
c = pd.concat([a, b])
c2 = c.groupby('actor1')['count'].sum().reset_index().sort_values(by ='count', ascending = False)
c2['percentage'] = (c2['count']/c2['count'].sum())

st.dataframe(c2, hide_index = True, use_container_width = True, column_config = {'actor1': 'Actor', 'count': 'Count',
'percentage': st.column_config.ProgressColumn('Percentage')})


############
st.subheader("Who's fighting who?")
st.markdown('Number of times one or two actors were involved in a conflit. The order does not reflect the perpetrator of the agression')

filtered_data['actor2'].fillna('None', inplace=True)
actor_counts = filtered_data.groupby(['actor1', 'actor2']).size().reset_index(name='count')
actor_counts['percentage'] = actor_counts['count'] / actor_counts['count'].sum()
actor_counts.sort_values(by = 'count', ascending = False, inplace = True)
st.dataframe(actor_counts, use_container_width=True, hide_index=True,
             column_config={'actor1': 'Actor 1', 'actor2': 'Actor 2', 'count': 'Count',
                            'percentage': st.column_config.ProgressColumn('Percentage')})

st.markdown(' ##### Creator: Felipe Bernardo, feel free to contact me on: felipebrenobernardo@gmail.com.')
########################
