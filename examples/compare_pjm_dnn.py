import os
import pandas as pd

# 基于当前脚本位置构造绝对路径，避免工作目录不同导致路径错误
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_PATH = os.path.join(BASE_DIR, "datasets", "PJM.csv")
FORECAST_PATH = os.path.join(
    BASE_DIR,
    "experimental_files",
    "DNN_forecast_nl2_datPJM_YT2_SFH1_CW4_1.csv",
)
OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "experimental_files",
    "PJM_vs_DNN_hourly_compare.csv",
)

print("当前脚本目录:", BASE_DIR)
print("真实数据路径:", DATASETS_PATH)
print("预测结果路径:", FORECAST_PATH)
print("输出文件路径:", OUTPUT_PATH)

# 1. 读真实电价（小时级）
df_real = pd.read_csv(DATASETS_PATH, index_col=0, parse_dates=True)

# 标准化列名，兼容原始文件中带空格的列，如 " Zonal COMED price"
df_real.columns = [c.strip() for c in df_real.columns]

# 将第一列视为价格列，统一命名为 "Price"
if len(df_real.columns) > 0:
    price_col = df_real.columns[0]
    df_real = df_real.rename(columns={price_col: "Price"})
else:
    raise ValueError("PJM.csv 中未发现任何数据列，请检查文件格式。")

# 2. 读预测结果（天 × 24 小时）
df_pred_day = pd.read_csv(FORECAST_PATH, index_col=0, parse_dates=True)

# 3. 只取测试区间内的真实价格（和示例脚本一致）
start_date = "2016-12-27"
end_date = "2017-03-01"
df_real = df_real.loc[f"{start_date} 00:00:00" : f"{end_date} 23:00:00"]

# 4. 把“按天 24 列”的预测，展开成“按小时一行”
records = []
for day, row in df_pred_day.iterrows():
    for h in range(24):
        ts = pd.Timestamp(day) + pd.Timedelta(hours=h)
        records.append((ts, row[f"h{h}"]))

df_pred_hourly = pd.DataFrame(records, columns=["Date", "Pred"]).set_index("Date")

# 5. 和真实电价按时间对齐
df_compare = df_real[["Price"]].rename(columns={"Price": "Real"}).join(
    df_pred_hourly, how="inner"
)

# 6. 计算简单指标（比如 MAE），顺便看几行
df_compare["abs_err"] = (df_compare["Pred"] - df_compare["Real"]).abs()
mae = df_compare["abs_err"].mean()

print("样本条数：", len(df_compare))
print("MAE：", mae)
print(df_compare.head())

# 如果想拿到一张方便在 Excel 里看的对比表：
df_compare.to_csv(OUTPUT_PATH)
print("对比结果已保存到:", OUTPUT_PATH)
