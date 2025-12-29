import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import datetime

# ==========================================
# [설정 구역] 텍스트 및 설정 (Soft Coding)
# ==========================================

ADMIN_PASSWORD = "1079"
DATA_FILE = "lunch_data.json"

TEXT = {
    "app_title": "Lunch Vote",
    "app_subtitle": "🥗 오늘의 점심 메뉴 선정",
    "sidebar_title": "참여자 목록",
    
    # 상태별 메시지
    "state_closed_title": "😴 투표 대기 중",
    "state_closed_msg": "관리자가 투표를 시작할 때까지 대기해주세요.",
    
    "state_collect_title": "Step 1. 메뉴 추천",
    "state_collect_desc": "오늘 땡기는 식당을 **하나만** 추천해주세요.",
    "input_label": "추천할 식당 이름",
    "btn_submit": "추천하기",
    
    "state_vote_title": "Step 2. 최종 선택",
    "state_vote_desc": "선정된 3곳 중 가장 가고 싶은 곳을 선택하세요.",
    "btn_vote": "최종 투표하기",
    
    # 관리자
    "admin_header": "관리자 설정",
    "btn_open": "▶ 투표 시작 (Open)",
    "btn_pick": "🎲 3곳 추첨 (Pick)",
    "btn_reroll": "🔄 재추첨 (Re-roll)",
    "btn_reset": "🗑 초기화 (Reset)",
    
    # 알림
    "msg_welcome": "환영합니다! 닉네임을 입력해주세요.",
    "msg_done_suggest": "추천 완료! 다른 분들을 기다려주세요.",
    "msg_done_vote": "투표 완료! 결과를 확인하세요.",
    "err_no_name": "왼쪽 사이드바에서 닉네임을 먼저 입력해주세요.",
    "err_dup": "이미 추천하셨습니다.",
    "err_admin": "비밀번호가 틀렸습니다.",
    "err_min_cand": "후보가 3개 이상이어야 합니다."
}

# ==========================================
# [디자인] 안전한 CSS 스타일링 (iOS 느낌)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* 기본 폰트 설정 */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', -apple-system, system-ui, sans-serif;
        }
        
        /* 메인 배경 (연한 회색) - 다크모드 대응을 위해 !important 사용 자제 */
        .stApp {
            background-color: #F5F5F7;
        }
        
        /* 컨텐츠 박스 디자인 (카드 형태) */
        .css-1r6slb0, .stContainer {
            background-color: #FFFFFF;
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
        }

        /* 제목 스타일 */
        h1 {
            color: #1D1D1F;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        h3 {
            color: #1D1D1F;
            font-weight: 600;
        }
        p {
            color: #86868B;
        }

        /* 강조 텍스트 (파란색) */
        .highlight {
            color: #007AFF;
            font-weight: bold;
        }

        /* 버튼 스타일 미세 조정 (깨짐 방지) */
        div.stButton > button {
            border-radius: 12px;
            font-weight: 600;
            transition: transform 0.1s;
        }
        div.stButton > button:active {
            transform: scale(0.98);
        }
        
        /* Expander 스타일 */
        .streamlit-expanderHeader {
            background-color: white;
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# [데이터] 로직 함수
# ==========================================

def init_default_data():
    default_data = {
        "status": "closed",
        "submissions": {},
        "finalists": [],
        "final_votes": {}
    }
    save_data(default_data)
    return default_data

def load_data():
    if not os.path.exists(DATA_FILE):
        return init_default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "submissions" not in data: # 구버전 호환
                return init_default_data()
            return data
    except:
        return init_default_data()

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

# ==========================================
# [앱 실행]
# ==========================================

st.set_page_config(page_title="Lunch Vote", page_icon="🍽️", layout="centered")
inject_custom_css()

data = load_data()

# --- 사이드바 ---
with st.sidebar:
    st.header(TEXT["sidebar_title"])
    username = st.text_input("닉네임 (Nickname)", key="user_name")
    
    st.markdown("---")
    
    # 참가자 목록 (깔끔한 리스트)
    active_users = list(set(data["submissions"].keys()) | set(data["final_votes"].keys()))
    
    if active_users:
        st.caption(f"총 {len(active_users)}명 참여 중")
        for user in active_users:
            st.markdown(f"👤 **{user}**")
    else:
        st.caption("아직 참여자가 없습니다.")

    st.markdown("---")
    
    # 관리자 패널
    with st.expander(TEXT["admin_header"]):
        pw = st.text_input("Password", type="password")
        if pw == ADMIN_PASSWORD:
            st.success("Admin Mode")
            
            if st.button(TEXT["btn_open"], use_container_width=True):
                data = init_default_data()
                data["status"] = "collecting"
                save_data(data)
                st.rerun()
                
            if data["status"] == "collecting":
                if st.button(TEXT["btn_pick"], type="primary", use_container_width=True):
                    cands = list(set(data["submissions"].values()))
                    if len(cands) < 3:
                        st.error(TEXT["err_min_cand"])
                    else:
                        data["finalists"] = random.sample(cands, 3)
                        data["status"] = "voting"
                        save_data(data)
                        st.rerun()
                        
            if data["status"] == "voting":
                if st.button(TEXT["btn_reroll"], type="primary", use_container_width=True):
                    cands = list(set(data["submissions"].values()))
                    if len(cands) >= 3:
                        data["finalists"] = random.sample(cands, 3)
                        data["final_votes"] = {}
                        save_data(data)
                        st.rerun()
            
            if st.button(TEXT["btn_reset"], use_container_width=True):
                os.remove(DATA_FILE)
                st.rerun()
        elif pw:
            st.error(TEXT["err_admin"])

# --- 메인 화면 ---

# 헤더
st.title(TEXT["app_title"])
st.markdown(f"**{TEXT['app_subtitle']}**")
st.markdown("---")

if not username:
    st.warning(TEXT["err_no_name"])
    st.stop()

# 상태별 화면
if data["status"] == "closed":
    st.info(TEXT["state_closed_title"])
    st.write(TEXT["state_closed_msg"])

elif data["status"] == "collecting":
    st.subheader(TEXT["state_collect_title"])
    st.markdown(TEXT["state_collect_desc"])
    
    # 카드형 컨테이너
    with st.container():
        if username in data["submissions"]:
            st.success(f"✅ {TEXT['msg_done_suggest']}")
            st.markdown(f"**My Pick:** {data['submissions'][username]}")
        else:
            with st.form("suggest_form"):
                menu = st.text_input(TEXT["input_label"])
                if st.form_submit_button(TEXT["btn_submit"], use_container_width=True):
                    if menu.strip():
                        data["submissions"][username] = menu
                        save_data(data)
                        st.rerun()
                    else:
                        st.warning("메뉴를 입력해주세요.")
    
    st.markdown("")
    st.markdown(f"#### 📋 현재 후보 ({len(data['submissions'])})")
    
    # 후보 칩 스타일 표시
    cands = list(set(data["submissions"].values()))
    if cands:
        # 가독성을 위해 HTML 대신 Streamlit 컬럼 사용 (안전성 확보)
        cols = st.columns(3)
        for i, c in enumerate(cands):
            cols[i%3].info(c)

elif data["status"] == "voting":
    st.subheader(TEXT["state_vote_title"])
    st.markdown(TEXT["state_vote_desc"])
    
    finalists = data["finalists"]
    
    # 후보 3개 강조 표시
    col1, col2, col3 = st.columns(3)
    col1.metric("1번", finalists[0])
    col2.metric("2번", finalists[1])
    col3.metric("3번", finalists[2])
    
    st.markdown("---")
    
    with st.container():
        st.write(f"**{username}**님의 선택")
        
        # 이전 선택값 유지
        prev_choice = data["final_votes"].get(username, finalists[0])
        if prev_choice not in finalists: prev_choice = finalists[0]
        
        with st.form("vote_form"):
            choice = st.radio("선택해주세요", finalists, index=finalists.index(prev_choice))
            if st.form_submit_button(TEXT["btn_vote"], type="primary", use_container_width=True):
                data["final_votes"][username] = choice
                save_data(data)
                st.rerun()
                
    # 결과 그래프
    if data["final_votes"]:
        st.markdown("---")
        st.subheader("📊 실시간 결과")
        
        df = pd.DataFrame(list(data["final_votes"].items()), columns=["User", "Choice"])
        counts = df["Choice"].value_counts()
        
        # 막대 그래프
        st.bar_chart(counts)
        
        # 상세 결과 (Expander)
        with st.expander("상세 투표 내역 보기"):
            st.dataframe(df, use_container_width=True, hide_index=True)
