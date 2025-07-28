import streamlit as st
import requests
import json
import re

# 페이지 설정
st.set_page_config(page_title="KEPCO 접속현황 조회기", page_icon="🔌", layout="centered")
st.title("🔌 KEPCO 접속현황 조회기")
st.markdown("고객번호 또는 접수번호 입력 후 접수, 공용망보강, 접속공사 현황을 조회합니다.")

# 입력 UI
number_input = st.text_input("고객번호 또는 접수번호", placeholder="예: 12-2945-7459 또는 4830-20231115-010412")
query_type = st.selectbox("조회 유형", ["접수", "공용망보강", "접속공사"])
search_button = st.button("🔍 조회하기")

# 숫자만 추출 함수
def normalize_number(text):
    return re.sub(r"[^0-9]", "", text)

# API URL (모든 유형 동일)
API_URL = "https://online.kepco.co.kr/ew/status/pwtr/search"

# 조회 수행
if search_button and number_input:
    clean_number = normalize_number(number_input)

    if len(clean_number) < 10:
        st.error("⚠️ 고객번호 또는 접수번호 형식이 잘못되었습니다.")
    else:
        # 고객번호, 접수번호 구분: 10자리 이하면 고객번호
        jurisOfficecd = clean_number[:4]
        acptNo = clean_number

        payload = {"dma_param": {"jurisOfficecd": jurisOfficecd, "acptNo": acptNo}}
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json",
        }

        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)

            if response.status_code == 200 and response.text.strip():
                try:
                    result = response.json()
                    if result.get("resultList"):
                        st.success("✅ 조회 성공")
                        st.dataframe(result["resultList"])
                    else:
                        st.warning("⚠️ 조회 결과가 없습니다.")
                except json.JSONDecodeError:
                    st.error("⚠️ 응답 파싱 실패: JSON 형식이 아님")
                    st.code(response.text[:500], language="html")
            else:
                st.warning("⚠️ 유효한 응답이 없습니다.")
        except Exception as e:
            st.error(f"❌ 요청 실패: {e}")
