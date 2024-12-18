import streamlit as st
import pandas as pd
import os
import altair as alt

# 设置文件路径
directory = r'C:\Data\data'
file = 'gdf_RAC.csv'
file2 = 'df_KPI.csv'

# 缓存读取 CSV 文件的函数
@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(directory, file), encoding='utf-8', usecols=['ID', '工作频段', '地市', '县区', '镇区', '村区'])
    df_KPI = pd.read_csv(os.path.join(directory, file2), encoding='utf-8', usecols=['ID', '开始时间', 'R1012_001', 'R1012_002', 'K1009_001', 'R1001_012', 'R1001_001', 'R1034_012', 'R1034_001', 'R1039_002', 'R1039_001', 'R1004_003', 'R1004_004', 'R1004_002', 'R1004_007', 'R1005_012', 'R1006_012', 'R2007_002', 'R2007_004', 'R2006_004', 'R2006_008', 'R2005_004', 'R2005_008', 'R2007_001', 'R2007_003', 'R2006_001', 'R2006_005', 'R2005_001', 'R2005_005', 'R1034_013', 'R1034_002', 'R1001_018', 'R1001_015', 'R1001_007', 'R1001_004', 'R2035_003', 'R2035_013', 'R2035_026', 'R2005_063', 'R2005_067', 'R2006_071', 'R2006_075', 'R2007_036', 'R2007_040', 'R2005_060', 'R2005_064', 'R2006_068', 'R2006_072', 'R2007_033', 'R2007_037'])
    return df, df_KPI

# 读取数据
df, df_KPI = load_data()

# 显示筛选项
with st.container():
    cols = st.columns(5)  # 创建五列布局

    # 频段选择框
    selected_band = cols[0].selectbox('选择工作频段', ['全部'] + df['工作频段'].unique().tolist())

    # 地市选择框，基于频段选择进行过滤
    if selected_band == '全部':
        city_options = df['地市'].unique().tolist()
    else:
        city_options = df[df['工作频段'] == selected_band]['地市'].unique().tolist()
    selected_city = cols[1].selectbox('选择地市', ['全部'] + city_options)

    # 县区选择框，基于频段和地市选择进行过滤
    if selected_city == '全部':
        county_options = df[df['工作频段'] == selected_band]['县区'].unique().tolist() if selected_band != '全部' else df['县区'].unique().tolist()
    else:
        county_options = df[(df['工作频段'] == selected_band) & (df['地市'] == selected_city)]['县区'].unique().tolist()
    selected_county = cols[2].selectbox('选择县区', ['全部'] + county_options)

    # 镇区选择框，基于频段、地市和县区选择进行过滤
    if selected_county == '全部':
        town_options = df[(df['工作频段'] == selected_band) & (df['地市'] == selected_city)]['镇区'].unique().tolist() if selected_city != '全部' else df['镇区'].unique().tolist()
    else:
        town_options = df[(df['工作频段'] == selected_band) & (df['地市'] == selected_city) & (df['县区'] == selected_county)]['镇区'].unique().tolist()
    selected_town = cols[3].selectbox('选择镇区', ['全部'] + town_options)

    # 村区选择框，基于频段、地市、县区和镇区选择进行过滤
    if selected_town == '全部':
        village_options = df[(df['工作频段'] == selected_band) & (df['地市'] == selected_city) & (df['县区'] == selected_county)]['村区'].unique().tolist() if selected_county != '全部' else df['村区'].unique().tolist()
    else:
        village_options = df[(df['工作频段'] == selected_band) & (df['地市'] == selected_city) & (df['县区'] == selected_county) & (df['镇区'] == selected_town)]['村区'].unique().tolist()
    selected_village = cols[4].selectbox('选择村区', ['全部'] + village_options)


# 根据选择更新数据筛选
final_df = df.copy()
if selected_band != '全部':
    final_df = final_df[final_df['工作频段'] == selected_band]
if selected_city != '全部':
    final_df = final_df[final_df['地市'] == selected_city]
if selected_county != '全部':
    final_df = final_df[final_df['县区'] == selected_county]
if selected_town != '全部':
    final_df = final_df[final_df['镇区'] == selected_town]
if selected_village != '全部':
    final_df = final_df[final_df['村区'] == selected_village]

# 合并数据框
merged_df = pd.merge(df_KPI, final_df, on='ID', how='inner')

# 时间范围选择
min_date = pd.to_datetime(merged_df['开始时间']).min().date()
max_date = pd.to_datetime(merged_df['开始时间']).max().date()
selected_date_range = st.slider('选择时间范围', min_value=min_date, max_value=max_date, value=(min_date, max_date))

# 时间范围筛选
merged_df['开始时间'] = pd.to_datetime(merged_df['开始时间'])
merged_df = merged_df[(merged_df['开始时间'].dt.date >= selected_date_range[0]) & (merged_df['开始时间'].dt.date <= selected_date_range[1])]

# 数据聚合
agg_df = merged_df.groupby('开始时间').sum().reset_index()

# 创建图表
def create_chart(data, y_field, title):
    return alt.Chart(data).mark_line().encode(
        x='开始时间:T',
        y=alt.Y(f'{y_field}:Q', title=title),
        tooltip=['开始时间:T', alt.Tooltip(f'{y_field}:Q', title=title)]
    ).properties(title=title, width=600, height=400)

# 显示图表
st.altair_chart(create_chart(agg_df, 'R1012_001', '数据业务流量'), use_container_width=True)