import streamlit as st
import requests
import pandas as pd
import io
import re

st.set_page_config(page_title="한전 분산전원 연계 접수진행현황 조회", layout="wide")

# --- 중앙 타이틀 ---
st.markdown('<h1 style="text-align:center;">🔌 한전 분산전원 연계 접수진행현황 조회</h1>', unsafe_allow_html=True)

# --- 제목 아래, 좌측정렬로 버전 표시 ---
st.markdown(
    '<div style="text-align:left; color:#222; font-size:0.97em; opacity:.7; margin-bottom:18px;">'
    '프로그램 제작 SAVE ENERGY VER 1.0'
    '</div>',
    unsafe_allow_html=True
)

# --- 입력란/버튼 중앙정렬 ---
col_blank1, col_main, col_blank2 = st.columns([2,5,2])
with col_main:
    st.markdown("#### <span style='color:#193a5a;'>📥 접수번호를 입력하세요</span>", unsafe_allow_html=True)
    number_input = st.text_input("", placeholder="예: 4830-20231115-010412 또는 483020180226000077")
    search_button = st.button("🔍 조회하기", use_container_width=True)

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
    num_only = re.sub(r'\D', '', num)
    dash_type = bool(re.match(r'^\d{4}-\d{8}-\d{6,}$', num))
    return (15 <= len(num_only) <= 20) or dash_type

# --- 최근검색조건 중앙정렬 ---
with col_main:
    with st.expander("📁 최근 검색조건", expanded=True):
        if st.session_state["search_history"]:
            for entry in st.session_state["search_history"]:
                st.markdown(
                    f'<div style="background:#fffce6; border-radius:0.7rem; padding:0.7rem 1rem; margin-bottom:1rem;'
                    f'border-left:6px solid #ffcd38; font-size:1.08em;">'
                    f'접수번호: <b style="color:#1a36b3;">{entry["접수번호"]}</b> '
                    f'| 지사코드: <b style="color:#125a21;">{entry["지사코드"]}</b>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown('<div style="background:#fffce6;border-radius:0.7rem;padding:0.7rem 1rem;">_(아직 저장된 검색 기록이 없습니다.)_</div>', unsafe_allow_html=True)

if search_button:
    with col_main:
        if not number_input.strip():
            st.warning("접수번호를 입력하세요.")
        elif not is_acptno_format(number_input):
            st.error("접수번호 형식이 올바르지 않습니다.<br>- 15~20자리 숫자 또는 xxxx-yyyyyyyy-zzzzzz 형식이어야 합니다.", unsafe_allow_html=True)
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
                    st.markdown(
                        f'<div style="background:#f5f7fb;border-radius:1.2rem;'
                        f'padding:1.2rem 2rem 1.0rem 2rem;box-shadow:0 2px 12px rgba(10,40,130,.10);margin-bottom:2rem;">'
                        f'<b>검색조건</b> : 접수번호 <span style="color:#2248ab">{number_input}</span> '
                        f'| <b>지사코드</b> <span style="color:#097b56">{juris_code}</span>'
                        f'</div>', unsafe_allow_html=True
                    )
                    if resp.status_code == 200 and text:
                        try:
                            data = resp.json()
                            resultlist = extract_resultlist(data)
                            cnt = None
                            for k in ["cnt_stepB", "cnt", "CNT", "cnt_stepb"]:
                                if k in data:
                                    cnt = data[k]
                                    break
                            if not cnt:
                                cnt = len(resultlist)
                            if resultlist:
                                df = pd.DataFrame(resultlist)
                                # END_YM 대체
                                if "END_YM" in df.columns and "ENDYM" in df.columns:
                                    df["END_YM"] = df["END_YM"].combine_first(df["ENDYM"])
                                # 접속예정순서
                                total_cnt = str(cnt)
                                df.insert(
                                    0,
                                    "접속예정순서",
                                    [f"{i+1}/{total_cnt}" for i in range(len(df))]
                                )
                                # ==== [상단: 나의 접수번호 조회 결과 카드] ====
                                my_row = None
                                input_clean = value_clean
                                for key in ["ACPT_SEQNO", "접수번호", "acpt_seqno", "ACPTNO"]:
                                    if key in df.columns:
                                        match_row = df[df[key].astype(str).str.replace("-", "") == input_clean]
                                        if not match_row.empty:
                                            my_row = match_row.iloc[0]
                                            break
                                if my_row is not None:
                                    row_html = ""
                                    for field in df.columns[:8]:
                                        val = my_row[field]
                                        row_html += f"<tr><td style='padding:.24em .8em;color:#125a21;font-weight:600;'>{field}</td><td style='padding:.24em .8em;color:#1943a6;font-weight:600;'>{val}</td></tr>"
                                    st.markdown(
                                        f"""<div style="background:#e7f9ed;border-radius:1.2rem;
                                        padding:1.3rem 2rem 1rem 2rem;box-shadow:0 2px 16px rgba(10,130,40,.11);
                                        margin-bottom:2.1rem;font-size:1.12em;">
                                            <b>🟢 나의 접수번호 조회 결과</b>
                                            <table style="margin-top:8px;">
                                            {row_html}
                                            </table>
                                        </div>""", unsafe_allow_html=True
                                    )
                                else:
                                    st.info("입력한 접수번호와 정확히 일치하는 행을 결과에서 찾지 못했습니다.")
                                # ==== [전체 표/엑셀 다운로드] ====
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
    with col_main:
        st.warning("접수번호를 입력하세요.")
