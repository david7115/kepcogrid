import streamlit as st

st.title("Hello Streamlit!")
st.write("이 앱은 GitHub에서 배포될 수 있습니다.")
import streamlit as st
import pandas as pd
import requests

def fetch_by_id(search_type: str, keyword: str):
    url = "https://online.kepco.co.kr/ew/status/pwtr/search"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    payload = {
        "actID": "EWM079D00",
        "searchType": "customer" if search_type=="고객번호" else "receipt",
        "keyword": keyword
    }
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()

def parse_response(data: dict):
    items = data.get("results", [])
    df = pd.DataFrame(items)
    return df

st.set_page_config(page_title="Kepco 분산형전원 조회", layout="wide")
st.title("📄 KEPCO 분산형전원 접수현황 조회")

search_type = st.radio("조회 방식", ["고객번호", "접수번호"], horizontal=True)
keyword = st.text_input(f"{search_type} 입력", "")
if st.button("조회"):
    try:
        with st.spinner("조회 중..."):
            data = fetch_by_id(search_type, keyword.strip())
            df = parse_response(data)
        if not df.empty:
            st.success("조회 성공")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("CSV 다운로드", csv, file_name="kepco_result.csv")
        else:
            st.warning("검색 결과가 없습니다.")
    except Exception as e:
        st.error(f"오류 발생: {e}")
