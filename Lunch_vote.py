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
    "app_title": "🥗 오늘의 점심 메뉴 선정",
    "app_subtitle": "연구실 점심 투표 시스템",
    "sidebar_title": "참여자 목록",
    
    # 상태별 메시지
    "state_closed_title": "⛔ 투표 대기 중",
    "state_closed_msg": "관리자가 투표를 시작할 때까지 대기해주세요.",
    
    "state_collect_title": "Step 1. 메뉴 추천하기",
    "state_collect_desc": "오늘 먹고 싶은 식당을 **하나만** 추천해주세요.",
    "input_label": "추천할 식당 이름 입력",
    "btn_submit": "이 메뉴로 추천하기",
    
    "state_vote_title": "Step 2. 최종 선택하기",
    "state_vote_desc": "선정된 3곳 중 가장 가고 싶은 곳을 선택하세요.",
    "btn_vote": "최종 투표 제출",
    
    # 관리자
    "admin_header": "관리자 설정 (Admin)",
    "btn_open": "▶ 투표 시작 (Open)",
    "btn_pick": "🎲 3곳 추첨 (Pick)",
    "btn_reroll": "🔄 다시 뽑기 (Re-roll)",
    "btn_reset": "🗑 데이터 초기화 (Reset)",
    
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
# [디자인] 강제 화이트 모드 (색상 고정)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* 1. 전체 배경 흰색 고정 */
        .stApp {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        
        /* 2. 사이드바 배경 밝은 회색 고정 */
        section[data-testid="stSidebar"] {
            background-color: #F8F9FA !important;
        }
        section[data-testid="stSidebar"] * {
            color: #333333 !important;
        }
        
        /* 3. 입력창 디자인 고정 (흰 배경, 검은 글씨) */
        div[data-testid="stTextInput"] input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #DDDDDD !important;
        }
        
        /* 4. 텍스트 가독성 확보 */
        h1, h2, h3, p, div, span, label {
            color: #000000 !important;
        }
        
        /* 5. 버튼 스타일 (기본 파란색 유지하되 텍스트 흰색 고정) */
        div.stButton > button {
            color: #FFFFFF !important;
            border: none;
        }
        
        /* 6. 경고/성공 메시지 박스 텍스트 색상 예외 처리 */
        div[data-testid="stAlert"] p, div[data-testid="stAlert"] div {
            color: inherit !important; 
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

st.set_page_config(page_title="Lunch Vote", page_icon="🍚", layout="centered")
inject_custom_css() # 강제 화이트 모드 적용

data = load_data()

# --- 사이드바 ---
with st.sidebar:
    st.header(TEXT["sidebar_title"])
    username = st.text_input("닉네임 (이름)", key="user_name")
    
    st.markdown("---")
    
    # 참가자 목록
    active_users = list(set(data["submissions"].keys()) | set(data["final_votes"].keys()))
    
    if active_users:
        st.caption(f"현재 {len(active_users)}명 참여 중")
        # 깔끔하게 불렛 포인트로 표시
        for user in active_users:
            st.markdown(f"- {user}")
    else:
        st.caption("아직 참여자가 없습니다.")

    st.markdown("---")
    
    # 관리자 패널
    with st.expander(TEXT["admin_header"]):
        pw = st.text_input("비밀번호", type="password")
        if pw == ADMIN_PASSWORD:
            st.success("관리자 권한 확인됨")
            
            # 버튼들 사이 간격 확보
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
            
            st.markdown("---")
            if st.button(TEXT["btn_reset"], use_container_width=True):
                os.remove(DATA_FILE)
                st.rerun()
        elif pw:
            st.error(TEXT["err_admin"])

# --- 메인 화면 ---

st.title(TEXT["app_title"])
st.write(TEXT["app_subtitle"])
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
    
    # 컨테이너 사용하여 구역 구분
    with st.container():
        if username in data["submissions"]:
            st.success(f"✅ {TEXT['msg_done_suggest']}")
            st.info(f"**나의 추천:** {data['submissions'][username]}")
        else:
            with st.form("suggest_form"):
                menu = st.text_input(TEXT["input_label"])
                # 엔터키 제출 방지 및 명확한 버튼 클릭 유도
                if st.form_submit_button(TEXT["btn_submit"], use_container_width=True):
                    if menu.strip():
                        data["submissions"][username] = menu
                        save_data(data)
                        st.rerun()
                    else:
                        st.warning("메뉴 이름을 입력해주세요.")
    
    st.markdown("---")
    st.subheader(f"📋 현재 추천된 메뉴 ({len(data['submissions'])})")
    
    cands = list(set(data["submissions"].values()))
    if cands:
        # 가독성 좋은 컬럼 배치
        cols = st.columns(3)
        for i, c in enumerate(cands):
            # Streamlit 기본 버튼 스타일을 활용하여 깔끔하게 표시 (클릭 기능 없음)
            cols[i%3].text_input(label=f"후보 {i+1}", value=c, disabled=True, key=f"cand_{i}")
    else:
        st.write("아직 등록된 메뉴가 없습니다.")

elif data["status"] == "voting":
    st.subheader(TEXT["state_vote_title"])
    st.markdown(TEXT["state_vote_desc"])
    
    finalists = data["finalists"]
    
    # 후보 3개 강조 (Metrics 사용)
    col1, col2, col3 = st.columns(3)
    col1.metric("기호 1번", finalists[0])
    col2.metric("기호 2번", finalists[1])
    col3.metric("기호 3번", finalists[2])
    
    st.markdown("---")
    
    with st.container():
        st.write(f"**{username}**님의 선택")
        
        prev_choice = data["final_votes"].get(username, finalists[0])
        if prev_choice not in finalists: prev_choice = finalists[0]
        
        with st.form("vote_form"):
            choice = st.radio("하나를 선택해주세요", finalists, index=finalists.index(prev_choice))
            if st.form_submit_button(TEXT["btn_vote"], type="primary", use_container_width=True):
                data["final_votes"][username] = choice
                save_data(data)
                st.rerun()
                
    # 결과 그래프
    if data["final_votes"]:
        st.markdown("---")
        st.subheader("📊 실시간 득표 현황")
        
        df = pd.DataFrame(list(data["final_votes"].items()), columns=["닉네임", "선택"])
        counts = df["선택"].value_counts()
        
        st.bar_chart(counts)
        
        with st.expander("누가 어디에 투표했나요?"):
            st.dataframe(df, use_container_width=True, hide_index=True)
