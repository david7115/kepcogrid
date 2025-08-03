import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from utils.kepco_api import KEPCOService
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(
    page_title="한국전력공사 신재생에너지 계통접속 용량 조회 시스템",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 스타일 추가
st.markdown("""
<style>
    /* 전체 배경 */
    .main .element-container {
        background-color: #f8f9fa;
    }
    
    /* 깔끔한 전체 레이아웃 */
    .main .block-container {
        padding: 1rem 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* 사이드바 최소화 */
    .css-1d391kg {
        width: 280px !important;
    }
    
    .css-1cypcdb {
        width: 280px !important;
    }
    
    /* 제목 스타일 */
    .main h1 {
        color: #2c3e50;
        font-weight: bold;
        border-bottom: 3px solid #e74c3c;
        padding-bottom: 10px;
        margin-bottom: 1rem;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        justify-content: left;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 4px;
        border: none;
        font-weight: bold;
        height: auto;
        min-height: 40px;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    
    /* 검색 버튼 */
    .stButton > button[data-testid="baseButton-primaryButton"] {
        background-color: #e74c3c !important;
        color: white !important;
    }
    
    /* 메트릭 카드 */
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #e9ecef;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 정보 카드 */
    .info-card {
        background-color: white;
        padding: 8px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        min-height: 110px;
    }
    
    /* 검색 결과 데이터 스타일링 */
    .capacity-data {
        font-weight: bold;
        font-size: 14px;
        line-height: 1.3;
        margin: 4px 0;
    }
    
    .facility-name {
        color: #2c3e50;
        font-size: 18px;
    }
    
    .capacity-value {
        color: #27ae60;
        font-size: 17px;
    }
    
    .received-capacity {
        color: #8e44ad;
        font-size: 17px;
    }
    
    .remaining-capacity {
        color: #e74c3c;
        font-size: 17px;
    }
    
    .status-normal {
        color: #27ae60;
        font-size: 17px;
        background-color: #d4edda;
        padding: 2px 8px;
        border-radius: 4px;
    }
    
    .status-saturated {
        color: #dc3545;
        font-size: 17px;
        background-color: #f8d7da;
        padding: 2px 8px;
        border-radius: 4px;
    }
    
    /* 모바일 최적화 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem;
            max-width: 100%;
        }
        
        .metric-card {
            padding: 10px;
            margin: 5px 0;
            font-size: 12px;
        }
        
        .info-card {
            padding: 8px;
            min-height: 100px;
            margin: 3px 0;
        }
        
        .capacity-data {
            font-size: 12px !important;
            line-height: 1.2;
            margin: 2px 0;
            word-wrap: break-word;
        }
        
        .facility-name {
            font-size: 13px !important;
        }
        
        .capacity-value, .received-capacity, .remaining-capacity {
            font-size: 12px !important;
        }
        
        .status-normal, .status-saturated {
            font-size: 11px !important;
            padding: 1px 4px;
        }
        
        /* 모바일에서 컬럼 간격 축소 */
        [data-testid="column"] {
            padding: 0 2px !important;
        }
        
        /* 헤더 텍스트 크기 조정 */
        h1 {
            font-size: 18px !important;
        }
        
        h2 {
            font-size: 16px !important;
        }
        
        h3 {
            font-size: 14px !important;
        }
        
        h4 {
            font-size: 12px !important;
            margin-bottom: 4px !important;
        }
        
        /* 사이드바 최적화 */
        .css-1d391kg {
            padding: 1rem 0.5rem;
        }
        
        /* 버튼 크기 조정 */
        .stButton > button {
            font-size: 12px;
            padding: 0.3rem 0.5rem;
            min-height: 32px;
        }
        
        /* 셀렉트박스 텍스트 크기 */
        .stSelectbox label {
            font-size: 12px !important;
        }
        
        /* 차트 컨테이너 최적화 */
        .js-plotly-plot {
            margin: 5px 0;
        }
        
        /* 메인 메뉴 버튼 모바일 최적화 */
        .stButton > button {
            font-size: 12px !important;
            padding: 0.5rem !important;
            min-height: 60px !important;
            white-space: normal !important;
            line-height: 1.2 !important;
            word-wrap: break-word !important;
        }
        
        /* 입력 폼 최적화 */
        .stTextInput > div > div > input {
            font-size: 14px !important;
        }
        
        /* 탭 텍스트 크기 조정 */
        .stTabs [data-baseweb="tab"] {
            padding: 5px 10px !important;
            font-size: 12px !important;
        }
        
        /* 메트릭 값 텍스트 크기 */
        [data-testid="metric-container"] {
            font-size: 12px !important;
        }
        
        /* 사이드바 컨트롤 최적화 */
        .stSlider > div > div > div {
            font-size: 12px !important;
        }
        
        /* 검색 히스토리 최적화 */
        .stExpander > div > div {
            font-size: 12px !important;
        }
        
        /* 제목 모바일 최적화 */
        .main h1 {
            font-size: 18px !important;
            text-align: center;
            margin-bottom: 0.8rem !important;
            padding-bottom: 5px !important;
        }
        
        /* 컬럼 간격 최적화 */
        .row-widget.stSelectbox > div {
            gap: 0.25rem !important;
        }
        
        /* 스크롤 최적화 */
        .main .block-container {
            padding: 0.5rem 0.8rem !important;
            overflow-x: hidden;
        }
        
        /* 차트 높이 모바일 최적화 */
        .plotly-graph-div {
            height: 280px !important;
        }
        
        /* 모바일에서 차트 텍스트 크기 및 배치 조정 */
        .plotly .gtitle {
            font-size: 12px !important;
        }
        
        .plotly .xtick, .plotly .ytick {
            font-size: 8px !important;
        }
        
        .plotly .legendtext {
            font-size: 9px !important;
        }
        
        /* 모바일에서 차트 annotation 위치 조정 */
        .plotly .annotation-text {
            font-size: 8px !important;
        }
        
        /* 모바일에서 막대 위 텍스트 크기 조정 */
        .plotly .textpoint {
            font-size: 8px !important;
        }
        
        /* 개발자 정보 폰트 크기 조정 */
        .footer {
            font-size: 10px !important;
        }
        
        /* 데이터프레임 모바일 최적화 */
        .stDataFrame {
            font-size: 10px !important;
        }
        
        /* 메트릭 컨테이너 간격 조정 */
        [data-testid="metric-container"] > div {
            font-size: 11px !important;
        }
    }
    
    /* 태블릿 최적화 */
    @media (max-width: 1024px) and (min-width: 769px) {
        .capacity-data {
            font-size: 13px;
        }
        
        .facility-name {
            font-size: 15px;
        }
        
        .info-card {
            padding: 10px;
            min-height: 105px;
        }
        
        .menu-box {
            font-size: 16px;
        }
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'search_history' not in st.session_state:
    st.session_state.search_history = []



def process_address_search(sido, si, gu, dong, li="", jibun=""):
    """주소별 검색 처리"""
    search_query = f"{sido} {si} {gu} {dong}"
    if li and li != "(해당없음)":
        search_query += f" {li}"
    if jibun:
        search_query += f" {jibun}"
    
    st.session_state.search_history.append(search_query)
    
    # KEPCO 서비스를 통한 실제 용량 조회
    kepco_service = KEPCOService()
    
    # retrieve_mesh_capacity 메서드 사용으로 정확한 용량 계산
    mesh_results = kepco_service.retrieve_mesh_capacity(
        search_condition="address",
        addr_do=sido,
        addr_si=si,
        addr_gu=gu,
        addr_lidong=dong,
        addr_li=li if li != "(해당없음)" else "",
        addr_jibun=jibun
    )
    
    # 결과가 있으면 표준 형식으로 변환
    if mesh_results and len(mesh_results) > 0:
        formatted_results = []
        for item in mesh_results:
            # 수정된 API 필드 매핑을 사용한 데이터 추출
            subst_capa = int(item.get("SUBST_CAPA", 0))  # 변전소 접속기준용량
            subst_pwr = int(item.get("SUBST_PWR", 0))    # 변전소 접수기준 접속용량
            mtr_capa = int(item.get("MTR_CAPA", 0))      # 주변압기 접속기준용량
            mtr_pwr = int(item.get("MTR_PWR", 0))        # 주변압기 접수기준 접속용량
            dl_capa = int(item.get("DL_CAPA", 0))        # 배전선로 접속기준용량
            dl_pwr = int(item.get("DL_PWR", 0))          # 배전선로 접수기준 접속용량
            
            # 접수기준 접속 여유용량 (API에서 직접 제공)
            vol_1 = int(item.get("VOL_1", 0))            # 변전소 접수기준 접속 여유용량
            vol_2 = int(item.get("VOL_2", 0))            # 주변압기 접수기준 접속 여유용량  
            vol_3 = int(item.get("VOL_3", 0))            # 배전선로 접수기준 접속 여유용량
            
            # 접속계획 반영 접속용량 (실제 접속 가능 용량)
            g_subst_capa = int(item.get("G_SUBST_CAPA", 0))  # 변전소 접속계획 반영 접속용량
            g_mtr_capa = int(item.get("G_MTR_CAPA", 0))      # 주변압기 접속계획 반영 접속용량
            g_dl_capa = int(item.get("G_DL_CAPA", 0))        # 배전선로 접속계획 반영 접속용량
            
            # 최종 접속가능용량은 세 단계의 최소값 (병목 지점)
            min_available = min([v for v in [g_subst_capa, g_mtr_capa, g_dl_capa] if v >= 0])
            status = "정상" if min_available > 0 else "포화"
            
            capacity_data = {
                "변전소": item.get("SUBST_NM", ""),
                "변전소코드": item.get("SUBST_CD", ""),
                "주변압기": f"TR-{item.get('MTR_NO', '')}" if item.get('MTR_NO') else "-",
                "배전선로": item.get("DL_NM", "") or "-",
                "배전선로코드": item.get("DL_CD", ""),
                # 접속기준용량 (각 설비의 최대 설계 용량)
                "변전소접속기준용량": f"{subst_capa:,} kW",
                "주변압기접속기준용량": f"{mtr_capa:,} kW", 
                "배전선로접속기준용량": f"{dl_capa:,} kW",
                # 접수기준접속용량 (현재 실제 접속된 용량)
                "변전소접수기준접속용량": f"{subst_pwr:,} kW",
                "주변압기접수기준접속용량": f"{mtr_pwr:,} kW",
                "배전선로접수기준접속용량": f"{dl_pwr:,} kW",
                # 접수기준 접속 여유용량 (API에서 직접 계산된 값)
                "변전소여유용량": f"{vol_1:,} kW",
                "주변압기여유용량": f"{vol_2:,} kW",
                "배전선로여유용량": f"{vol_3:,} kW",
                # 접속계획 반영 접속용량 (실제 계획이 반영된 접속용량)
                "변전소접속계획반영접속용량": f"{g_subst_capa:,} kW",
                "주변압기접속계획반영접속용량": f"{g_mtr_capa:,} kW",
                "배전선로접속계획반영접속용량": f"{g_dl_capa:,} kW",
                # 최종 접속가능용량 (병목지점의 용량)
                "최종접속가능용량": min_available,
                "상태": status,
                # 원본 API 데이터 보존
                "SUBST_CAPA": subst_capa,
                "SUBST_PWR": subst_pwr,
                "MTR_CAPA": mtr_capa,
                "MTR_PWR": mtr_pwr,
                "DL_CAPA": dl_capa,
                "DL_PWR": dl_pwr,
                "VOL_1": vol_1,
                "VOL_2": vol_2,
                "VOL_3": vol_3,
                "G_SUBST_CAPA": g_subst_capa,
                "G_MTR_CAPA": g_mtr_capa,
                "G_DL_CAPA": g_dl_capa
            }
            formatted_results.append(capacity_data)
        
        st.session_state.search_results = formatted_results
        # 검색 기록에 저장 (성공한 경우)
        query_address = f"{sido} {si} {dong}"
        if li and li != "(해당없음)":
            query_address += f" {li}"
        add_to_search_history('주소기반 검색', query_address, formatted_results)
    else:
        # 검색 결과가 없는 경우 빈 결과 설정
        st.session_state.search_results = []
        # 검색 기록에 저장 (결과 없음)
        query_address = f"{sido} {si} {dong}"
        if li and li != "(해당없음)":
            query_address += f" {li}"
        add_to_search_history('주소기반 검색', query_address, [])
    
    st.rerun()

def display_detailed_analysis(facility):
    """상세 분석 및 해설 표시"""
    
    # 용량 데이터 추출 및 계산
    try:
        # 변전소 데이터
        subst_capa = facility.get('SUBST_CAPA', 0)
        subst_pwr = facility.get('SUBST_PWR', 0)
        g_subst_capa = facility.get('G_SUBST_CAPA', 0)
        
        # 주변압기 데이터
        mtr_capa = facility.get('MTR_CAPA', 0)
        mtr_pwr = facility.get('MTR_PWR', 0)
        g_mtr_capa = facility.get('G_MTR_CAPA', 0)
        
        # 배전선로 데이터
        dl_capa = facility.get('DL_CAPA', 0)
        dl_pwr = facility.get('DL_PWR', 0)
        g_dl_capa = facility.get('G_DL_CAPA', 0)
        
        # 여유용량 계산 (접속기준용량 - 접수기준접속용량)
        subst_vol1_dsc_1 = max(0, subst_capa - subst_pwr)
        subst_vol1_dsc_2 = max(0, subst_capa - g_subst_capa)
        mtr_vol2_dsc_1 = max(0, mtr_capa - mtr_pwr)
        mtr_vol2_dsc_2 = max(0, mtr_capa - g_mtr_capa)
        dl_vol3_dsc_1 = max(0, dl_capa - dl_pwr)
        dl_vol3_dsc_2 = max(0, dl_capa - g_dl_capa)
        
        # 접속 가능성 판단
        subst_available = subst_vol1_dsc_1 > 0 and subst_vol1_dsc_2 > 0
        mtr_available = mtr_vol2_dsc_1 > 0 and mtr_vol2_dsc_2 > 0
        dl_available = dl_vol3_dsc_1 > 0 and dl_vol3_dsc_2 > 0
        
    except (ValueError, TypeError):
        st.error("용량 데이터를 분석할 수 없습니다.")
        return
    
    # 분석 결과 표시
    analysis_col1, analysis_col2 = st.columns(2)
    
    with analysis_col1:
        st.markdown("### 🔍 접속 가능성 분석")
        
        # 변전소 분석
        subst_status_color = "#1479c7" if subst_available else "#ff0000"
        subst_status_text = "접속가능" if subst_available else "여유용량 없음"
        st.markdown(f"""
        <div style="padding: 10px; margin: 8px 0; border-left: 4px solid {subst_status_color}; background-color: #f8f9fa;">
            <strong style="color: {subst_status_color};">🏢 변전소: {subst_status_text}</strong><br>
            <small>접속기준용량 대비 여유용량: {subst_vol1_dsc_1:,} kW</small><br>
            <small>접속계획 반영 여유용량: {subst_vol1_dsc_2:,} kW</small>
        </div>
        """, unsafe_allow_html=True)
        
        # 주변압기 분석
        mtr_status_color = "#1479c7" if mtr_available else "#ff0000"
        mtr_status_text = "접속가능" if mtr_available else "여유용량 없음"
        st.markdown(f"""
        <div style="padding: 10px; margin: 8px 0; border-left: 4px solid {mtr_status_color}; background-color: #f8f9fa;">
            <strong style="color: {mtr_status_color};">⚡ 주변압기: {mtr_status_text}</strong><br>
            <small>접속기준용량 대비 여유용량: {mtr_vol2_dsc_1:,} kW</small><br>
            <small>접속계획 반영 여유용량: {mtr_vol2_dsc_2:,} kW</small>
        </div>
        """, unsafe_allow_html=True)
        
        # 배전선로 분석
        dl_status_color = "#1479c7" if dl_available else "#ff0000"
        dl_status_text = "접속가능" if dl_available else "여유용량 없음"
        st.markdown(f"""
        <div style="padding: 10px; margin: 8px 0; border-left: 4px solid {dl_status_color}; background-color: #f8f9fa;">
            <strong style="color: {dl_status_color};">🔌 배전선로: {dl_status_text}</strong><br>
            <small>접속기준용량 대비 여유용량: {dl_vol3_dsc_1:,} kW</small><br>
            <small>접속계획 반영 여유용량: {dl_vol3_dsc_2:,} kW</small>
        </div>
        """, unsafe_allow_html=True)
    
    with analysis_col2:
        st.markdown("### 📊 용량 상세 설명")
        
        st.markdown("""
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <h4 style="color: #1565c0; margin-top: 0;">📌 용량 용어 설명</h4>
            <ul style="margin: 10px 0;">
                <li><strong>접속기준용량:</strong> 해당 설비의 최대 설계 용량</li>
                <li><strong>접수기준접속용량:</strong> 현재 실제 접속된 발전설비 용량</li>
                <li><strong>접속계획반영접속용량:</strong> 향후 계획을 반영한 접속 예정 용량</li>
                <li><strong>여유용량:</strong> 추가 접속 가능한 용량</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <h4 style="color: #ef6c00; margin-top: 0;">⚠️ 접속 판단 기준</h4>
            <p style="margin: 5px 0; font-size: 14px;">
                • <strong style="color: #1479c7;">접속가능:</strong> 모든 설비에서 여유용량이 있는 경우<br>
                • <strong style="color: #ff0000;">여유용량 없음:</strong> 하나라도 여유용량이 부족한 경우<br>
                • <strong>최종 접속가능용량:</strong> 변전소, 주변압기, 배전선로 중 최소값
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # 종합 분석 결과
    st.markdown("### 🎯 종합 분석 결과")
    
    overall_available = subst_available and mtr_available and dl_available
    
    if overall_available:
        min_capacity = min([
            subst_vol1_dsc_2, mtr_vol2_dsc_2, dl_vol3_dsc_2
        ])
        st.success(f"""
        ✅ **신재생에너지 발전설비 접속 가능**
        
        - 모든 전력설비에서 여유용량이 확인되었습니다.
        - 최종 접속가능용량: **{min_capacity:,} kW**
        - 접속 신청 시 해당 용량 범위 내에서 승인 가능합니다.
        """)
    else:
        bottleneck_facilities = []
        if not subst_available:
            bottleneck_facilities.append("변전소")
        if not mtr_available:
            bottleneck_facilities.append("주변압기")
        if not dl_available:
            bottleneck_facilities.append("배전선로")
        
        st.error(f"""
        ❌ **신재생에너지 발전설비 접속 제한**
        
        - 다음 설비에서 여유용량 부족: **{', '.join(bottleneck_facilities)}**
        - 현재 상태로는 신규 발전설비 접속이 어렵습니다.
        - 계통 보강 또는 기존 접속용량 조정이 필요할 수 있습니다.
        """)
    
    # 지역별 특별 안내사항
    addr_do = st.session_state.get('addr_sido', '')
    subst_cd = facility.get('변전소코드', '')
    
    regional_guidance = get_regional_guidance(addr_do, subst_cd)
    if regional_guidance:
        st.markdown("### ⚠️ 지역별 특별 안내사항")
        st.markdown(f"""
        <div style="background-color: #ffebee; border: 2px solid #f44336; border-radius: 8px; padding: 15px; margin: 15px 0;">
            <p style="color: #d32f2f; font-weight: bold; font-size: 16px; margin: 0; line-height: 1.5;">
                {regional_guidance}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # 주의사항 및 안내
    st.markdown("### 📢 주의사항 및 추가 안내")
    
    st.info("""
    **📋 접속 신청 시 참고사항:**
    - 본 조회 결과는 참고용이며, 실제 접속 승인은 한국전력공사의 검토를 거쳐 결정됩니다.
    - 신재생에너지 발전설비 설치 전 반드시 한국전력공사에 사전 협의를 요청하시기 바랍니다.
    - 지역별 계통 보강 계획에 따라 접속 가능 시기가 달라질 수 있습니다.
    
    **🔗 관련 문의:**
    - 한국전력공사 신재생에너지 접속 상담: 국번없이 123
    - 온라인 접속신청: https://online.kepco.co.kr
    """)

def get_regional_guidance(addr_do, subst_cd):
    """지역별 특별 안내사항 반환"""
    
    # 특별 변전소 코드 기반 안내
    special_subst_codes = ['S621', 'D372']  # 운남, 안좌
    if subst_cd in special_subst_codes:
        return "※ 해당 변전소는 송전계통 보강이 필요하므로, 계통보강('31.12월 예정) 후 발전소 연계가능"
    
    # 지역별 안내사항
    if addr_do in ["광주광역시", "전라남도"]:
        return "※ 해당 변전소는 송전계통 보강이 필요하므로, 계통보강('31.12월 예정) 후 발전소 연계가능 ('24. 8. 31부터 적용)"
    
    elif addr_do == "전북특별자치도":
        special_jeonbuk_codes = ['2674', '2274', '2463', 'SC03', 'D510', '2742', 'E541']
        if subst_cd in special_jeonbuk_codes:
            return "※ 해당 변전소는 송전계통 보강이 필요하므로, 계통보강('31.12월 예정) 후 발전소 연계가능"
        else:
            return "※ 해당 변전소는 송전계통 보강이 필요하므로, 계통보강('31.12월 예정) 후 발전소 연계가능 ('24. 8. 31부터 적용)"
    
    elif addr_do == "제주특별자치도":
        return "※ 해당 변전소는 신규 발전소 연계시 전력수급의 균형 및 안정적 전력계통 운영에 지장을 줄 수 있어, 발전소 연계 잠정보류(추후 대책 마련 예정) [단, 1MW 이하 발전소의 경우 '24. 8. 31부터 적용]"
    
    elif addr_do == "강원특별자치도":
        gangwon_codes = ['2510', '4363', 'S401', 'S418', 'S440', 'S423', '2447', 'S408', 'S432', 'E198', 'D338', 'E404', 'E541']
        if subst_cd in gangwon_codes:
            return "※ 해당 변전소는 송전계통 보강이 필요하므로, 계통보강('26.6월 예정) 후 발전소 연계가능"
    
    elif addr_do == "경상북도":
        gyeongbuk_codes = ['2521', 'S718', 'E204', '2733', 'E318']
        if subst_cd in gyeongbuk_codes:
            return "※ 해당 변전소는 송전계통 보강이 필요하므로, 계통보강('26.12월 예정) 후 발전소 연계가능"
    
    return None

def create_capacity_chart(facility_name, facility_type, accepted_capacity, planned_capacity, standard_capacity):
    """
    용량 차트 생성 함수 - 텍스트 겹침 방지 최적화
    
    레이아웃 요소 배치 전략:
    1. 데이터 레이블: 막대 위쪽 (textposition='outside')
    2. 제목: 상단 중앙 (y=0.95)
    3. 범례: 하단 중앙 (y=-0.15) 
    4. 단위: 우측 바깥쪽 (x=1.12)
    5. Y축 범위: 데이터 레이블 공간 확보 (max_value * 1.3)
    """
    try:
        # 데이터 준비 - 수치형으로 변환 (kW 단위 제거)
        def parse_capacity(value):
            if not value or value == 'N/A':
                return 0
            if isinstance(value, str):
                # "123,456 kW" 형태에서 숫자만 추출
                value = value.replace(',', '').replace(' kW', '').strip()
            try:
                return float(value)
            except:
                return 0
        
        accepted = parse_capacity(accepted_capacity)
        planned = parse_capacity(planned_capacity)  
        standard = parse_capacity(standard_capacity)
        
        # 여유용량 계산
        remaining_accepted = max(0, standard - accepted)
        remaining_planned = max(0, standard - planned)
        
        # 상태 판단
        if remaining_accepted <= 0 or remaining_planned <= 0:
            status = "여유용량 없음"
            status_color = "#ff0000"
        else:
            status = "접속가능"
            status_color = "#1479c7"
        
        # 차트 생성
        fig = go.Figure()
        
        # 1. 막대 그래프 추가 - 데이터 레이블 개선
        fig.add_trace(go.Bar(
            name='접수기준 접속용량',
            x=[facility_name],
            y=[accepted],
            marker_color='#3366CC',  # 더 진한 파랑
            marker_line=dict(color='#2952A3', width=1),  # 테두리 추가
            text=[f'{accepted:,.0f}'],
            textposition='outside',  # 막대 위에 배치
            textfont=dict(size=10, color='#333333', family="Arial, sans-serif"),  # 폰트 크기 줄임
            width=0.35,  # 막대 폭 조정
            offset=-0.18,  # 간격 조정
            hovertemplate='<b>접수기준 접속용량</b><br>%{y:,.0f} kW<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='접속계획 반영 접속용량',
            x=[facility_name],
            y=[planned],
            marker_color='#109618',  # 더 진한 초록
            marker_line=dict(color='#0D7914', width=1),  # 테두리 추가
            text=[f'{planned:,.0f}'],
            textposition='outside',  # 막대 위에 배치
            textfont=dict(size=10, color='#333333', family="Arial, sans-serif"),  # 폰트 크기 줄임
            width=0.35,  # 막대 폭 조정
            offset=0.18,  # 간격 조정
            hovertemplate='<b>접속계획 반영 접속용량</b><br>%{y:,.0f} kW<extra></extra>'
        ))
        
        # 접속기준용량 라인 추가 - 개선된 스타일
        if standard > 0:
            fig.add_hline(
                y=standard,
                line_dash="solid",
                line_color="#FF0000",  # 더 선명한 빨강
                line_width=2.5,
                annotation_text=f"접속기준용량: {standard:,.0f} kW",
                annotation_position="top left",
                annotation=dict(
                    font=dict(size=10, color="#FF0000", family="Arial, sans-serif"),
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#FF0000",
                    borderwidth=1
                )
            )
        
        # 레이아웃 설정
        max_value = max(standard * 1.2, max(accepted, planned) * 1.1, 100)
        
        # 제목 색상: 여유용량 없음이면 빨간색, 접속가능이면 파란색  
        title_color = "#ff0000" if status == "여유용량 없음" else "#1479c7"
        
        fig.update_layout(
            # 1. 제목 개선: 크게, 진하게, 중앙정렬, 간격 넉넉히
            title=dict(
                text=f'<b style="font-size:16px;">{facility_type}: <span style="color:{title_color};">{status}</span></b>',
                x=0.5,  # 중앙 정렬
                y=0.95,  # 제목 위치 조정
                xanchor='center',
                yanchor='top',
                font=dict(size=16, color='#333333')
            ),
            xaxis_title="",
            yaxis_title="",  # Y축 제목 제거
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#e5e5e5',
                range=[0, max_value * 1.3],  # 위쪽 여백 늘림 (데이터 레이블 공간 확보)
                tickfont=dict(size=10, color='#555555'),
                showline=True,
                linecolor='#cccccc'
            ),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(size=10, color='#555555'),
                showline=True,
                linecolor='#cccccc'
            ),
            plot_bgcolor='#fafafa',
            paper_bgcolor='white',
            font=dict(size=10, family="Arial, sans-serif"),
            height=380,  # 높이 증가 (텍스트 겹침 방지)
            # 2. 마진 조정 - 각 요소를 위한 충분한 여백 확보
            margin=dict(l=50, r=120, t=80, b=50),  # 우측 마진 크게 늘림
            # 3. 범례 위치 조정 - 그래프 아래쪽으로 이동
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,  # 그래프 아래쪽에 배치
                xanchor="center", 
                x=0.5,
                font=dict(size=10, color='#555555'),
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#dddddd',
                borderwidth=1
            ),
            # 4. 단위 표시 - 그래프 영역 밖 우측 상단에 고정
            annotations=[
                dict(
                    x=1.12,  # 그래프 영역 밖 오른쪽 
                    y=0.9,   # 위쪽 위치
                    xref="paper",
                    yref="paper", 
                    text="<b>단위: kW</b>",
                    showarrow=False,
                    font=dict(size=10, color="#666666", family="Arial, sans-serif"),
                    align="center",
                    xanchor="center",
                    yanchor="middle",
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="#bbbbbb",
                    borderwidth=1,
                    borderpad=4
                )
            ],
            # 5. 바 간격 조정 
            bargap=0.4,  # 막대 그룹 간격 
            bargroupgap=0.15,  # 막대 간 간격
            # 6. 반응형 설정
            showlegend=True,
            # 7. 호버 정보 개선
            hovermode='closest'
        )
        
        # 모바일 최적화를 위한 추가 설정
        fig.update_traces(
            textangle=0,  # 텍스트 각도 고정
            textposition='outside',  # 텍스트 위치 고정
            cliponaxis=False  # 텍스트 잘림 방지
        )
        
        # 모바일 환경에서 추가 레이아웃 조정 (streamlit 환경에서는 자동 적용)
        fig.update_layout(
            # 범례와 단위 표시가 겹치지 않도록 추가 조정
            legend=dict(
                x=0.5,
                y=-0.15,  # 범례를 더 아래로
                bgcolor='rgba(255,255,255,0.95)',
                bordercolor='#dddddd',
                borderwidth=1
            ),
            # 제목과 다른 요소 간격 확보
            title=dict(
                pad=dict(t=10, b=20)  # 제목 주변 패딩
            )
        )
        
        return fig, status, remaining_accepted, remaining_planned
        
    except Exception as e:
        st.error(f"차트 생성 중 오류가 발생했습니다: {str(e)}")
        return None, "오류", 0, 0

def display_results(results):
    """검색 결과 표시"""
    # results가 리스트인지 딕셔너리인지 확인
    if isinstance(results, list):
        results_data = results
    elif isinstance(results, dict) and results.get('results'):
        results_data = results.get('results', [])
    else:
        st.warning("조회 결과가 없습니다.")
        return
    
    if not results_data:
        st.markdown("""
        <div style="background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
            <h3 style="color: #856404; margin-bottom: 15px;">🔍 검색 결과가 없습니다</h3>
            <p style="color: #856404; font-size: 16px; margin-bottom: 10px;">
                입력하신 주소에 대한 접속 용량 정보를 찾을 수 없습니다.
            </p>
            <p style="color: #856404; font-size: 16px; font-weight: bold;">
                다른 주소를 입력해 주세요.
            </p>
            <div style="margin-top: 15px; padding: 10px; background-color: #fff8e1; border-radius: 4px;">
                <p style="color: #6c5b00; font-size: 14px; margin: 0;">
                    💡 <strong>검색 팁:</strong> 시/도부터 읍/면/동까지 정확히 선택하시고, 
                    리와 상세번지는 생략하셔도 됩니다.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 요약 메트릭
    total_facilities = len(results_data)
    final_capacities = []
    
    for facility in results_data:
        final_cap = facility.get('최종접속가능용량', 0)
        if isinstance(final_cap, str):
            try:
                final_cap = int(final_cap.replace(',', '').replace(' kW', ''))
            except:
                final_cap = 0
        final_capacities.append(final_cap)
    
    total_final_capacity = min(final_capacities) if final_capacities else 0
    
    # 메트릭 카드들을 균형있게 배치
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666; margin-bottom: 8px;">접속 지점 수</div>
            <div style="font-size: 28px; font-weight: bold; color: #2c3e50;">{total_facilities}개</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666; margin-bottom: 8px;">총 가용 용량</div>
            <div style="font-size: 28px; font-weight: bold; color: #2c3e50;">{total_final_capacity:,} kW</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666; margin-bottom: 8px;">접속 상태</div>
            <div style="font-size: 28px; font-weight: bold; color: {'#28a745' if total_final_capacity > 0 else '#dc3545'};">
                {'정상' if total_final_capacity > 0 else '포화'}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 접속 상태 요약
    st.markdown("### 접속 상태 요약")
    
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        normal_count = len([r for r in results_data if r.get('상태') == '정상'])
        st.success(f"✅ 정상 접속 가능: {normal_count}개 설비")
        
    with status_col2:
        saturated_count = len([r for r in results_data if r.get('상태') == '포화'])
        if saturated_count > 0:
            st.error(f"❌ 접속 포화: {saturated_count}개 설비")
        else:
            st.info("모든 설비 접속 가능")
    
    # 상세 결과 탭
    tab1, tab2 = st.tabs(["📊 상세 용량 정보", "📋 데이터 테이블"])
    
    with tab1:
        if results_data:
            # 첫 번째 결과만 상세 표시
            facility = results_data[0]
            
            # 그래프 섹션 추가
            st.markdown("## 📊 용량 분석 차트")
            st.markdown("**변전소, 주변압기, 배전선로 용량 분석 차트**")
            
            # 범례 표시 (접속기준용량 제거)
            legend_col1, legend_col2 = st.columns(2)
            with legend_col1:
                st.markdown("🔵 **접수기준 접속용량**")  
            with legend_col2:
                st.markdown("🟢 **접속계획 반영 접속용량**")
            
            st.markdown("---")
            
            # 3개 차트를 3컬럼으로 배치
            chart_col1, chart_col2, chart_col3 = st.columns(3, gap="medium")
            
            with chart_col1:
                # 변전소 차트
                subst_chart, subst_status, _, _ = create_capacity_chart(
                    facility.get('변전소', 'N/A'),
                    "변전소",
                    facility.get('변전소접수기준접속용량', 0),
                    facility.get('변전소접속계획반영접속용량', 0),
                    facility.get('변전소접속기준용량', 0)
                )
                if subst_chart:
                    st.plotly_chart(subst_chart, use_container_width=True)
            
            with chart_col2:
                # 주변압기 차트
                mtr_chart, mtr_status, _, _ = create_capacity_chart(
                    facility.get('주변압기', 'N/A'),
                    "주변압기", 
                    facility.get('주변압기접수기준접속용량', 0),
                    facility.get('주변압기접속계획반영접속용량', 0),
                    facility.get('주변압기접속기준용량', 0)
                )
                if mtr_chart:
                    st.plotly_chart(mtr_chart, use_container_width=True)
            
            with chart_col3:
                # 배전선로 차트
                dl_chart, dl_status, _, _ = create_capacity_chart(
                    facility.get('배전선로', 'N/A'),
                    "배전선로",
                    facility.get('배전선로접수기준접속용량', 0),
                    facility.get('배전선로접속계획반영접속용량', 0),
                    facility.get('배전선로접속기준용량', 0)
                )
                if dl_chart:
                    st.plotly_chart(dl_chart, use_container_width=True)
            
            st.markdown("---")
            
            # 기존 상세 정보 카드들
            capacity_col1, capacity_col2, capacity_col3 = st.columns(3, gap="large")
            
            with capacity_col1:
                st.markdown("""
                <div class="info-card">
                    <h4 style="color: #2c3e50; text-align: center; margin-bottom: 8px; font-size: 16px;">🏢 변전소 정보</h4>
                """, unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data facility-name'>🏢 변전소명: {facility.get('변전소', 'N/A')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data capacity-value'>📊 접속기준용량: {facility.get('변전소접속기준용량', 'N/A')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data received-capacity'>📝 접수기준접속용량: {facility.get('변전소접수기준접속용량', 'N/A')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data remaining-capacity'>⚡ 여유용량: {facility.get('변전소여유용량', 'N/A')}</div>", unsafe_allow_html=True)
                status_class = 'status-normal' if facility.get('상태') == '정상' else 'status-saturated'
                st.markdown(f"<div class='capacity-data'><span class='{status_class}'>🔍 상태: {facility.get('상태', '알 수 없음')}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with capacity_col2:
                st.markdown("""
                <div class="info-card">
                    <h4 style="color: #2c3e50; text-align: center; margin-bottom: 8px; font-size: 16px;">⚡ 주변압기 정보</h4>
                """, unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data facility-name'>⚡ 주변압기번호: {facility.get('주변압기', 'N/A')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data capacity-value'>📊 접속기준용량: {facility.get('주변압기접속기준용량', 'N/A')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data received-capacity'>📝 접수기준접속용량: {facility.get('주변압기접수기준접속용량', 'N/A')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data remaining-capacity'>⚡ 여유용량: {facility.get('주변압기여유용량', 'N/A')}</div>", unsafe_allow_html=True)
                status_class = 'status-normal' if facility.get('상태') == '정상' else 'status-saturated'
                st.markdown(f"<div class='capacity-data'><span class='{status_class}'>🔍 상태: {facility.get('상태', '알 수 없음')}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with capacity_col3:
                st.markdown("""
                <div class="info-card">
                    <h4 style="color: #2c3e50; text-align: center; margin-bottom: 8px; font-size: 16px;">🔌 배전선로 정보</h4>
                """, unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data facility-name'>🔌 배전선로명: {facility.get('배전선로', 'N/A')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data capacity-value'>📊 접속기준용량: {facility.get('배전선로접속기준용량', 'N/A')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data received-capacity'>📝 접수기준접속용량: {facility.get('배전선로접수기준접속용량', 'N/A')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='capacity-data remaining-capacity'>⚡ 여유용량: {facility.get('배전선로여유용량', 'N/A')}</div>", unsafe_allow_html=True)
                status_class = 'status-normal' if facility.get('상태') == '정상' else 'status-saturated'
                st.markdown(f"<div class='capacity-data'><span class='{status_class}'>🔍 상태: {facility.get('상태', '알 수 없음')}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("표시할 용량 데이터가 없습니다.")
    
    # 상세 분석 섹션 추가
    st.markdown("---")
    st.markdown("## 📋 상세 분석 및 해설")
    
    if results_data:
        facility = results_data[0]
        display_detailed_analysis(facility)
    
    with tab2:
        # 데이터프레임으로 표시
        if results_data:
            df = pd.DataFrame(results_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("표시할 데이터가 없습니다.")

def initialize_search_history():
    """검색 히스토리 초기화"""
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    else:
        # 기존 데이터가 올바르지 않은 형식인 경우 초기화
        if st.session_state.search_history and not isinstance(st.session_state.search_history[0], dict):
            st.session_state.search_history = []

def add_to_search_history(search_type: str, query: str, results: Dict):
    """검색 결과를 히스토리에 추가"""
    from datetime import datetime
    
    history_item = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'search_type': search_type,
        'query': query,
        'results': results
    }
    
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    # 최신 검색을 맨 앞에 추가 (최대 50개 유지)
    st.session_state.search_history.insert(0, history_item)
    if len(st.session_state.search_history) > 50:
        st.session_state.search_history = st.session_state.search_history[:50]

def show_search_history_menu():
    """검색 히스토리 메뉴 (3번 메뉴)"""
    
    # 뒤로가기 버튼
    if st.button("🏠 메인 메뉴로 돌아가기"):
        st.session_state.selected_menu = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("## 📝 검색 기록")
    st.markdown("**지금까지 검색한 모든 결과를 확인할 수 있습니다.**")
    
    if 'search_history' not in st.session_state or not st.session_state.search_history:
        st.info("아직 검색 기록이 없습니다. 용량 조회를 먼저 실행해 주세요.")
        return
    
    # 히스토리 초기화 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🗑️ 모든 검색 기록 삭제", type="secondary"):
            st.session_state.search_history = []
            st.rerun()
    
    st.markdown(f"**전체 검색 기록: {len(st.session_state.search_history)}건**")
    st.markdown("---")
    
    for i, item in enumerate(st.session_state.search_history):
        # 안전하게 데이터 접근
        if isinstance(item, dict):
            search_type = item.get('search_type', '알 수 없음')
            query = item.get('query', '알 수 없음')
            timestamp = item.get('timestamp', '알 수 없음')
            results = item.get('results', {})
        else:
            # 예상치 못한 데이터 형식인 경우 건너뛰기
            continue
            
        with st.expander(f"🔍 [{i+1}] {search_type} - {query} ({timestamp})"):
            if search_type == '배전용(공용)변압기':
                # 변압기 검색 결과 표시
                transformer_data = results
                if transformer_data:
                    st.markdown(f"**📍 전산화번호:** {transformer_data.get('pole_number', 'N/A')}")
                    st.markdown(f"**🏢 소속:** {transformer_data.get('facility_info', {}).get('분전함/배전소', 'N/A')}")
                    
                    # 상간별 용량 정보 - 안전한 표시 방식
                    phases_data = transformer_data.get('phases', {})
                    if phases_data:
                        st.markdown("**📊 상간별 용량 정보:**")
                        for phase, data in phases_data.items():
                            st.markdown(f"**{phase}**")
                            st.markdown(f"- 기준용량: {data.get('기준용량', 'N/A')}")
                            st.markdown(f"- 가설누적용량: {data.get('가설누적용량', 'N/A')}")
                            st.markdown(f"- 여유용량: {data.get('여유용량', 'N/A')}")
                            st.markdown(f"- 여유율: {data.get('여유율', 'N/A')}")
                            st.markdown("")
                else:
                    st.write("검색 결과가 없습니다.")
            else:
                # 주소 기반 검색 결과
                if isinstance(results, list) and results:
                    # 컬럼 오류를 방지하기 위해 간단한 표시 방식 사용
                    st.markdown("**검색 결과:**")
                    for idx, result in enumerate(results):
                        with st.container():
                            st.markdown(f"**📍 결과 {idx+1}**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"- **변전소:** {result.get('변전소', 'N/A')}")
                                st.markdown(f"- **주변압기:** {result.get('주변압기', 'N/A')}")
                                st.markdown(f"- **배전선로:** {result.get('배전선로', 'N/A')}")
                            with col2:
                                st.markdown(f"- **변전소 여유용량:** {result.get('변전소여유용량', 'N/A')}")
                                st.markdown(f"- **주변압기 여유용량:** {result.get('주변압기여유용량', 'N/A')}")
                                st.markdown(f"- **배전선로 여유용량:** {result.get('배전선로여유용량', 'N/A')}")
                            st.markdown(f"- **상태:** {result.get('상태', 'N/A')}")
                            st.markdown("---")
                else:
                    st.write("검색 결과가 없습니다.")

def main():
    
    # 검색 히스토리 초기화
    initialize_search_history()
    
    # CSS 스타일 추가
    st.markdown("""
    <style>
    .main-title {
        font-size: 28px;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 20px;
        padding: 15px;
        background: linear-gradient(90deg, #e3f2fd 0%, #ffffff 100%);
        border-radius: 10px;
        border-left: 5px solid #1976d2;
    }
    
    .menu-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
        cursor: pointer;
        transition: transform 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .menu-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .menu-card h3 {
        color: white;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    
    .menu-card p {
        color: rgba(255,255,255,0.9);
        font-size: 16px;
        margin: 0;
    }
    
    .menu-card-1 {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    }
    
    .menu-card-2 {
        background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
    }
    
    /* 메인 메뉴 버튼 스타일링 */
    div[data-testid="column"]:nth-child(1) button[kind="secondary"] {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%) !important;
        color: white !important;
        border: none !important;
        height: 180px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3) !important;
        transition: all 0.3s ease !important;
        white-space: pre-line !important;
        text-align: center !important;
    }
    
    div[data-testid="column"]:nth-child(2) button[kind="secondary"] {
        background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%) !important;
        color: white !important;
        border: none !important;
        height: 180px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 25px rgba(78, 205, 196, 0.3) !important;
        transition: all 0.3s ease !important;
        white-space: pre-line !important;
        text-align: center !important;
    }
    
    div[data-testid="column"] button[kind="secondary"]:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.2) !important;
    }
    
    .info-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 10px 0;
    }
    
    .capacity-data {
        margin: 8px 0;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 16px;
        font-weight: bold;
        line-height: 1.4;
    }
    
    .facility-name {
        background-color: #e3f2fd;
        color: #1565c0;
    }
    
    .capacity-value {
        background-color: #e8f5e8;
        color: #2e7d32;
    }
    
    .received-capacity {
        background-color: #f3e5f5;
        color: #7b1fa2;
    }
    
    .remaining-capacity {
        background-color: #ffebee;
        color: #dc3545;
        font-weight: bold;
    }
    
    .status-normal {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    
    .status-saturated {
        background-color: #ffebee;
        color: #d32f2f;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #6c757d;
        text-align: center;
        padding: 10px 0;
        font-size: 12px;
        border-top: 1px solid #dee2e6;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 메인 타이틀
    st.markdown('<div class="main-title">⚡ 한국전력공사 신재생에너지 계통접속 용량 조회 시스템</div>', unsafe_allow_html=True)
    
    # 세션 상태에서 메뉴 선택 확인
    if 'selected_menu' not in st.session_state:
        st.session_state.selected_menu = None
    
    # 메인 메뉴 표시
    if st.session_state.selected_menu is None:
        show_main_menu()
    elif st.session_state.selected_menu == 1:
        show_transformer_capacity_menu()
    elif st.session_state.selected_menu == 2:
        show_address_based_search_menu()
    elif st.session_state.selected_menu == 3:
        show_search_history_menu()

def show_main_menu():
    """메인 메뉴 화면 표시"""
    
    st.markdown("---")
    st.markdown("## 📋 서비스 선택")
    st.markdown("원하시는 조회 서비스를 선택해 주세요.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 클릭 가능한 빨간색 메뉴 박스
        menu1_clicked = st.button(
            "🔌 배전용(공용)변압기 용량조회\n\n배전용(공용)변압기별 접속 가능 용량을\n상세히 조회할 수 있습니다.",
            key="menu1",
            use_container_width=True,
            help="전산화번호로 배전용(공용)변압기 용량 조회"
        )
        if menu1_clicked:
            st.session_state.selected_menu = 1
            st.rerun()
    
    with col2:
        # 클릭 가능한 초록색 메뉴 박스
        menu2_clicked = st.button(
            "🏢 배전선로/주변압기/변전소 용량조회\n\n주소 기반으로 해당 지역의\n전력설비 접속 용량을 조회합니다.",
            key="menu2", 
            use_container_width=True,
            help="주소 기반 전력설비 용량 조회"
        )
        if menu2_clicked:
            st.session_state.selected_menu = 2
            st.rerun()
    
    # 검색 기록 버튼 추가
    st.markdown("---")
    history_col1, history_col2, history_col3 = st.columns([1, 2, 1])
    with history_col2:
        history_count = len(st.session_state.get('search_history', []))
        history_text = f"📝 검색 기록 조회 ({history_count}건)" if history_count > 0 else "📝 검색 기록 조회"
        
        if st.button(history_text, key="menu3", use_container_width=True, type="secondary"):
            st.session_state.selected_menu = 3
            st.rerun()
    
    # 시스템 소개
    st.markdown("---")
    st.markdown("## ℹ️ 시스템 소개")
    
    intro_col1, intro_col2 = st.columns(2)
    
    with intro_col1:
        st.markdown("""
        ### 🎯 주요 기능
        - **실시간 용량 조회**: KEPCO 공식 데이터 연동
        - **상세 분석 제공**: 접속 가능성 및 여유용량 분석
        - **지역별 안내**: 계통보강 일정 및 특별 안내사항
        - **직관적 인터페이스**: 사용하기 쉬운 검색 및 결과 표시
        """)
    
    with intro_col2:
        st.markdown("""
        ### 📞 고객 지원
        - **전화 상담**: 국번없이 123
        - **온라인 신청**: https://online.kepco.co.kr
        - **운영 시간**: 평일 09:00 ~ 18:00
        - **개발팀**: SAVE ENERGY | DAVID.LEE
        """)
    
    # 개발자 정보 푸터
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 20px; color: #666; font-size: 14px;">
            <p><strong>🔧 개발자 정보</strong></p>
            <p>SAVE ENERGY | DAVID.LEE | 2025.07.30</p>
            <p><em>한국전력공사 신재생에너지 계통접속 용량 조회 시스템</em></p>
        </div>
        """,
        unsafe_allow_html=True
    )

def show_transformer_capacity_menu():
    """배전용(공용)변압기 용량조회 메뉴 (1번 메뉴)"""
    
    # 뒤로가기 버튼
    if st.button("🏠 메인 메뉴로 돌아가기"):
        st.session_state.selected_menu = None
        # 변압기 검색 관련 세션 상태 초기화
        if 'transformer_search_results' in st.session_state:
            del st.session_state.transformer_search_results
        st.rerun()
    
    st.markdown("---")
    st.markdown("## 🔌 배전용(공용)변압기 용량조회")
    st.markdown("**전산화번호로 배전용(공용)변압기의 접속 가능 용량을 조회합니다.**")
    
    # KEPCO 서비스 인스턴스 생성
    kepco_service = KEPCOService()
    
    # 전산화번호 검색 영역
    st.markdown("### 🔍 전산화번호 검색")
    
    # 검색 안내
    st.info("예시와 같이 배전용(공용)변압기 설치전신 또는 지상번기가 설치된 전주 또는 지상 배전용(공용)변압기의 전산화번호를 입력하세요.")
    
    # 전산화번호 입력 영역
    search_col1, search_col2 = st.columns([3, 1])
    
    with search_col1:
        # 입력 필드와 버튼 결합
        input_col1, input_col2 = st.columns([4, 1])
        
        with input_col1:
            pole_number = st.text_input(
                "전산화번호 입력",
                placeholder="예: 9185W431",
                key="transformer_search_input",
                help="전산화번호를 입력하세요 (8자리: 숫자4자리+영문1자리+숫자3자리)",
                max_chars=8
            )
        
        with input_col2:
            search_button = st.button("🔍 검색", key="transformer_search_btn", type="primary", use_container_width=True)
    
    # 검색 실행
    if search_button and pole_number.strip():
        # 전산화번호 형식 검증 (8자리: 숫자4자리+영문1자리+숫자3자리)
        clean_number = pole_number.strip().upper()
        
        if len(clean_number) == 8 and clean_number[:4].isdigit() and clean_number[4].isalpha() and clean_number[5:].isdigit():
            with st.spinner(f"전산화번호 {clean_number}에 대한 변압기 정보를 조회하는 중..."):
                transformer_data = kepco_service.query_by_transformer_number(clean_number)
                
                if transformer_data:
                    st.session_state.transformer_search_results = transformer_data
                    # 검색 기록에 저장
                    add_to_search_history('배전용(공용)변압기', clean_number, transformer_data)
                    st.success(f"전산화번호 {clean_number}에 대한 검색이 완료되었습니다.")
                else:
                    st.error("검색 결과를 찾을 수 없습니다. 전산화번호를 확인해 주세요.")
        else:
            st.error("올바른 전산화번호를 입력해 주세요. (형식: 9185W431 - 숫자4자리+영문1자리+숫자3자리)")
    
    # 검색 결과 표시
    if 'transformer_search_results' in st.session_state and st.session_state.transformer_search_results:
        display_transformer_results(st.session_state.transformer_search_results)

def display_transformer_results(transformer_data: Dict):
    """배전용(공용)변압기 검색 결과 표시"""
    
    st.markdown("---")
    st.markdown("## 📊 배전용(공용)변압기 조회 결과")
    
    # 기본 정보 표시
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    
    with info_col1:
        st.markdown(f"""
        <div class="capacity-data facility-name">
            <strong>본부</strong><br>
            {transformer_data.get('substation', '정보없음')}
        </div>
        """, unsafe_allow_html=True)
    
    with info_col2:
        st.markdown(f"""
        <div class="capacity-data facility-name">
            <strong>지사</strong><br>
            {transformer_data.get('branch', '정보없음')}
        </div>
        """, unsafe_allow_html=True)
    
    with info_col3:
        st.markdown(f"""
        <div class="capacity-data facility-name">
            <strong>가용/지종</strong><br>
            {transformer_data.get('available', '정보없음')}
        </div>
        """, unsafe_allow_html=True)
    
    with info_col4:
        st.markdown(f"""
        <div class="capacity-data facility-name">
            <strong>상세보기</strong><br>
            {transformer_data.get('detail', '정보없음')}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 경고 메시지
    st.markdown(f"""
    <div style="background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 15px; margin: 10px 0;">
        <h4 style="color: #856404; margin: 0 0 10px 0;">⚠️ 연계용량이 500kW 미만인 경우 저압 연계 대상입니다.</h4>
        <p style="color: #856404; margin: 0; font-size: 14px;">
            {transformer_data.get('info_message', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 배전용(공용)변압기 상세 정보
    st.markdown(f"### 🔌 배전용(공용)변압기 ({transformer_data.get('pole_number', 'N/A')})")
    
    # 상세 용량 정보 테이블
    phases_data = transformer_data.get('phases', {})
    
    if phases_data:
        # 테이블 데이터 준비
        table_data = []
        for phase_name, phase_data in phases_data.items():
            capacity = phase_data.get('기준용량', 0)
            accumulated = phase_data.get('가설누적용량', 0)
            remaining = phase_data.get('여유용량', 0)
            
            # 여유용량에 따른 색상 표시
            remaining_display = f"🔴 {remaining:,}" if remaining < 10 else f"🟢 {remaining:,}"
            
            table_data.append({
                '상구분': phase_name,
                '기준용량(kVA)': f"{capacity:,}",
                '가설누적용량(kW)': f"{accumulated:,}",
                '여유용량(kW)': remaining_display
            })
        
        # DataFrame으로 변환
        df = pd.DataFrame(table_data)
        
        # Streamlit의 dataframe을 사용하여 표시
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "상구분": st.column_config.TextColumn(
                    "상구분",
                    width="small",
                    help="변압기 상별 구분"
                ),
                "기준용량(kVA)": st.column_config.TextColumn(
                    "기준용량(kVA)",
                    width="medium",
                    help="변압기 정격 용량"
                ),
                "가설누적용량(kW)": st.column_config.TextColumn(
                    "가설누적용량(kW)",
                    width="medium",
                    help="현재까지 접속된 설비 용량"
                ),
                "여유용량(kW)": st.column_config.TextColumn(
                    "여유용량(kW)",
                    width="medium",
                    help="추가 접속 가능한 용량 (🟢충분/🔴부족)"
                )
            }
        )
    
    # 추가 안내사항
    st.markdown("---")
    st.markdown("### 📋 추가 안내사항")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown("""
        #### 🔍 용량 설명
        - **기준용량**: 배전용(공용)변압기의 정격 설치 용량
        - **가설누적용량**: 현재까지 접속된 설비 용량
        - **여유용량**: 추가 접속 가능한 용량
        """)
    
    with info_col2:
        st.markdown("""
        #### ⚠️ 주의사항
        - 여유용량이 부족한 경우 다른 배전용(공용)변압기 검토 필요
        - 500kW 미만 설비는 저압 연계 대상
        - 정확한 접속 가능 여부는 KEPCO 확인 필요
        """)
    
    # 관련 서비스 링크
    st.markdown("---")
    st.markdown("### 🔗 관련 서비스")
    
    link_col1, link_col2 = st.columns(2)
    
    with link_col1:
        if st.button("📋 설비 용량조회 (변전소/주변압기/배전선로)", key="goto_facility_search", use_container_width=True):
            st.session_state.selected_menu = 2
            st.rerun()
    
    with link_col2:
        st.markdown("""
        **📞 고객 상담**  
        국번없이 **123**  
        평일 09:00 ~ 18:00
        """)

def show_address_based_search_menu():
    """배전선로/주변압기/변전소 용량조회 메뉴 (2번 메뉴) - 기존 앱 기능"""
    
    # 뒤로가기 버튼
    if st.button("🏠 메인 메뉴로 돌아가기"):
        st.session_state.selected_menu = None
        # 검색 관련 세션 상태 초기화
        if 'search_results' in st.session_state:
            del st.session_state.search_results
        st.rerun()
    
    st.markdown("---")
    st.markdown("## 🏢 배전선로/주변압기/변전소 용량조회")
    st.markdown("**주소 기반 검색을 통해 해당 지역의 전력설비 접속 용량을 조회합니다.**")
    
    # KEPCO 서비스 인스턴스 생성
    kepco_service = KEPCOService()
    
    # 시/도 선택
    if 'sido_list' not in st.session_state:
        with st.spinner("시/도 정보를 불러오는 중..."):
            sido_data = kepco_service.get_address_data(-1)
            if sido_data:
                st.session_state.sido_list = [item.get('ADDR_DO', '') for item in sido_data]
            else:
                st.session_state.sido_list = [
                    "강원특별자치도", "경기도", "경상남도", "경상북도", "광주광역시",
                    "대구광역시", "대전광역시", "부산광역시", "서울특별시", "세종특별자치시",
                    "울산광역시", "인천광역시", "전라남도", "전북특별자치도", "제주특별자치도",
                    "충청남도", "충청북도"
                ]
        
    # 첫 번째 행: 시/도, 시/군, 구/군
    addr_col1, addr_col2, addr_col3 = st.columns(3)
    
    with addr_col1:
        selected_sido = st.selectbox("시/도", st.session_state.sido_list, 
                                   index=st.session_state.sido_list.index("전북특별자치도") if "전북특별자치도" in st.session_state.sido_list else 0,
                                   key="addr_sido")
    
    with addr_col2:
        # 시/군 선택
        si_key = f"si_list_{selected_sido}"
        if si_key not in st.session_state or st.session_state.get('current_sido') != selected_sido:
            with st.spinner("시/군 정보를 불러오는 중..."):
                si_data = kepco_service.get_address_data(0, addr_do=selected_sido)
                if si_data:
                    st.session_state[si_key] = [item.get('ADDR_SI', '') for item in si_data]
                else:
                    st.session_state[si_key] = ["정보를 불러올 수 없습니다"]
                st.session_state.current_sido = selected_sido
        
        selected_si = st.selectbox("시/군", st.session_state.get(si_key, []), key="addr_si")
    
    with addr_col3:
        # 구/군 선택
        gun_key = f"gun_list_{selected_sido}_{selected_si}"
        if gun_key not in st.session_state or st.session_state.get('current_si') != selected_si:
            with st.spinner("구/군 정보를 불러오는 중..."):
                gun_data = kepco_service.get_address_data(1, addr_do=selected_sido, addr_si=selected_si)
                if gun_data:
                    st.session_state[gun_key] = [item.get('ADDR_GU', '') for item in gun_data]
                else:
                    st.session_state[gun_key] = ["정보를 불러올 수 없습니다"]
                st.session_state.current_si = selected_si
        
        selected_gun = st.selectbox("구/군", st.session_state.get(gun_key, []), key="addr_gun")
    
    # 두 번째 행: 읍/면/동, 리, 상세번지
    addr_col4, addr_col5, addr_col6 = st.columns(3)
    
    with addr_col4:
        # 읍/면/동 선택
        dong_key = f"dong_list_{selected_sido}_{selected_si}_{selected_gun}"
        if dong_key not in st.session_state or st.session_state.get('current_gun') != selected_gun:
            with st.spinner("읍/면/동 정보를 불러오는 중..."):
                dong_data = kepco_service.get_address_data(2, addr_do=selected_sido, addr_si=selected_si, addr_gu=selected_gun)
                if dong_data:
                    st.session_state[dong_key] = [item.get('ADDR_LIDONG', '') for item in dong_data]
                else:
                    st.session_state[dong_key] = ["정보를 불러올 수 없습니다"]
                st.session_state.current_gun = selected_gun
        
        selected_dong = st.selectbox("읍/면/동", st.session_state.get(dong_key, []), key="addr_dong")
    
    with addr_col5:
        # 리 선택 (선택사항)
        li_key = f"li_list_{selected_sido}_{selected_si}_{selected_gun}_{selected_dong}"
        if li_key not in st.session_state or st.session_state.get('current_dong') != selected_dong:
            if selected_dong and selected_dong not in ["정보를 불러올 수 없습니다"]:
                with st.spinner("리 정보를 확인하는 중..."):
                    li_data = kepco_service.get_address_data(3, addr_do=selected_sido, addr_si=selected_si, addr_gu=selected_gun, addr_lidong=selected_dong)
                    if li_data:
                        li_options = [item.get('ADDR_LI', '') for item in li_data if item.get('ADDR_LI')]
                        if li_options:
                            st.session_state[li_key] = li_options
                        else:
                            st.session_state[li_key] = ["(해당없음)"]
                    else:
                        st.session_state[li_key] = ["(해당없음)"]
                    st.session_state.current_dong = selected_dong
            else:
                st.session_state[li_key] = ["(해당없음)"]
        
        selected_li = st.selectbox("리 (선택)", st.session_state.get(li_key, ["(해당없음)"]), key="addr_li")
    
    with addr_col6:
        # 상세번지 선택 - 동적 로드
        jibun_key = f"jibun_list_{selected_sido}_{selected_si}_{selected_gun}_{selected_dong}"
        if jibun_key not in st.session_state or st.session_state.get('current_dong') != selected_dong:
            if selected_dong and selected_dong not in ["정보를 불러올 수 없습니다"]:
                with st.spinner("상세번지 정보를 불러오는 중..."):
                    jibun_data = kepco_service.get_address_data(4, addr_do=selected_sido, addr_si=selected_si, addr_gu=selected_gun, addr_lidong=selected_dong)
                    if jibun_data:
                        jibun_options = [item.get('ADDR_JIBUN', '') for item in jibun_data if item.get('ADDR_JIBUN')]
                        if jibun_options:
                            st.session_state[jibun_key] = jibun_options
                        else:
                            st.session_state[jibun_key] = ["553-5"]  # 기본값
                    else:
                        st.session_state[jibun_key] = ["553-5"]  # 기본값
            else:
                st.session_state[jibun_key] = ["553-5"]  # 기본값
        
        jibun_options = st.session_state.get(jibun_key, ["553-5"])
        selected_jibun = st.selectbox("상세번지 (선택)", jibun_options, key="addr_jibun")
    
    # 검색 버튼
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 주소 검색", type="primary", use_container_width=True):
        process_address_search(selected_sido, selected_si, selected_gun, selected_dong, selected_li, selected_jibun)
    
    # 사이드바는 간단한 정보만 표시
    with st.sidebar:
        st.header("📋 검색 히스토리")
        
        if st.session_state.search_history:
            for i, search in enumerate(st.session_state.search_history[-5:]):  # 최근 5개만 표시
                st.text(f"{i+1}. {search}")
        else:
            st.info("검색 기록이 없습니다.")
        
        st.markdown("---")
        st.markdown("### 💡 사용 가이드")
        st.markdown("""
        **주소별 조회:**
        - 시/도 → 시/군 → 구/군 → 읍/면/동 순으로 선택
        - 리와 상세번지는 선택사항입니다
        
        **결과 해석:**
        - 정상: 접속 가능
        - 포화: 접속 불가능
        - 최종접속가능용량: 변전소/주변압기/배전선로 중 최소값
        """)
        
        if st.button("🗑️ 히스토리 초기화"):
            st.session_state.search_history = []
            st.rerun()
    
    # 결과 표시 영역
    if 'search_results' in st.session_state:
        if st.session_state.search_results:
            st.markdown("---")
            st.markdown("## 📊 조회 결과")
            display_results(st.session_state.search_results)
        elif st.session_state.search_results == []:  # 빈 리스트인 경우 (검색 했지만 결과 없음)
            st.markdown("---")
            st.markdown("## 📊 조회 결과")
            st.markdown("""
            <div style="background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                <h3 style="color: #856404; margin-bottom: 15px;">🔍 검색 결과가 없습니다</h3>
                <p style="color: #856404; font-size: 16px; margin-bottom: 10px;">
                    입력하신 주소에 대한 접속 용량 정보를 찾을 수 없습니다.
                </p>
                <p style="color: #856404; font-size: 16px; font-weight: bold;">
                    다른 주소를 입력해 주세요.
                </p>
                <div style="margin-top: 15px; padding: 10px; background-color: #fff8e1; border-radius: 4px;">
                    <p style="color: #6c5b00; font-size: 14px; margin: 0;">
                        💡 <strong>검색 팁:</strong> 시/도부터 읍/면/동까지 정확히 선택하시고, 
                        리와 상세번지는 생략하셔도 됩니다.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()