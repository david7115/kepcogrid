import streamlit as st
import requests
import json
import re
import pandas as pd

st.set_page_config(page_title="KEPCO 접속현황 조회기", layout="centered")
st.title("🔌 KEPCO 접속현황 조회기")
st.markdown("""
접수번호(앞 4자리가 지사코드) 또는 고객번호를 입력하세요.
- 접수/공용망보강/접속공사 모두 지원
- 서버 사정에 따라 **조회가 10~20초 이상 지연**될 수 있습니다.
""")

number_input = st.text_input("고객번호 또는 접수번호", placeholder="예: 4830-20231115-010412 또는 12-2945-7459")
query_type = st.selectbox("조회 유형", ["접수", "공용망보강", "접속공사"])
search_button = st.button("🔍 조회하기")

API_URL = "https://online.kepco.co.kr/ew/status/pwtr/search"

def extract_officecd(acpt_no):
    nums = re.findall(r'\d+', acpt_no)
    return nums[0][:4] if nums and len(nums[0]) >= 4 else None

def parse_response(data):
    # 다양한 응답 구조 지원 (dlt_stepA, dlt_stepB, dlt_stepC + fallback)
    resultlist = []
    for key in ['dlt_stepA', 'dlt_stepB', 'dlt_stepC']:
        if key in data and isinstance(data[key], list):
            resultlist.extend(data[key])
    if not resultlist:
        # fallback (resultList, list 등)
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
                "User-Agent": "Mozilla/5.0"
                # "Cookie": "...",  # 내부망/세션 필요시
            }

            with st.spinner("서버 조회 중... (최대 30초 소요될 수 있습니다)"):
                try:
                    resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                    text = resp.text.strip()
                    if resp.status_code == 200 and text:
                        try:
                            data = resp.json()
                            rows = parse_response(data)
                            if rows:
                                df = pd.DataFrame(rows)
                                st.success(f"✅ {len(df)}건 조회 성공")
                                st.dataframe(df, use_container_width=True)
                                csv = df.to_csv(index=False, encoding="utf-8-sig")
                                st.download_button("CSV 다운로드", csv, file_name="kepco_result.csv")
                            else:
                                st.warning("📭 조회 결과가 없습니다. 입력값/유형/지사코드를 다시 확인하세요.")
                        except Exception as e:
                            st.error(f"❌ 응답 파싱 오류: {e}")
                            st.code(text[:500], language="html")
                    else:
                        st.warning("⚠️ 유효한 응답이 없습니다. 서버 부하나 입력값 오류일 수 있습니다.")
                except requests.exceptions.Timeout:
                    st.error("❌ 서버 응답이 30초를 초과하여 타임아웃되었습니다.\n한전 서버 상황에 따라 다시 시도해보세요.")
                except Exception as e:
                    st.error(f"🚨 조회 중 오류 발생: {e}")
