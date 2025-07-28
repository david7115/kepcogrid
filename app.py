import streamlit as st
import requests
import pandas as pd
import io

st.set_page_config(page_title="KEPCO 접속현황 조회기", layout="centered")
st.title("🔌 KEPCO 접속현황 조회기 (Excel+고객↔지사 매핑)")

number_input = st.text_input("고객번호 또는 접수번호", placeholder="예: 4830-20231115-010412 또는 12-2945-7459")
search_type = st.selectbox("검색유형", ["접수번호", "고객번호"])
search_button = st.button("🔍 조회하기")

API_URL = "https://online.kepco.co.kr/ew/status/pwtr/search"

# --- 세션상태에 최근검색조건, 고객번호↔지사코드 매핑 저장 ---
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

# --- 상단 최근 검색조건 표시 ---
st.subheader("🗂️ 최근 검색조건")
if st.session_state["search_history"]:
    for entry in st.session_state["search_history"]:
        st.markdown(f"- **{entry['검색유형']}** | 번호: `{entry['고객/접수번호']}` | 지사코드: `{entry['지사코드']}`")
else:
    st.markdown("_(아직 저장된 검색 기록이 없습니다.)_")

# --- 페이로드 자동생성 함수 ---
def build_payload(search_type, value):
    value_clean = value.replace("-", "").strip()
    if search_type == "접수번호":
        juris_code = value_clean[:4]
        return juris_code, {"dma_param": {"jurisOfficecd": juris_code, "acptNo": value_clean}}
    elif search_type == "고객번호":
        # 매핑 테이블 우선 조회
        customer_no = value_clean
        mapped = st.session_state["customer_to_officecd"].get(customer_no)
        juris_code = mapped if mapped else customer_no[:2]
        return juris_code, {"dma_param": {"jurisOfficecd": juris_code, "custNo": customer_no}}
    else:
        return None, None

# --- 메인 조회로직 ---
if search_button:
    if not number_input.strip():
        st.warning("고객번호 또는 접수번호를 입력하세요.")
    else:
        juris_code, payload = build_payload(search_type, number_input)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "Mozilla/5.0"
        }
        with st.spinner("서버 조회 중... (최대 30초)"):
            try:
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                text = resp.text.strip()
                if resp.status_code == 200 and text:
                    try:
                        data = resp.json()
                        resultlist = extract_resultlist(data)
                        # ---- 상단에 '이번 검색조건' 표시 ----
                        st.info(f"**검색조건:** [{search_type}] `{number_input}` | **지사코드:** `{juris_code}`")
                        if resultlist:
                            df = pd.DataFrame(resultlist)
                            # --- 일련번호(순번) 컬럼 추가 ---
                            df.insert(0, "일련번호", range(1, len(df) + 1))
                            st.success(f"{len(df)}건 조회 성공")
                            st.dataframe(df, use_container_width=True)
                            # --- 엑셀 다운로드 ---
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                                df.to_excel(writer, index=False, sheet_name="KEPCO")
                            st.download_button(
                                label="Excel 다운로드 (.xlsx)",
                                data=output.getvalue(),
                                file_name="kepco_result.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            # --- 검색조건/매핑 자동저장 ---
                            save_search_history(number_input, search_type, juris_code)
                            # --- 접수번호 검색이면, 결과에서 고객번호↔지사코드 매핑 자동추출/저장 ---
                            if search_type == "접수번호":
                                # 실제 결과에서 고객번호(CUSTNO)와 지사코드(JURIS_OFFICECD) 필드 확인
                                if "CUSTNO" in df.columns and "JURIS_OFFICECD" in df.columns:
                                    for row in df.itertuples():
                                        cust_no = str(getattr(row, "CUSTNO"))
                                        office_cd = str(getattr(row, "JURIS_OFFICECD"))
                                        # 매핑 자동 저장
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

