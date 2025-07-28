import streamlit as st
import requests
import pandas as pd
import io

st.set_page_config(page_title="KEPCO 접속현황 조회기", layout="centered")
st.title("🔌 KEPCO 접속현황 조회기 (Excel 다운로드 지원)")

number_input = st.text_input("고객번호 또는 접수번호", placeholder="예: 4830-20231115-010412 또는 12-2945-7459")
search_type = st.selectbox("검색유형", ["접수번호", "고객번호"])
search_button = st.button("🔍 조회하기")

API_URL = "https://online.kepco.co.kr/ew/status/pwtr/search"

def build_payload(search_type, value):
    value_clean = value.replace("-", "").strip()
    if search_type == "접수번호":
        juris_code = "4830"
        return {"dma_param": {"jurisOfficecd": juris_code, "acptNo": value_clean}}
    elif search_type == "고객번호":
        juris_code = value_clean[:2]
        return {"dma_param": {"jurisOfficecd": juris_code, "custNo": value_clean}}
    else:
        return None

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

if search_button:
    if not number_input.strip():
        st.warning("고객번호 또는 접수번호를 입력하세요.")
    else:
        payload = build_payload(search_type, number_input)
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
                        if resultlist:
                            df = pd.DataFrame(resultlist)
                            st.success(f"{len(df)}건 조회 성공")
                            st.dataframe(df, use_container_width=True)
                            # Excel 변환
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                                df.to_excel(writer, index=False, sheet_name="KEPCO")
                            st.download_button(
                                label="Excel 다운로드 (.xlsx)",
                                data=output.getvalue(),
                                file_name="kepco_result.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
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

