import streamlit as st
import requests
import json
import re
import pandas as pd

st.set_page_config(page_title="KEPCO 접속현황 조회기", layout="centered")
st.title("🔌 KEPCO 접속현황 조회기")
st.markdown("접수번호(앞 4자리가 지사코드) 또는 고객번호를 입력하세요. 접수/공용망보강/접속공사 모두 지원.")

number_input = st.text_input("고객번호 또는 접수번호", placeholder="예: 4830-20231115-010412 또는 12-2945-7459")
query_type = st.selectbox("조회 유형", ["접수", "공용망보강", "접속공사"])
search_button = st.button("🔍 조회하기")

API_URL = "https://online.kepco.co.kr/ew/status/pwtr/search"

def extract_officecd(acpt_no):
    # 접수번호 맨 앞 4자리의 숫자를 지사코드로 사용
    nums = re.findall(r'\d+', acpt_no)
    if nums and len(nums[0]) >= 4:
        return nums[0][:4]
    return None

if search_button and number_input.strip():
    acpt_no = number_input.strip()
    officecd = extract_officecd(acpt_no)
    if not officecd:
        st.warning("접수번호 또는 고객번호 앞 4자리에서 올바른 지사코드를 추출할 수 없습니다.")
    else:
        payload = {"dma_param": {"jurisOfficecd": officecd, "acptNo": acpt_no}}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "Referer": "https://online.kepco.co.kr/EWM079D00",
            "Origin": "https://online.kepco.co.kr",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            # "Cookie": "...", # 필요하다면 실제 브라우저에서 복사
        }

        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            text = resp.text.strip()
            if resp.status_code == 200 and text:
                try:
                    data = resp.json()
                    # dlt_stepA, dlt_stepB, dlt_stepC가 모두 결과 list
                    resultlist = []
                    for key in ['dlt_stepA', 'dlt_stepB', 'dlt_stepC']:
                        rows = data.get(key)
                        if rows and isinstance(rows, list):
                            resultlist.extend(rows)
                    # fallback: 기존 list 위치에도 결과가 있으면 추가
                    if not resultlist:
                        # stepB 등 없을 경우, result->data->list 또는 resultList 활용
                        resultlist = (
                            data.get("resultList")
                            or data.get("list")
                            or data.get("data", {}).get("list")
                            or data.get("result", {}).get("data", {}).get("list")
                            or []
                        )
                    if resultlist:
                        st.success("✅ 조회 성공")
                        st.dataframe(pd.DataFrame(resultlist), use_container_width=True)
                        st.download_button("CSV 다운로드", data=pd.DataFrame(resultlist).to_csv(index=False), file_name="kepco_result.csv")
                    else:
                        st.warning("📭 조회 결과가 없습니다. 입력값/유형/지사코드를 다시 확인하세요.")
                except Exception as e:
                    st.error(f"❌ 응답 파싱 오류: {e}")
                    st.code(text[:500], language="html")
            else:
                st.warning("⚠️ 유효한 응답이 없습니다. 입력값/지사코드/유형을 다시 확인하세요.")
        except Exception as e:
            st.error(f"🚨 조회 중 오류 발생: {e}")

elif search_button:
    st.warning("고객번호 또는 접수번호를 입력하세요.")
