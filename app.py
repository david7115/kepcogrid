import streamlit as st
import requests
import json
import re

# ---- 페이지 설정 ----
st.set_page_config(page_title="KEPCO 접속현황 조회기", page_icon="🔌", layout="centered")
st.title("🔌 KEPCO 접속현황 조회기")
st.markdown("고객번호 또는 접수번호 입력 후 접수, 공용망보강, 접속공사 현황을 조회합니다.")

# ---- 입력 UI ----
number_input = st.text_input("고객번호 또는 접수번호", placeholder="예: 12-2945-7459 또는 4830-20231115-010412")
query_type = st.selectbox("조회 유형", ["접수", "공용망보강", "접속공사"])
search_button = st.button("🔍 조회하기")

# ---- API URL ----
API_URL = "https://online.kepco.co.kr/ew/status/pwtr/search"

def guess_office_code(acpt_no):
    # 접수번호 형식: 4830-20231115-010412 또는 483020231115010412 등
    nums = re.sub(r"[^0-9]", "", acpt_no)
    if len(nums) >= 4:
        return nums[:4]
    return "4830"  # 기본값

if search_button and number_input.strip():
    acpt_no = number_input.strip()
    jurisOfficecd = guess_office_code(acpt_no)

    payload = {"dma_param": {"jurisOfficecd": jurisOfficecd, "acptNo": acpt_no}}
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json",
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        text = response.text.strip()
        # 디버그: 상태코드와 본문 일부 보여주기 (개발시만 표시, 운영시 삭제)
        # st.write(f"응답코드: {response.status_code}")
        # st.code(text[:300])

        if response.status_code == 200 and text:
            try:
                result = response.json()
                # 다양한 구조 지원
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
                    st.download_button("CSV 다운로드", data=json.dumps(resultlist, ensure_ascii=False, indent=2), file_name="kepco_result.json")
                else:
                    st.warning("📭 조회 결과가 없습니다. 입력값과 유형을 다시 확인하세요.")
            except json.JSONDecodeError:
                st.error("❌ 응답이 JSON 형식이 아닙니다.")
                st.code(text[:500], language="html")
        else:
            st.warning("⚠️ 유효한 응답이 없습니다. 입력값과 유형을 다시 확인하세요.")
    except Exception as e:
        st.error(f"🚨 조회 중 오류 발생: {e}")

elif search_button and not number_input.strip():
    st.warning("고객번호 또는 접수번호를 입력하세요.")

