import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="입찰 사정률 예측 시스템", layout="wide")
st.title("📊 입찰 사정률 분석 및 예측 대시보드")

# 2. 가상 데이터 생성 (실제 데이터 DB 연결 시 이 부분을 수정)
@st.cache_data
def load_data():
    # 10년치 가상 데이터 생성
    dates = pd.date_range(start='2016-01-01', end=datetime.now(), freq='D')
    data = pd.DataFrame({
        'date': np.random.choice(dates, 2000),
        'agency': np.random.choice(['조달청', 'LH', '서울시', '경기도'], 2000),
        'base_price': np.random.randint(100, 1000, 2000) * 1000000,
        'bid_rate': np.random.normal(100.0, 0.5, 2000)  # 사정률 100% 기준 분포
    })
    data['date'] = pd.to_datetime(data['date'])
    return data.sort_values('date', ascending=False)

df = load_data()

# 3. 사이드바 - 분석 필터 설정
st.sidebar.header("🔍 분석 설정")
selected_agency = st.sidebar.selectbox("발주처 선택", ["전체"] + list(df['agency'].unique()))
half_life = st.sidebar.slider("가중치 반감기 (일)", 30, 365, 180)

# 데이터 필터링
if selected_agency != "전체":
    df_filtered = df[df['agency'] == selected_agency].copy()
else:
    df_filtered = df.copy()

# 4. 시간 가중치 계산 (최신 데이터 엣지 확보)
current_date = datetime.now()
df_filtered['days_diff'] = (current_date - df_filtered['date']).dt.days
# 지수 감쇠 가중치 계산: e^(-ln(2) * t / 반감기)
df_filtered['weight'] = np.exp(-np.log(2) * df_filtered['days_diff'] / half_life)

# 5. 대시보드 메인 지표 (KPI)
weighted_mean = np.average(df_filtered['bid_rate'], weights=df_filtered['weight'])
raw_mean = df_filtered['bid_rate'].mean()

col1, col2, col3 = st.columns(3)
col1.metric("예측 사정률 (가중치 적용)", f"{weighted_mean:.4f}%")
col2.metric("전체 평균 사정률", f"{raw_mean:.4f}%")
col3.metric("분석 데이터 수", f"{len(df_filtered)}건")

# 6. 시각화 - 사정률 분포 (히스토그램)
st.subheader("📈 사정률 분포 분석")
fig = px.histogram(df_filtered, x="bid_rate", nbins=50, 
                   title=f"[{selected_agency}] 사정률 빈도수",
                   labels={'bid_rate': '사정률 (%)'})
fig.add_vline(x=weighted_mean, line_dash="dash", line_color="red", annotation_text="예측치")
st.plotly_chart(fig, use_container_width=True)

# 7. 최근 낙찰 데이터 리스트
st.subheader("📑 최근 데이터 상세 (가중치 높은 순)")
st.dataframe(df_filtered[['date', 'agency', 'base_price', 'bid_rate', 'weight']].head(20))
