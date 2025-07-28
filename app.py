import streamlit as st
import requests
import pandas as pd
import io
import re

st.set_page_config(page_title="KEPCO 접속현황 조회기 (Excel+고객↔지사 매핑)", layout="centered")
st.title("🔌 KEPCO 접속현황 조회기 (Excel+고객↔지사 매핑)")

number_input = st.text_input("고객번호 또는 접수번호", placeholder="예: 4830-20231115-010412 또는 12-2945-7459")
search_type = st.selectbox("검색유형", ["접수번호", "고객번호"])
search_button = st.button("🔍 조회하기")

API_URL = "https://online.kepco.co.kr/ew/status/pwtr/search"

if "search_history" not in st.session_state:
    st.session_state["search_history"] = []
if "customer_to_officecd" not in st.session_state:
    st.session_state["customer_to_officecd"] = {}

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

def save_search_history(number, search_type, juris_code):
    entry = {
        "고객/접수번호": number,
        "검색유형": search_type,
        "지사코드": juris_code
    }
    if entry not in st.session_state["search_history"]:
        st.session_state["search_history"].insert(0, entry)
        st.session_state["search_history"] = st.session_state["search_history"][:10]

def is_acptno_format(num):
    # 접수번호: 15자리 이상 or 하이픈 구분 3개 (4-8-6 등)
    num_only = re.sub(r'\D', '', num)
    return len(num_only) >= 15 or (num.count('-') >= 2 and len(num) > 12)

def is_custno_format(num):
    # 고객번호: 10~12자리 or 하이픈 구분 2개
    num_only = re.sub(r'\D', '', num)
    return (10 <= len(num_only) <= 12) or (num.count('-') == 2 and len(num_only) <= 12)

def build_payload(search_type, value):
    value_clean = value.replace("-", "").strip()
    if search_type == "접수번호" and is_acptno_format(value):
        juris_code = value_clean[:4]
        return juris_code, {"dma_param": {"jurisOfficecd": juris_code, "acptNo": value_clean}}
    elif search_type == "고객번호" and is_custno_format(value):
        customer_no = value_clean
        mapped = st.session_state["customer_to_officecd"].get(customer_no)
        juris_code = mapped if mapped else customer_no[:2]
        return juris_code, {"dma_param": {"jurisOfficecd": juris_code, "custNo": customer_no}}
    else:
        return None, None

# 상단 최근 검색조건 표시
st.subheader("📁 최근 검색조건")
if st.session_state["search_history"]:
    for entry in st.session_state["search_history"]:
        st.markdown(f"- **{entry['검색유형']}** | 번호: `{entry['고객/접수번호']}` | 지사코드: `{entry['지사코드']}`")
else:
    st.markdown("_(아직 저장된 검색 기록이 없습니다.)_")

if search_button:
    if not number_input.strip():
        st.warning("고객번호 또는 접수번호를 입력하세요.")
    else:
        juris_code, payload = build_payload(search_type, number_input)
        # [1] 형식 오류 시 안내
        if juris_code is None or payload is None:
            st.error("입력값 형식이 올바르지 않습니다. 접수번호(15~20자/하이픈3개) 또는 고객번호(10~12자/하이픈2개)를 정확히 입력하세요.")
        else:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": "Mozilla/5.0"
            }
            with st.spinner("서버 조회 중... (최대 30초)"):
                try:
                    resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                    text = resp.text.strip()
                    st.info(f"**검색조건:** [{search_type}] `{number_input}` | **지사코드:** `{juris_code}`")
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
                                save_search_history(number_input, search_type, juris_code)
                                # 접수번호 검색이면 고객번호-지사코드 매핑
                                if search_type == "접수번호":
                                    if "CUSTNO" in df.columns and "JURIS_OFFICECD" in df.columns:
                                        for row in df.itertuples():
                                            cust_no = str(getattr(row, "CUSTNO"))
                                            office_cd = str(getattr(row, "JURIS_OFFICECD"))
                                            st.session_state["customer_to_officecd"][cust_no] = office_cd
                            else:
                                st.warning("📭 결과가 없습니다. 입력값, 지사코드, 유형을 확인하세요.")
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
    st.warning("고객번호 또는 접수번호를 입력하세요.")

