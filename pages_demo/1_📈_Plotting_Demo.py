import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.interpolate import make_interp_spline
import numpy as np

# 定义数据目录和文件名
Datadir = r'C:\Users\Administrator\Documents\MnewData'
gdf_filename = 'gdf_RAC.csv'
KPI_filename = 'df_KPI.csv'

# 构建文件路径
file_path1 = os.path.join(Datadir, gdf_filename)
file_path2 = os.path.join(Datadir, KPI_filename)

@st.cache_data
def load_data():
    # 读取CSV文件
    gdf_RAC = pd.read_csv(file_path1, encoding='utf8')
    df_KPI = pd.read_csv(file_path2, encoding='utf8')

    # 将[开始时间]和[结束时间]列定义为日期格式
    df_KPI['开始时间'] = pd.to_datetime(df_KPI['开始时间'], errors='coerce')
    df_KPI['结束时间'] = pd.to_datetime(df_KPI['结束时间'], errors='coerce')

    # 将[R2035_003]至[R1001_019]列定义为整数
    int_columns = df_KPI.loc[:, 'R2035_003':'R1001_019'].columns
    df_KPI[int_columns] = df_KPI[int_columns].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)

    # 将[K1009_001]和[K1009_002]列定义为保留两位小数的小数
    df_KPI['K1009_001'] = pd.to_numeric(df_KPI['K1009_001'], errors='coerce').fillna(0).round(2)
    df_KPI['K1009_002'] = pd.to_numeric(df_KPI['K1009_002'], errors='coerce').fillna(0).round(2)

    # 合并数据框
    merged_df = pd.merge(df_KPI, gdf_RAC, on='ID', how='left')

    # 构建新的列顺序
    desired_columns = ['ID', '开始时间', '工作频段', '网元标识', '小区本地ID', '小区名称', 'Longitude', 'Latitude', '省份', '地市', '县区', '镇区', '村区']
    kpi_columns = merged_df.loc[:, 'R2035_003':'K1009_002'].columns.tolist()
    columns_order = desired_columns + kpi_columns

    # 重新排列数据框的列
    merged_df = merged_df[columns_order]

    return merged_df

def calculate_all_metrics(df):
    df["最大RRC连接用户数"] = df["R1504_002"]
    df["平均RRC连接用户数"] = df["R1504_001"] / df["R1504_029"]
    df["下行PDCP层业务流量"] = df["R2032_012"] / 1000 / 1000
    df["上行PDCP层业务流量"] = df["R2032_001"] / 1000 / 1000
    df["总流量"] = (df["R1012_001"] + df["R1012_002"]) / 1000000
    return df

def custom_grouping(df):
    # 按时间分组，统计不重复的['网元标识']和['小区名称']的数量
    grouped_df = df.groupby('开始时间').agg({
        '网元标识': pd.Series.nunique, 
        '小区名称': pd.Series.nunique,
        '总流量': lambda x: (x == 0).sum()  # 统计总流量为0的小区友好名数量
    }).reset_index()
    grouped_df.rename(columns={'网元标识': '不重复网元标识数量', '小区名称': '不重复小区名称数量', '总流量': '总流量为0的小区数量'}, inplace=True)
    return grouped_df

st.title("KPI Data Analysis")

# 加载数据
data_load_state = st.text('Loading data...')
merged_df = load_data()
data_load_state.text("Done! (using st.cache_data)")

# 提取并打印列名列表
list1 = merged_df.columns.to_list()
print(list1)

# 计算所有指标
merged_df = calculate_all_metrics(merged_df)

# 获取时间范围
min_date = merged_df['开始时间'].min().date()
max_date = merged_df['开始时间'].max().date()

# 筛选框
st.sidebar.header('Filter Options')
start_date, end_date = st.sidebar.slider("Select date range", min_value=min_date, max_value=max_date, value=(min_date, max_date))
selected_provinces = st.sidebar.multiselect('Select Province', options=merged_df['省份'].unique(), default=merged_df['省份'].unique())
selected_cities = st.sidebar.multiselect('Select City', merged_df[merged_df['省份'].isin(selected_provinces)]['地市'].unique())
selected_counties = st.sidebar.multiselect('Select County', merged_df[(merged_df['地市'].isin(selected_cities))]['县区'].unique())

# 根据筛选条件过滤数据
filtered_df = merged_df[(merged_df['开始时间'].dt.date >= start_date) & (merged_df['开始时间'].dt.date <= end_date)]
if selected_provinces:
    filtered_df = filtered_df[filtered_df['省份'].isin(selected_provinces)]
if selected_cities:
    filtered_df = filtered_df[filtered_df['地市'].isin(selected_cities)]
if selected_counties:
    filtered_df = filtered_df[filtered_df['县区'].isin(selected_counties)]

# 分组计算
grouped_df = custom_grouping(filtered_df)

# 显示数据框
if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(merged_df)  # 显示原始数据

# 显示分组后的数据框
if st.checkbox('Show grouped data'):
    st.subheader('Grouped data by Date')
    st.write(grouped_df)

# 绘制柱线图
if st.checkbox('Show Bar-Line Chart'):
    st.subheader('Bar-Line Chart of Unique Identifiers and Zero Traffic Cells by Date')
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # 使用中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 绘制柱状图
    ax1.bar(grouped_df['开始时间'], grouped_df['不重复网元标识数量'], color='b', alpha=0.6, label='不重复网元标识数量')
    ax1.bar(grouped_df['开始时间'], grouped_df['不重复小区名称数量'], color='g', alpha=0.6, label='不重复小区名称数量', bottom=grouped_df['不重复网元标识数量'])

    ax1.set_xlabel('时间')
    ax1.set_ylabel('数量')
    ax1.legend(loc='upper left')

    # 创建第二个y轴
    ax2 = ax1.twinx()
    ax2.plot(grouped_df['开始时间'], grouped_df['总流量为0的小区数量'], color='r', marker='o', label='总流量为0的小区数量')
    ax2.set_ylabel('总流量为0的小区数量')
    ax2.legend(loc='upper right')

    plt.title('按时间分组的唯一标识符和总流量为0的小区数量柱线图')
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)