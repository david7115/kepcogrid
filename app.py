import streamlit as st
import requests
import pandas as pd
import io
import re

st.set_page_config(page_title="한전 분산전원 연계 접수진행현황 조회", layout="wide")

# --- 좌상단 검정색 버전 정보 ---
st.markdown("""
    <style>
        .version-left {
            position: fixed;
            left: 24px; top: 18px;
            color: #222 !important;
            font-size: .97em;
            font-family: 'Segoe UI', sans-serif;
            z-index:99;
            letter-spacing:0.1em;
            opacity: 0.95;
        }
        .main-center {text-align:center !important;}
        .result-card {
            background: #f5f7fb; border-radius: 1.2rem;
            padding: 1.2rem 2rem 1.0rem 2rem;
            box-shadow: 0 2px 12px rgba(10,40,130,.10);
            margin-bottom: 2rem;
        }
        .mycard {
            background: #e7f9ed; border-radius: 1.2rem;
            padding: 1.3rem 2rem 1rem 2rem;
            box-shadow: 0 2px 16px rgba(10,130,40,.11);
            margin-bottom: 2.1rem;
            font-size:1.12em;
        }
        .recent-history {
            background: #fffce6; border-radius: 0.7rem;
            padding: 0.7rem 1rem; margin-bottom: 1rem;
            border-left: 6px solid #ffcd38;
            font-size: 1.08em;
        }
    </style>
    <div class="version-left">프로그램 제작 SAVE ENERGY VER 1.0</div>
""", unsafe_allow_html=True)

# --- 중앙 타이틀 ---
st.markdown('<h1 class="main-center">🔌 한전 분산전원 연계 접수진행현황 조회</h1>', unsafe_allow_html=True)

# --- 입력란/버튼 중앙정렬 ---
col_blank1, col_main, col_blank2 = st.columns([2,5,2])
with col_main:
    st.markdown("#### <span style='color:#193a5a;'>📥 접수번호를 입력하세요</span>", unsafe_allow_html=True)
    number_input = st.text_input("", placeholder="예: 4830-20231115-010412 또는 483020180226000077")
    search_button = st.button("🔍 조회하기", use_container_width=True)

API_URL = "https://online.kepco.co.kr/ew/status/pwtr/search"

if "search_history" not in st.session_state:
    st.session_state["search_history"] = []

def extract_resultlist(data):
    resultlist = []
    for key in ['dlt_stepA', 'dlt_stepB', 'dlt_stepC']:
        if key in data and isinstance(data[key], list):
            resultlist.extend(data[key])
    if not resultlist:
        resultlist = (
            data.get("resultList")
            or data.get("list")
            or data.get("data", {}).get("list")
            or data.get("result", {}).get("data", {}).get("list")
            or []
        )
    return resultlist

def save_search_history(number, juris_code):
    entry = {
        "접수번호": number,
        "지사코드": juris_code
    }
    if entry not in st.session_state["search_history"]:
        st.session_state["search_history"].insert(0, entry)
        st.session_state["search_history"] = st.session_state["search_history"][:10]

def is_acptno_format(num):
    num_only = re.sub(r'\D', '', num)
    dash_type = bool(re.match(r'^\d{4}-\d{8}-\d{6,}$', num))
    return (15 <= len(num_only) <= 20) or dash_type

# --- 최근검색조건도 중앙정렬 ---
with col_main:
    with st.expander("📁 최근 검색조건", expanded=True):
        if st.session_state["search_history"]:
            for entry in st.session_state["search_history"]:
                st.markdown(
                    f'<div class="recent-history">'
                    f'접수번호: <b style="color:#1a36b3;">{entry["접수번호"]}</b> '
                    f'| 지사코드: <b style="color:#125a21;">{entry["지사코드"]}</b>'
                    f'</div>',
                    unsafe_allow_html=True
