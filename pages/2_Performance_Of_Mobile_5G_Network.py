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
    df = pd.read_csv(os.path.join(directory, file), encoding='utf-8')
    df_KPI = pd.read_csv(os.path.join(directory, file2), encoding='utf-8')
    return df, df_KPI

# 读取数据
df, df_KPI = load_data()

# 显示筛选项
with st.container():
    cols = st.columns([2, 1, 1, 1, 1])  # 调整列宽
    
    # 工作频段筛选
    filtered_bands = df['工作频段'].unique().tolist()
    selected_band = cols[0].selectbox('选择工作频段', ['全部'] + filtered_bands)
    
    # 地市筛选
    filtered_cities = df['地市'].unique().tolist()
    selected_city = cols[1].selectbox('选择地市', ['全部'] + filtered_cities)
    
    # 县区筛选
    filtered_counties = df['县区'].unique().tolist()
    selected_county = cols[2].selectbox('选择县区', ['全部'] + filtered_counties)
    
    # 镇区筛选
    filtered_towns = df['镇区'].unique().tolist()
    selected_town = cols[3].selectbox('选择镇区', ['全部'] + filtered_towns)
    
    # 村区筛选
    filtered_villages = df['村区'].unique().tolist()
    selected_village = cols[4].selectbox('选择村区', ['全部'] + filtered_villages)

# 根据所有选择更新最终的数据筛选
final_df = df.copy()

# 工作频段筛选
if selected_band != '全部':
    final_df = final_df[final_df['工作频段'] == selected_band]

# 地市筛选
if selected_city != '全部':
    final_df = final_df[final_df['地市'] == selected_city]

# 县区筛选
if selected_county != '全部':
    final_df = final_df[final_df['县区'] == selected_county]

# 镇区筛选
if selected_town != '全部':
    final_df = final_df[final_df['镇区'] == selected_town]

# 村区筛选
if selected_village != '全部':
    final_df = final_df[final_df['村区'] == selected_village]

# 合并数据框
merged_df = pd.merge(df_KPI, final_df, on='ID', how='left')

# 时间范围选择使用 select_slider
min_date = pd.to_datetime(merged_df['开始时间']).min().date()
max_date = pd.to_datetime(merged_df['开始时间']).max().date()

selected_date_range = st.select_slider(
    '选择时间范围', 
    options=pd.date_range(min_date, max_date).date.tolist(),
    value=(min_date, max_date)
)

# 时间范围筛选
merged_df['开始时间'] = pd.to_datetime(merged_df['开始时间']).dt.date
merged_df = merged_df[
    (merged_df['开始时间'] >= selected_date_range[0]) & 
    (merged_df['开始时间'] <= selected_date_range[1])
]

# 恢复datetime类型
merged_df['开始时间'] = pd.to_datetime(merged_df['开始时间'])

# 数据聚合函数
def aggregate_data(df):
    # 确保开始时间列是datetime类型
    df['开始时间'] = pd.to_datetime(df['开始时间'])
    
    # 按时间聚合原始数据
    agg_df = df.groupby('开始时间').agg({
        'R1012_001': 'sum',
        'R1012_002': 'sum',
        'R1001_012': 'sum',
        'R1001_001': 'sum',
        'R1034_012': 'sum',
        'R1034_001': 'sum',
        'R1039_002': 'sum',
        'R1039_001': 'sum',
        'R1004_003': 'sum',
        'R1004_004': 'sum',
        'R1004_002': 'sum',
        'R1004_007': 'sum',
        'R1005_012': 'sum',
        'R1006_012': 'sum',
        'R2007_002': 'sum',
        'R2007_004': 'sum',
        'R2006_004': 'sum',
        'R2006_008': 'sum',
        'R2005_004': 'sum',
        'R2005_008': 'sum',
        'R2007_001': 'sum',
        'R2007_003': 'sum',
        'R2006_001': 'sum',
        'R2006_005': 'sum',
        'R2005_001': 'sum',
        'R2005_005': 'sum',
        'K1009_001': 'sum',
        'R1034_013': 'sum',
        'R1034_002': 'sum',
        'R1001_018': 'sum',
        'R1001_015': 'sum',
        'R1001_007': 'sum',
        'R1001_004': 'sum',
        'R2035_003': 'sum',
        'R2035_013': 'sum',
        'R2035_026': 'sum',
        'R2005_063': 'sum',
        'R2005_067': 'sum',
        'R2006_071': 'sum',
        'R2006_075': 'sum',
        'R2007_036': 'sum',
        'R2007_040': 'sum',
        'R2005_060': 'sum',
        'R2005_064': 'sum',
        'R2006_068': 'sum',
        'R2006_072': 'sum',
        'R2007_033': 'sum',
        'R2007_037': 'sum'
    }).reset_index()
    
    # 使用聚合后的数据计算指标，并调整单位
    agg_df["数据业务流量"] = (agg_df["R1012_001"] + agg_df["R1012_002"]) / 1000000000  # 转换为TB
    agg_df["VoNR语音话务量"] = (agg_df["K1009_001"] / 4) / 1000  # 转换为千Erl
    agg_df["无线接通率"] = (agg_df["R1001_012"] / agg_df["R1001_001"]) * (agg_df["R1034_012"] / agg_df["R1034_001"]) * (agg_df["R1039_002"] / agg_df["R1039_001"]) * 100
    agg_df["无线掉线率"] = 100 * (agg_df["R1004_003"] - agg_df["R1004_004"]) / (agg_df["R1004_002"] + agg_df["R1004_007"] + agg_df["R1005_012"] + agg_df["R1006_012"])
    agg_df["系统内切换成功率"] = 100 * ((agg_df["R2007_002"] + agg_df["R2007_004"] + agg_df["R2006_004"] + agg_df["R2006_008"] + agg_df["R2005_004"] + agg_df["R2005_008"]) / (agg_df["R2007_001"] + agg_df["R2007_003"] + agg_df["R2006_001"] + agg_df["R2006_005"] + agg_df["R2005_001"] + agg_df["R2005_005"]))
    agg_df["VoNR无线接通率"] = 100 * (agg_df["R1034_013"] / agg_df["R1034_002"]) * (agg_df["R1001_018"] + agg_df["R1001_015"]) / (agg_df["R1001_007"] + agg_df["R1001_004"])
    agg_df["VoNR语音掉线率"] = 100 * ((agg_df["R2035_003"] - agg_df["R2035_013"]) / (agg_df["R2035_003"] + agg_df["R2035_026"]))
    agg_df["VoNR系统内切换成功率"] = 100 * (agg_df["R2005_063"] + agg_df["R2005_067"] + agg_df["R2006_071"] + agg_df["R2006_075"] + agg_df["R2007_036"] + agg_df["R2007_040"]) / (agg_df["R2005_060"] + agg_df["R2005_064"] + agg_df["R2006_068"] + agg_df["R2006_072"] + agg_df["R2007_033"] + agg_df["R2007_037"])
    
    # 四舍五入到2位小数以减少数据量
    for col in agg_df.columns:
        if col != '开始时间':
            agg_df[col] = agg_df[col].round(2)
    
    return agg_df

# 创建带最大最小值的图表的函数
def create_chart_with_extremes(data, y_field, title, y_title, is_full_width=False):
    # 设置图表基础配置
    config = {
        "view": {"strokeWidth": 0},  # 移除图表边框
        "title": {
            "fontSize": 12,
            "anchor": "middle",  # 标题居中
            "offset": 18,  # 标题与图表的距离
            "color": "#333333"  # 标题颜色
        },
        "axis": {
            "labelFontSize": 10,  # 轴标签字体大小
            "titleFontSize": 12,  # 轴标题字体大小
            "grid": False  # 移除网格线
        }
    }
    
    # 获取最大最小值
    max_val = data[y_field].max()
    min_val = data[y_field].min()
    max_time = data.loc[data[y_field].idxmax(), '开始时间']
    min_time = data.loc[data[y_field].idxmin(), '开始时间']
    
    # 设置图表宽度和高度
    width = 1200 if is_full_width else 380
    height = 400 if is_full_width else 320
    
    # 创建基础图表
    base = alt.Chart(data).mark_line(
        color='#5276A7',  # 线条颜色
        strokeWidth=2  # 线条宽度
    ).encode(
        x=alt.X('开始时间:T', 
                title='时间',
                axis=alt.Axis(
                    format='%m-%d',  # 时间格式
                    labelAngle=-45,  # 标签角度
                    titleFontSize=12,  # 横坐标标题字体大小
                    labelFontSize=10,  # 横坐标标签字体大小
                    tickCount=5  # 控制刻度数量
                )),
        y=alt.Y(f'{y_field}:Q', 
                title=y_title,
                scale=alt.Scale(zero=False),  # y轴不从0开始
                axis=alt.Axis(
                    titleFontSize=12,  # 纵坐标标题字体大小
                    labelFontSize=10,  # 纵坐标标签字体大小
                    format='.2f'  # 数值格式
                )),
        tooltip=[
            alt.Tooltip('开始时间:T', title='时间', format='%Y-%m-%d'),
            alt.Tooltip(f'{y_field}:Q', title=y_title, format='.2f')
        ]
    ).properties(
        title=title,
        width=width,
        height=height
    )
    
    # 添加最大值点和标签
    max_point = alt.Chart(pd.DataFrame({
        '开始时间': [max_time], 
        y_field: [max_val]
    })).mark_point(
        color='#FF4B4B',
        size=100,
        filled=True
    ).encode(
        x='开始时间:T',
        y=f'{y_field}:Q'
    )
    
    max_text = alt.Chart(pd.DataFrame({
        '开始时间': [max_time], 
        y_field: [max_val]
    })).mark_text(
        align='left',
        dx=5,
        dy=-10,
        color='#FF4B4B',
        fontSize=10
    ).encode(
        x='开始时间:T',
        y=f'{y_field}:Q',
        text=alt.Text(f'{y_field}:Q', format='.2f')
    )
    
    # 添加最小值点和标签
    min_point = alt.Chart(pd.DataFrame({
        '开始时间': [min_time], 
        y_field: [min_val]
    })).mark_point(
        color='#4B4BFF',
        size=100,
        filled=True
    ).encode(
        x='开始时间:T',
        y=f'{y_field}:Q'
    )
    
    min_text = alt.Chart(pd.DataFrame({
        '开始时间': [min_time], 
        y_field: [min_val]
    })).mark_text(
        align='left',
        dx=5,
        dy=10,
        color='#4B4BFF',
        fontSize=10
    ).encode(
        x='开始时间:T',
        y=f'{y_field}:Q',
        text=alt.Text(f'{y_field}:Q', format='.2f')
    )
    
    # 组合所有图层并配置
    return (base + max_point + min_point + max_text + min_text).configure(**config)

# 处理和聚合数据
agg_df = aggregate_data(merged_df)

# 创建图表
chart_traffic = create_chart_with_extremes(
    agg_df,
    '数据业务流量',
    '数据业务流量',
    '数据业务流量 (TB)',
    is_full_width=True
)

chart_vonr_traffic = create_chart_with_extremes(
    agg_df,
    'VoNR语音话务量',
    'VoNR语音话务量',
    'VoNR语音话务量 (千Erl)',
    is_full_width=True
)

chart_connection = create_chart_with_extremes(
    agg_df,
    '无线接通率',
    '无线接通率',
    '无线接通率 (%)'
)

chart_drop = create_chart_with_extremes(
    agg_df,
    '无线掉线率',
    '无线掉线率',
    '无线掉线率 (%)'
)

chart_handover = create_chart_with_extremes(
    agg_df,
    '系统内切换成功率',
    '系统内切换',
    '系统内切换成功率 (%)'
)

chart_vonr_connection = create_chart_with_extremes(
    agg_df,
    'VoNR无线接通率',
    'VoNR无线接通率',
    'VoNR无线接通率 (%)'
)

chart_vonr_drop = create_chart_with_extremes(
    agg_df,
    'VoNR语音掉线率',
    'VoNR语音掉线率',
    'VoNR语音掉线率 (%)'
)

chart_vonr_handover = create_chart_with_extremes(
    agg_df,
    'VoNR系统内切换成功率',
    'VoNR系统内切换',
    'VoNR系统内切换成功率 (%)'
)

# 使用streamlit显示图表
st.subheader('数据业务流量及性能指标')
st.altair_chart(chart_traffic, use_container_width=True)


col1, col2, col3 = st.columns(3)
with col1:
    st.altair_chart(chart_connection, use_container_width=True)
with col2:
    st.altair_chart(chart_drop, use_container_width=True)
with col3:
    st.altair_chart(chart_handover, use_container_width=True)

st.subheader('VoNR语音话务量及性能指标')
st.altair_chart(chart_vonr_traffic, use_container_width=True)


col4, col5, col6 = st.columns(3)
with col4:
    st.altair_chart(chart_vonr_connection, use_container_width=True)
with col5:
    st.altair_chart(chart_vonr_drop, use_container_width=True)
with col6:
    st.altair_chart(chart_vonr_handover, use_container_width=True)