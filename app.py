import re
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# ----- 날짜 포맷 변환 -----
def normalize_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
    except:
        return date_str

# ----- API 호출 -----
def fetch_kepco_data(acpt_no: str):
    # 숫자만 추출하여 접수번호 변환
    acpt_no_cleaned = re.sub(r"[^0-9]", "", acpt_no)
    
    url = "https://online.kepco.co.kr/ew/status/pwtr/search"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json",
    }
    payload = {
        "dma_param": {
            "jurisOfficecd": "4830",  # 업무지사코드: 예시로 고정
            "acptNo": acpt_no_cleaned
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        return None, f"요청 실패: 상태코드 {response.status_code}"

    try:
        json_data = response.json()
        data_rows = json_data.get("result", {}).get("data", {}).get("list", [])
        if not data_rows:
            return None, "조회된 데이터가 없습니다."

        for row in data_rows:
            row["접수일자"] = normalize_date(row.get("rcptYmd", ""))
            row["예정일자"] = normalize_date(row.get("schdYmd", ""))
            row["접수번호"] = row.get("acptNo", "")
            row["사업명"] = row.get("pjNm", "")
            row["상태"] = row.get("prgrsSttcNm", "")
            row["관할지사"] = row.get("jurisOfficeNm", "")
            row["담당부서"] = row.get("mntrnDeptNm", "")

        df = pd.DataFrame(data_rows)
        return df[["접수번호", "사업명", "접수일자", "예정일자", "상태", "관할지사", "담당부서"]], None
    except Exception as e:
        return None, f"응답 파싱 실패: {e}"

# ----- Streamlit UI -----
st.set_page_config(page_title="KEPCO 전력 접수현황", layout="centered")
st.title("🔌 KEPCO 접수현황 조회")
st.caption("고객번호 또는 접수번호 입력 후 접수, 공용망보강, 접속공사 현황을 조회합니다.")

col1, col2 = st.columns([3, 2])
with col1:
    acpt_no = st.text_input("고객번호 또는 접수번호", placeholder="예: 12-2945-7459 / 4830-20231115-010412")

with col2:
    step_type = st.selectbox("조회 유형", ["접수", "공용망보강", "접속공사"])

if st.button("조회하기"):
    if not acpt_no.strip():
        st.warning("고객번호 또는 접수번호를 입력하세요.")
    else:
        with st.spinner("KEPCO 시스템에서 조회 중..."):
            df_result, err_msg = fetch_kepco_data(acpt_no)
            if df_result is not None:
                st.success("✅ 조회 완료")
                st.dataframe(df_result, use_container_width=True)
            else:
                st.error(f"⚠️ {err_msg}")
