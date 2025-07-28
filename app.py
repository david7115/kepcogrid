import streamlit as st
import requests
import pandas as pd
import io
import re

st.set_page_config(page_title="한전 분산전원 연계 접수진행현황 조회", layout="centered")
st.title("🔌 한전 분산전원 연계 접수진행현황 조회")

number_input = st.text_input(
    "접수번호를 입력하세요",
    placeholder="예: 4830-20231115-010412 또는 483020180226000077"
)
search_button = st.button("🔍 조회하기")

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
    # 15~20자리 숫자 or xxxx-yyyyyyyy-zzzzzz
    num_only = re.sub(r'\D', '', num)
    dash_type = bool(re.match(r'^\d{4}-\d{8}-\d{6,}$', num))
    return (15 <= len(num_only) <= 20) or dash_type

st.subheader("📁 최근 검색조건")
if st.session_state["search_history"]:
    for entry in st.session_state["search_history"]:
        st.markdown(f"- 접수번호: `{entry['접수번호']}` | 지사코드: `{entry['지사코드']}`")
else:
    st.markdown("_(아직 저장된 검색 기록이 없습니다.)_")

if search_button:
    if not number_input.strip():
        st.warning("접수번호를 입력하세요.")
    elif not is_acptno_format(number_input):
        st.error("접수번호 형식이 올바르지 않습니다.\n- 15~20자리 숫자 또는 xxxx-yyyyyyyy-zzzzzz 형식이어야 합니다.")
    else:
        value_clean = number_input.replace("-", "").strip()
        juris_code = value_clean[:4]
        payload = {"dma_param": {"jurisOfficecd": juris_code, "acptNo": value_clean}}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "Mozilla/5.0"
        }
        with st.spinner("서버 조회 중... (최대 30초)"):
            try:
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                text = resp.text.strip()
                st.info(f"**검색조건:** 접수번호 `{number_input}` | **지사코드:** `{juris_code}`")
                if resp.status_code == 200 and text:
                    try:
                        data = resp.json()
                        resultlist = extract_resultlist(data)
                        if resultlist:
                            df = pd.DataFrame(resultlist)
                            df.insert(0, "일련번호", range(1, len(df) + 1))
                            st.success(f"{len(df)}건 조회 성공")
                            st.dataframe(df, use_container_width=True)
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                                df.to_excel(writer, index=False, sheet_name="KEPCO")
                            st.download_button(
                                label="Excel 다운로드 (.xlsx)",
                                data=output.getvalue(),
                                file_name="kepco_result.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            save_search_history(number_input, juris_code)
                        else:
                            st.warning("📭 결과가 없습니다. 입력값/지사코드 확인.")
                    except Exception as e:
                        st.error(f"❌ 응답 파싱 오류: {e}")
                        st.code(text[:500], language="html")
                else:
                    st.warning("⚠️ 유효한 응답이 없습니다. 입력값/지사코드를 확인하세요.")
            except requests.exceptions.Timeout:
                st.error("❌ 서버 응답 타임아웃 (30초 초과). 서버 상황에 따라 재시도 필요.")
            except Exception as e:
                st.error(f"🚨 조회 오류: {e}")

elif search_button:
    st.warning("접수번호를 입력하세요.")
