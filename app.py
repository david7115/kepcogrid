import streamlit as st
import pandas as pd
import requests

def fetch_kepco_data(step: str, search_type: str = None, keyword: str = None):
    url = "https://online.kepco.co.kr/ew/status/pwtr/search"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "searchType": step
    }
    if search_type == "고객번호" and keyword:
        payload["고객번호"] = keyword.replace("-", "").strip()
    elif search_type == "접수번호" and keyword:
        payload["접수번호"] = keyword.replace("-", "").strip()

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        rows = data.get("rows") or data.get("list") or []
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ 데이터 요청 실패: {e}")
        return pd.DataFrame()

# --- Streamlit 앱 UI ---
st.set_page_config(layout="wide", page_title="KEPCO 분산형전원 접속현황 조회")

st.title("🔌 KEPCO 분산형전원 접속현황 조회기")
st.caption("📡 접수유형별 고객번호/접수번호 검색 | Streamlit Cloud 배포용")

# 안전한 위젯 배치
step = st.selectbox("📁 접수유형", ["접수", "공용망보강", "접속공사"], key="step_select")
search_type = st.radio("🔍 조회기준", ["고객번호", "접수번호"], horizontal=True, key="search_type_radio")
raw_keyword = st.text_input("번호 입력 (하이픈 '-' 포함 가능)", placeholder="예: 12-2945-7459", key="input_keyword")

# 조회 실행
if st.button("📥 조회 실행"):
    keyword = raw_keyword.replace("-", "").strip()
    if not keyword:
        st.warning("❗ 번호를 입력해주세요.")
    else:
        with st.spinner("⏳ 데이터를 조회 중입니다..."):
            df = fetch_kepco_data(step=step, search_type=search_type, keyword=keyword)
            if not df.empty:
                st.success(f"✅ 총 {len(df)}건 조회됨")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("📄 CSV 다운로드", csv, file_name=f"kepco_{step}.csv")
            else:
                st.warning("📭 조회 결과가 없습니다.")
