import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# 设置文件路径
directory = r'C:\Data\data'
file = 'df_BRP.csv'

# 缓存读取 CSV 文件的函数
@st.cache_data
def load_data():
    df_PBR = pd.read_csv(os.path.join(directory, file), encoding='utf-8')
    return df_PBR

# 读取数据
df_PBR = load_data()

# 删除包含 'D5S' 的行
df_PBR = df_PBR[~df_PBR['Model'].str.contains('D5S')]

# 删除 'BBU功耗(R1054_001)[W]' 或 'RRU总功耗' 等于 0 的行
df_PBR = df_PBR[(df_PBR['BBU功耗(R1054_001)[W]'] != 0) & (df_PBR['RRU总功耗'] != 0)]

# 计算新的功耗值
df_PBR['设备功耗'] = df_PBR['BBU功耗[千瓦时]'] + (df_PBR['RRU总功耗'] / df_PBR['天线数量']) * 3

# 获取清洗后的 Model 列表
model_list = df_PBR['Model'].unique().tolist()

# Streamlit 部分
st.title("主设备功耗分析")

# 显示清洗后的 Model 列表
st.sidebar.subheader("模型选择")
selected_models = st.sidebar.multiselect("选择模型", model_list, default=model_list)

# 过滤数据根据选择的模型
filtered_df = df_PBR[df_PBR['Model'].isin(selected_models)]

# 计算平均值、最大值和最小值
result = filtered_df.groupby('Model')['设备功耗'].agg(['mean', 'max', 'min']).reset_index()

# 显示计算结果
st.subheader("设备功耗统计")
st.dataframe(result)

# 显示每个 Model 的平均值和与最大值和最小值的比值
for index, row in result.iterrows():
    mean_val = row['mean']
    max_val = row['max']
    min_val = row['min']
    max_ratio = (max_val - mean_val) / mean_val * 100
    min_ratio = (mean_val - min_val) / mean_val * 100

    st.metric(
        label=f"{row['Model']} 平均功耗",
        value=f"{mean_val:.2f} kWh",
        delta=f"最大值比率: {max_ratio:.2f}%, 最小值比率: {min_ratio:.2f}%"
    )

# 以箱线图呈现
st.subheader("功耗分布箱线图")
fig, ax = plt.subplots(figsize=(10, 6))
filtered_df.boxplot(column='设备功耗', by='BBU名称', grid=False, ax=ax)
plt.title('功耗分布箱线图')
plt.suptitle('')  # 去掉默认的子标题
plt.xlabel('BBU名称')
plt.ylabel('设备功耗')
st.pyplot(fig)