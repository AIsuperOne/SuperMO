import streamlit as st
import pandas as pd
import os
import altair as alt

# 设置文件路径
directory = r'C:\Users\Administrator\Documents\MnewData'
file = 'gdf_RAC.csv'
file2 = 'df_KPI.csv'

# 缓存读取 CSV 文件的函数
@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(directory, file), encoding='utf-8', usecols=['ID', '工作频段', '地市', '县区', '基站名称'])
    df_KPI = pd.read_csv(os.path.join(directory, file2), encoding='utf-8', usecols=[
        'ID', '开始时间', 'R1012_001', 'R1012_002', 'K1009_001', 'K1009_002'
    ])
    return df, df_KPI

# 读取数据
df, df_KPI = load_data()

# 获取不重复的工作频段和地市
unique_bands = df['工作频段'].unique().tolist()
unique_cities = df['地市'].unique().tolist()

# 显示筛选项
with st.container():
    col1, col2, col3 = st.columns(3)
    selected_band = col1.selectbox('选择工作频段', ['全部'] + unique_bands)
    
    if selected_band != '全部':
        filtered_cities = df[df['工作频段'] == selected_band]['地市'].unique().tolist()
    else:
        filtered_cities = unique_cities
    
    selected_city = col2.selectbox('选择地市', ['全部'] + filtered_cities)
    
    if selected_city != '全部':
        if selected_band != '全部':
            unique_counties = df[(df['工作频段'] == selected_band) & (df['地市'] == selected_city)]['县区'].unique().tolist()
        else:
            unique_counties = df[df['地市'] == selected_city]['县区'].unique().tolist()
    else:
        if selected_band != '全部':
            unique_counties = df[df['工作频段'] == selected_band]['县区'].unique().tolist()
        else:
            unique_counties = df['县区'].unique().tolist()
    
    selected_county = col3.selectbox('选择县区', ['全部'] + unique_counties)

# 根据筛选项过滤数据
if selected_band != '全部':
    df = df[df['工作频段'] == selected_band]

if selected_city != '全部':
    df = df[df['地市'] == selected_city]

if selected_county != '全部':
    df = df[df['县区'] == selected_county]

# 合并数据框
merged_df = pd.merge(df_KPI, df, on='ID', how='left')

# 根据筛选项过滤merged_df
if selected_band != '全部':
    merged_df = merged_df[merged_df['工作频段'] == selected_band]

if selected_city != '全部':
    merged_df = merged_df[merged_df['地市'] == selected_city]

if selected_county != '全部':
    merged_df = merged_df[merged_df['县区'] == selected_county]

# 计算基站数量
BS_num = df['基站名称'].nunique()
BS_num_1 = df[df['工作频段'] == 'band28']['基站名称'].nunique()
BS_num_2 = df[df['工作频段'] == 'band41']['基站名称'].nunique()

# 显示子标题
st.subheader('5G网络基站数量')

# 创建三列布局并显示指标
col1, col2, col3 = st.columns(3)
col1.metric('5G网络基站数', BS_num, 0.1)
col2.metric('5G网络700M基站数', BS_num_1, 0.15)
col3.metric('5G网络2.6G基站数', BS_num_2, 0.25)

# 计算新列
def calculate_columns(df):
    df["数据业务流量"] = df["R1012_001"] + df["R1012_002"]
    df["VoNR语音话务量"] = df["K1009_001"] / 4
    return df

merged_df = calculate_columns(merged_df)

# 将开始时间列转换为datetime类型并进行分组计算
merged_df['开始时间'] = pd.to_datetime(merged_df['开始时间'])
merged_df_grouped = merged_df.groupby('开始时间').agg({
    '数据业务流量': 'sum',
    'VoNR语音话务量': 'sum',
    'ID': 'nunique'
}).reset_index()

# 在展示数据时进行单位转换
merged_df_grouped['数据业务流量_TB'] = (merged_df_grouped['数据业务流量'] / 1000000000).round(2)
merged_df_grouped['VoNR语音话务量_千Erl'] = (merged_df_grouped['VoNR语音话务量'] / 1000).round(2)

# 计算最近一个月的日平均值
last_month_data = merged_df_grouped[merged_df_grouped['开始时间'] >= (merged_df_grouped['开始时间'].max() - pd.DateOffset(months=1))]
avg_traffic = (last_month_data['数据业务流量'] / 1000000000).mean().round(2)
avg_vonr = (last_month_data['VoNR语音话务量'] / 1000).mean().round(2)

# 找到最高和最低值
max_value_traffic = merged_df_grouped['数据业务流量_TB'].max()
min_value_traffic = merged_df_grouped['数据业务流量_TB'].min()
max_time_traffic = merged_df_grouped[merged_df_grouped['数据业务流量_TB'] == max_value_traffic]['开始时间'].iloc[0]
min_time_traffic = merged_df_grouped[merged_df_grouped['数据业务流量_TB'] == min_value_traffic]['开始时间'].iloc[0]

max_value_vonr = merged_df_grouped['VoNR语音话务量_千Erl'].max()
min_value_vonr = merged_df_grouped['VoNR语音话务量_千Erl'].min()
max_time_vonr = merged_df_grouped[merged_df_grouped['VoNR语音话务量_千Erl'] == max_value_vonr]['开始时间'].iloc[0]
min_time_vonr = merged_df_grouped[merged_df_grouped['VoNR语音话务量_千Erl'] == min_value_vonr]['开始时间'].iloc[0]

# 使用 Altair 绘制话务量的曲线趋势图
line_chart_traffic = alt.Chart(merged_df_grouped).mark_line().encode(
    x='开始时间:T',
    y=alt.Y('数据业务流量_TB:Q', title='数据业务流量 (TB)'),
    tooltip=['开始时间:T', '数据业务流量_TB:Q']
).properties(
    title='话务量趋势图',
    width=800,
    height=400
)

# 添加标注
max_annotation_traffic = alt.Chart(pd.DataFrame({
    '开始时间': [max_time_traffic], 
    '数据业务流量_TB': [max_value_traffic]
})).mark_text(
    text=f'{max_value_traffic} TB',
    align='left',
    dx=5,
    dy=-5,
    color='red'
).encode(
    x='开始时间:T',
    y='数据业务流量_TB:Q'
)

min_annotation_traffic = alt.Chart(pd.DataFrame({
    '开始时间': [min_time_traffic], 
    '数据业务流量_TB': [min_value_traffic]
})).mark_text(
    text=f'{min_value_traffic} TB',
    align='left',
    dx=5,
    dy=5,
    color='blue'
).encode(
    x='开始时间:T',
    y='数据业务流量_TB:Q'
)

# 添加平均线
avg_line_traffic = alt.Chart(pd.DataFrame({
    '开始时间': merged_df_grouped['开始时间'],
    '平均数据业务流量': [avg_traffic] * len(merged_df_grouped)
})).mark_line(
    color='green',
    strokeDash=[5, 5]
).encode(
    x='开始时间:T',
    y='平均数据业务流量:Q'
)

avg_annotation_traffic = alt.Chart(pd.DataFrame({
    '开始时间': [merged_df_grouped['开始时间'].max()],
    '平均数据业务流量': [avg_traffic]
})).mark_text(
    text=f'平均 {avg_traffic} TB',
    align='right',
    dx=-5,
    dy=-5,
    color='green'
).encode(
    x='开始时间:T',
    y='平均数据业务流量:Q'
)

line_chart_traffic = line_chart_traffic + max_annotation_traffic + min_annotation_traffic + avg_line_traffic + avg_annotation_traffic

# 使用 Altair 绘制VoNR语音话务量趋势图
line_chart_vonr = alt.Chart(merged_df_grouped).mark_line().encode(
    x='开始时间:T',
    y=alt.Y('VoNR语音话务量_千Erl:Q', title='VoNR语音话务量 (千Erl)'),
    tooltip=['开始时间:T', 'VoNR语音话务量_千Erl:Q']
).properties(
    title='VoNR语音话务量趋势图',
    width=800,
    height=400
)

# VoNR语音话务量标注
max_annotation_vonr = alt.Chart(pd.DataFrame({
    '开始时间': [max_time_vonr],
    'VoNR语音话务量_千Erl': [max_value_vonr]
})).mark_text(
    text=f'{max_value_vonr} 千Erl',
    align='left',
    dx=5,
    dy=-5,
    color='red'
).encode(
    x='开始时间:T',
    y='VoNR语音话务量_千Erl:Q'
)

min_annotation_vonr = alt.Chart(pd.DataFrame({
    '开始时间': [min_time_vonr],
    'VoNR语音话务量_千Erl': [min_value_vonr]
})).mark_text(
    text=f'{min_value_vonr} 千Erl',
    align='left',
    dx=5,
    dy=5,
    color='blue'
).encode(
    x='开始时间:T',
    y='VoNR语音话务量_千Erl:Q'
)

# 添加平均线
avg_line_vonr = alt.Chart(pd.DataFrame({
    '开始时间': merged_df_grouped['开始时间'],
    '平均VoNR语音话务量': [avg_vonr] * len(merged_df_grouped)
})).mark_line(
    color='green',
    strokeDash=[5, 5]
).encode(
    x='开始时间:T',
    y='平均VoNR语音话务量:Q'
)

avg_annotation_vonr = alt.Chart(pd.DataFrame({
    '开始时间': [merged_df_grouped['开始时间'].max()],
    '平均VoNR语音话务量': [avg_vonr]
})).mark_text(
    text=f'平均 {avg_vonr} 千Erl',
    align='right',
    dx=-5,
    dy=-5,
    color='green'
).encode(
    x='开始时间:T',
    y='平均VoNR语音话务量:Q'
)

line_chart_vonr = line_chart_vonr + max_annotation_vonr + min_annotation_vonr + avg_line_vonr + avg_annotation_vonr

# 计算零流量小区数据
zero_traffic_counts = merged_df[merged_df["数据业务流量"] == 0].groupby('开始时间')['ID'].nunique().reset_index()

# 合并零流量小区数量和总小区数量
zero_traffic_trend = pd.merge(zero_traffic_counts, merged_df_grouped[['开始时间', 'ID']], 
                            on='开始时间', suffixes=('_zero', '_total'))
zero_traffic_trend['零流量小区比例'] = (zero_traffic_trend['ID_zero'] / zero_traffic_trend['ID_total'] * 100).round(2)

# 找到零流量小区数量和比例的最大值和最小值
max_value_zero = zero_traffic_trend['ID_zero'].max()
min_value_zero = zero_traffic_trend['ID_zero'].min()
max_time_zero = zero_traffic_trend[zero_traffic_trend['ID_zero'] == max_value_zero]['开始时间'].iloc[0]
min_time_zero = zero_traffic_trend[zero_traffic_trend['ID_zero'] == min_value_zero]['开始时间'].iloc[0]

max_ratio = zero_traffic_trend['零流量小区比例'].max()
min_ratio = zero_traffic_trend['零流量小区比例'].min()
max_ratio_time = zero_traffic_trend[zero_traffic_trend['零流量小区比例'] == max_ratio]['开始时间'].iloc[0]
min_ratio_time = zero_traffic_trend[zero_traffic_trend['零流量小区比例'] == min_ratio]['开始时间'].iloc[0]

# 绘制零流量小区趋势图
bar_chart_zero_traffic = alt.Chart(zero_traffic_trend).mark_bar().encode(
    x='开始时间:T',
    y=alt.Y('ID_zero:Q', 
            title='零流量小区数量',
            scale=alt.Scale(domain=[0, max_value_zero * 2])),
    tooltip=['开始时间:T', 'ID_zero:Q']
).properties(
    title='零流量小区趋势图',
    width=800,
    height=400
)

# 绘制零流量小区比例趋势线
line_chart_zero_traffic_ratio = alt.Chart(zero_traffic_trend).mark_line(color='orange').encode(
    x='开始时间:T',
    y=alt.Y('零流量小区比例:Q', 
            title='零流量小区比例 (%)',
            scale=alt.Scale(domain=[0, max_ratio * 0.8])),
    tooltip=['开始时间:T', '零流量小区比例:Q']
).properties(
    width=800,
    height=400
)

# 添加数量标注
max_annotation_zero = alt.Chart(pd.DataFrame({
    '开始时间': [max_time_zero],
    'ID_zero': [max_value_zero]
})).mark_text(
    text=f'{max_value_zero}',
    align='left',
    dx=5,
    dy=-5,
    color='red'
).encode(
    x='开始时间:T',
    y=alt.Y('ID_zero:Q', scale=alt.Scale(domain=[0, max_value_zero * 2]))
)

min_annotation_zero = alt.Chart(pd.DataFrame({
    '开始时间': [min_time_zero],
    'ID_zero': [min_value_zero]
})).mark_text(
    text=f'{min_value_zero}',
    align='left',
    dx=5,
    dy=5,
    color='blue'
).encode(
    x='开始时间:T',
    y=alt.Y('ID_zero:Q', scale=alt.Scale(domain=[0, max_value_zero * 2]))
)

# 添加比例标注
max_ratio_annotation = alt.Chart(pd.DataFrame({
    '开始时间': [max_ratio_time],
    '零流量小区比例': [max_ratio]
})).mark_text(
    text=f'{max_ratio}%',
    align='left',
    dx=5,
    dy=-5,
    color='red'
).encode(
    x='开始时间:T',
    y=alt.Y('零流量小区比例:Q', scale=alt.Scale(domain=[0, max_ratio * 0.8]))
)

min_ratio_annotation = alt.Chart(pd.DataFrame({
    '开始时间': [min_ratio_time],
    '零流量小区比例': [min_ratio]
})).mark_text(
    text=f'{min_ratio}%',
    align='left',
    dx=5,
    dy=5,
    color='blue'
).encode(
    x='开始时间:T',
    y=alt.Y('零流量小区比例:Q', scale=alt.Scale(domain=[0, max_ratio * 0.8]))
)

# 组合图表
combined_chart_zero_traffic = alt.layer(
    bar_chart_zero_traffic + max_annotation_zero + min_annotation_zero,
    line_chart_zero_traffic_ratio + max_ratio_annotation + min_ratio_annotation
).resolve_scale(
    y='independent'
)

# 使用 Streamlit 显示图表
st.subheader('话务量和业务量趋势图')

# 创建两列布局并显示图表
with st.container():
    col1, col2 = st.columns(2)
    col1.altair_chart(line_chart_traffic, use_container_width=True)
    col2.altair_chart(line_chart_vonr, use_container_width=True)

# 显示零流量小区趋势图
st.subheader('零流量小区趋势图')
st.altair_chart(combined_chart_zero_traffic, use_container_width=True)