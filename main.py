import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ----------------------------
# 페이지 기본 설정
# ----------------------------
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide",
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


# ----------------------------
# 데이터 불러오기 (캐시로 속도 향상)
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year
    return df


df = load_data()

# ----------------------------
# 제목 및 소개
# ----------------------------
st.title("🌡️ 서울, 100년 동안 얼마나 더워졌을까?")
st.markdown(
    """
서울의 **날마다 측정된 기온 기록**을 모아서,
지난 100년이 넘는 기간 동안 **연평균 기온이 어떻게 변해왔는지** 살펴봅니다.

데이터 출처: 기상청 서울(지점번호 108) 관측 자료
"""
)

st.divider()

# ----------------------------
# 연도별 평균 기온 계산
# ----------------------------
yearly = (
    df.groupby("연도")["평균기온"]
    .mean()
    .reset_index()
    .rename(columns={"평균기온": "연평균기온"})
)

# 관측 일수가 너무 적은(자료가 불완전한) 연도는 제외해서 왜곡을 줄임
counts = df.groupby("연도")["평균기온"].count()
valid_years = counts[counts >= 300].index
yearly = yearly[yearly["연도"].isin(valid_years)].reset_index(drop=True)

min_year = int(yearly["연도"].min())
max_year = int(yearly["연도"].max())

# ----------------------------
# 사이드바: 기간 선택
# ----------------------------
st.sidebar.header("📅 기간 선택")
year_range = st.sidebar.slider(
    "살펴보고 싶은 연도 범위를 골라보세요",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

filtered = yearly[
    (yearly["연도"] >= year_range[0]) & (yearly["연도"] <= year_range[1])
]

# ----------------------------
# 핵심 요약 지표
# ----------------------------
col1, col2, col3 = st.columns(3)

first_temp = filtered["연평균기온"].iloc[0]
last_temp = filtered["연평균기온"].iloc[-1]
temp_diff = last_temp - first_temp

with col1:
    st.metric(
        label=f"{int(filtered['연도'].iloc[0])}년 연평균 기온",
        value=f"{first_temp:.1f} °C",
    )

with col2:
    st.metric(
        label=f"{int(filtered['연도'].iloc[-1])}년 연평균 기온",
        value=f"{last_temp:.1f} °C",
    )

with col3:
    st.metric(
        label="선택 기간 동안의 변화",
        value=f"{temp_diff:+.1f} °C",
        delta=f"{temp_diff:+.2f} °C",
    )

st.divider()

# ----------------------------
# 그래프: 연평균 기온 추세
# ----------------------------
st.subheader("📈 연평균 기온 변화 그래프")

# 추세선 계산 (선형 회귀)
x = filtered["연도"].values
y = filtered["연평균기온"].values
coeffs = np.polyfit(x, y, 1)
trend = np.poly1d(coeffs)
slope_per_10yr = coeffs[0] * 10

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=filtered["연도"],
        y=filtered["연평균기온"],
        mode="lines+markers",
        name="연평균 기온",
        line=dict(color="#f4a300", width=2),
        marker=dict(size=5),
    )
)

fig.add_trace(
    go.Scatter(
        x=filtered["연도"],
        y=trend(x),
        mode="lines",
        name="전체 추세선",
        line=dict(color="#e74c3c", width=3, dash="dash"),
    )
)

fig.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균 기온 (°C)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500,
)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# 추세 설명 (쉬운 말로)
# ----------------------------
if slope_per_10yr > 0:
    st.success(
        f"🔺 선택한 기간 동안 서울의 기온은 **10년마다 평균 약 {slope_per_10yr:.2f}°C씩 올라가는 추세**예요. "
        "빨간 점선은 전체 흐름을 대표하는 추세선입니다."
    )
else:
    st.info(
        f"선택한 기간 동안 서울의 기온은 **10년마다 평균 약 {abs(slope_per_10yr):.2f}°C씩 내려가는 추세**로 나타났어요."
    )

st.caption(
    "※ 하루 중 관측 기록이 부족해 자료가 불완전한 연도는 그래프에서 제외했습니다."
)

st.divider()

# ----------------------------
# 원자료 살짝 보여주기
# ----------------------------
with st.expander("🔍 연도별 평균 기온 표로 보기"):
    st.dataframe(
        filtered.rename(columns={"연도": "연도", "연평균기온": "연평균 기온(°C)"}).round(2),
        use_container_width=True,
        hide_index=True,
    )
