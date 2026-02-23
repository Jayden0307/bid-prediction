import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정 및 다크 모드 커스텀 디자인 (CSS)
st.set_page_config(page_title="Top-Tier Bid Predictor", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stHeader { color: #10b981; }
    </style>
    """, unsafe_allow_html=True)

# 2. 가상 데이터 생성 함수 (실제 데이터 연동 전 테스트용)
@st.cache_data
def load_data():
    dates = pd.date_range(start='2020-01-01', end=datetime.now(), freq='D')
    df = pd.DataFrame({
        'date': np.random.choice(dates, 1000),
        'agency': np.random.choice(['조달청', 'LH공사', '경기도', '한국전력'], 1000),
        'bid_rate': np.random.normal(100.05, 0.4, 1000)
    })
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date', ascending=False)

df = load_data()

# 3. 사이드바 - 전략적 가중치 설정
with st.sidebar:
    st.header("⚙️ 전략 파라미터")
    selected_agency = st.selectbox("발주처 선택", ["전체"] + list(df['agency'].unique()))
    half_life = st.slider("시간 가중치 반감기 (일)", 30, 365, 180, help="최신 데이터에 얼마나 민감하게 반응할지 결정합니다.")
    st.info("반감기가 짧을수록 최근 입찰 경향을 더 강하게 반영합니다.")

# 4. 데이터 분석 로직 (시간 가중치 적용)
current_date = datetime.now()
df['days_diff'] = (current_date - df['date']).dt.days
df['weight'] = np.exp(-np.log(2) * df['days_diff'] / half_life)

if selected_agency != "전체":
    df_final = df[df['agency'] == selected_agency].copy()
else:
    df_final = df.copy()

# 5. 메인 UI 구성
st.title("🎯 입찰 사정률 전략 분석 엔진")
st.markdown("---")

# KPI 카드 섹션
col1, col2, col3 = st.columns(3)
weighted_mean = np.average(df_final['bid_rate'], weights=df_final['weight'])
raw_mean = df_final['bid_rate'].mean()

with col1:
    st.metric("추천 타겟 사정률", f"{weighted_mean:.4f}%", delta=f"{(weighted_mean - 100):.4f}%")
with col2:
    st.metric("데이터 신뢰도 (최근 1년)", f"{len(df_final[df_final['days_diff'] < 365])}건")
with col3:
    st.metric("기관 평균 변동성", f"{df_final['bid_rate'].std():.3f}")

# 시각화 섹션
st.subheader("📊 사정률 확률 밀도 분석 (Probability Density)")
fig = go.Figure()
fig.add_trace(go.Violin(x=df_final['bid_rate'], line_color='#6366f1', fillcolor='#818cf8', opacity=0.6, name="밀도 분포"))
fig.add_vline(x=weighted_mean, line_dash="dash", line_color="#10b981", annotation_text="최적 구간")
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

# 데이터 테이블
with st.expander("📝 분석 원천 데이터 확인"):
    st.dataframe(df_final[['date', 'agency', 'bid_rate', 'weight']].head(50), use_container_width=True)

# 파일 업로더 위젯 추가
uploaded_file = st.sidebar.file_uploader("📂 분석할 엑셀/CSV 파일을 선택하세요", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 사용자가 파일을 올리면 해당 데이터 읽기
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # 여기서부터는 업로드된 df를 바탕으로 가중치 및 사정률 실시간 계산
    st.success("데이터가 성공적으로 로드되었습니다!")
else:
    # 파일을 올리기 전에는 안내 문구 표시
    st.info("좌측 사이드바에서 데이터를 업로드하면 실시간 예측이 시작됩니다.")
