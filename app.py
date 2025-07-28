import streamlit as st
import requests
import json

st.set_page_config(page_title="KEPCO 접속현황 조회기", layout="centered")
st.title("🔌 KEPCO 접속현황 조회기")
st.markdown("지사코드, 고객번호 또는 접수번호, 조회 유형을 모두 정확히 입력해야 결과가 나옵니다.")

# 입력 UI
officecd = st.text_input("지사코드 (jurisOfficecd, 예: 4830)", value="4830")
number_input = st.text_input("고객번호 또는 접수번호", placeholder="예: 12-2945-7459 또는 4830-20231115-010412")
query_type = st.selectbox("조회 유형", ["접수", "공용망보강", "접속공사"])
search_button = st.button("🔍 조회하기")

API_URL = "https://online.kepco.co.kr/ew/status/pwtr/search"

if search_button and officecd and number_input.strip():
    acpt_no = number_input.strip()
    payload = {"dma_param": {"jurisOfficecd": officecd, "acptNo": acpt_no}}
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json",
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        text = response.text.strip()

        if response.status_code == 200 and text:
            try:
                result = response.json()
                resultlist = (
                    result.get("resultList")
                    or result.get("list")
                    or result.get("data", {}).get("list")
                    or result.get("result", {}).get("data", {}).get("list")
                    or []
                )
                if resultlist:
                    st.success("✅ 조회 성공")
                    st.dataframe(resultlist, use_container_width=True)
                else:
                    st.warning("📭 조회 결과가 없습니다. 입력값/지사코드/유형을 다시 확인하세요.")
            except json.JSONDecodeError:
                st.error("❌ 응답이 JSON 형식이 아닙니다.")
                st.code(text[:500], language="html")
        else:
            st.warning("⚠️ 유효한 응답이 없습니다. 입력값/지사코드/유형을 다시 확인하세요.")
    except Exception as e:
        st.error(f"🚨 조회 중 오류 발생: {e}")

elif search_button:
    st.warning("지사코드와 고객번호/접수번호를 모두 입력하세요.")
