import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import datetime

# ==========================================
# [설정 구역] 멘트와 설정 (Soft Coding)
# ==========================================

ADMIN_PASSWORD = "1079"
DATA_FILE = "lunch_data.json"

TEXT = {
    "app_title": "Lunch Vote",
    "app_subtitle": "연구실 점심 메뉴 선정",
    "sidebar_title": "Participants",
    "sidebar_participants_list": "접속 중인 멤버",
    
    # 상태별 멘트
    "state_closed_title": "투표 대기 중",
    "state_closed_msg": "관리자가 세션을 시작할 때까지 잠시만 기다려주세요.",
    
    "state_collect_title": "메뉴 추천",
    "state_collect_desc": "오늘 먹고 싶은 식당을 **하나만** 추천해주세요.",
    "input_candidate_label": "식당 이름",
    "btn_submit_candidate": "추천하기",
    
    "state_vote_title": "최종 선택",
    "state_vote_desc": "랜덤 선정된 3곳 중 가장 끌리는 곳을 선택하세요.",
    "btn_submit_vote": "투표하기",
    
    # 관리자
    "admin_section": "Admin Controls",
    "btn_open_voting": "투표 시작 (Session Open)",
    "btn_pick_3": "마감 & 3곳 추첨",
    "btn_reroll": "재추첨 (Re-roll)",
    "btn_reset": "초기화 (Reset)",
    
    # 메시지
    "msg_need_name": "닉네임을 먼저 설정해주세요.",
    "msg_submitted": "추천이 완료되었습니다.",
    "msg_voted": "투표가 완료되었습니다.",
    "msg_pw_wrong": "비밀번호가 올바르지 않습니다.",
    "msg_no_candidates": "후보가 부족합니다 (최소 3개).",
}

# ==========================================
# [디자인] iOS 스타일 커스텀 CSS
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        /* 1. 전체 폰트 및 배경 설정 (San Francisco 느낌) */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans KR", sans-serif;
        }
        
        /* 메인 배경색: iOS 라이트 모드 배경 */
        .stApp {
            background-color: #F2F2F7;
        }

        /* 2. 카드 스타일 (iOS 위젯 느낌) */
        div.stContainer, div[data-testid="stForm"] {
            background-color: #FFFFFF;
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
            border: 1px solid rgba(0, 0, 0, 0.02);
        }

        /* 3. 헤더 스타일 */
        h1 {
            color: #1C1C1E;
            font-weight: 700 !important;
            letter-spacing: -0.5px;
            font-size: 2.2rem !important;
        }
        h2, h3 {
            color: #1C1C1E;
            font-weight: 600 !important;
            letter-spacing: -0.3px;
        }
        p, label {
            color: #3A3A3C;
        }

        /* 4. 입력창 스타일 (회색 배경, 둥근 모서리) */
        .stTextInput > div > div > input {
            background-color: #E5E5EA !important;
            border-radius: 12px !important;
            border: none !important;
            color: #000000 !important;
            padding: 12px 15px !important;
            font-size: 16px !important;
        }
        .stTextInput > div > div > input:focus {
            box-shadow: 0 0 0 2px #007AFF !important;
        }

        /* 5. 버튼 스타일 (iOS Blue Pills) */
        .stButton > button {
            background-color: #007AFF !important;
            color: white !important;
            border-radius: 20px !important;
            border: none !important;
            font-weight: 600 !important;
            padding: 10px 24px !important;
            font-size: 16px !important;
            transition: all 0.2s ease;
            width: 100%;
        }
        .stButton > button:hover {
            background-color: #0062CC !important;
            transform: scale(1.02);
        }
        .stButton > button:active {
            transform: scale(0.98);
        }
        
        /* 2차 버튼 (회색) */
        button[kind="secondary"] {
            background-color: #E5E5EA !important;
            color: #007AFF !important;
        }

        /* 6. 메트릭(결과) 카드 스타일 */
        div[data-testid="stMetric"] {
            background-color: #F2F2F7;
            padding: 15px;
            border-radius: 16px;
            text-align: center;
        }
        div[data-testid="stMetricLabel"] {
            color: #8E8E93 !important;
            font-size: 0.9rem !important;
        }
        div[data-testid="stMetricValue"] {
            color: #000000 !important;
            font-size: 1.5rem !important;
            font-weight: 700 !important;
        }

        /* 7. 라디오 버튼 스타일 */
        .stRadio > div {
            background-color: transparent;
        }
        
        /* 8. 사이드바 스타일 */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E5E5EA;
        }
        
        /* Expander (아코디언) 스타일 */
        .streamlit-expanderHeader {
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E5E5EA;
        }
        
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# [시스템 로직] 데이터 관리 함수
# ==========================================

def init_default_data():
    default_data = {
        "status": "closed",
        "open_date": "",
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
            if "submissions" not in data or "status" not in data:
                return init_default_data()
            return data
    except:
        return init_default_data()

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Save Error: {e}")

# ==========================================
# [앱 시작]
# ==========================================

st.set_page_config(page_title="Lunch Vote", page_icon="🍽️", layout="centered")
inject_custom_css() # CSS 주입

data = load_data()

# --- 사이드바 ---
with st.sidebar:
    st.markdown(f"### 👤 {TEXT['sidebar_title']}")
    
    # 닉네임 입력 (iOS 스타일 텍스트박스)
    username = st.text_input("Name", placeholder="Nickname", key="user_input")
    
    st.divider()
    
    st.markdown(f"**{TEXT['sidebar_participants_list']}**")
    
    active_users = set(data["submissions"].keys()) | set(data["final_votes"].keys())
    
    if active_users:
        # 참가자 목록을 태그 스타일로 표시
        for user in active_users:
            st.markdown(f"""
            <div style="
                background-color: #E5E5EA;
                padding: 8px 12px;
                border-radius: 20px;
                margin-bottom: 6px;
                font-size: 14px;
                color: #3A3A3C;
                display: flex;
                align-items: center;
            ">
                <span style="margin-right: 8px;">🟢</span> {user}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No participants yet.")
        
    st.divider()

    # 관리자 (깔끔하게 숨김)
    with st.expander(TEXT["admin_section"]):
        admin_pw = st.text_input("Admin Password", type="password")
        is_admin = (admin_pw == ADMIN_PASSWORD)
        
        if is_admin:
            st.success("Admin Access Granted")
            
            if st.button(TEXT["btn_open_voting"]):
                data = init_default_data()
                data["status"] = "collecting"
                data["open_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(data)
                st.rerun()
            
            if data["status"] == "collecting":
                if st.button(TEXT["btn_pick_3"]):
                    candidates_list = list(set(data["submissions"].values()))
                    if len(candidates_list) < 3:
                        st.error(f"{TEXT['msg_no_candidates']} ({len(candidates_list)})")
                    else:
                        data["finalists"] = random.sample(candidates_list, 3)
                        data["status"] = "voting"
                        save_data(data)
                        st.rerun()

            if data["status"] == "voting":
                if st.button(TEXT["btn_reroll"]):
                    candidates_list = list(set(data["submissions"].values()))
                    if len(candidates_list) >= 3:
                        data["finalists"] = random.sample(candidates_list, 3)
                        data["final_votes"] = {} 
                        save_data(data)
                        st.toast("Re-rolled!")
                        st.rerun()
                    else:
                        st.error("Not enough candidates.")

            st.markdown("---")
            if st.button(TEXT["btn_reset"]):
                os.remove(DATA_FILE)
                st.rerun()
        else:
            if admin_pw:
                st.error(TEXT["msg_pw_wrong"])

# --- 메인 화면 ---

# 타이틀 섹션 (iOS Large Title 느낌)
st.markdown(f"""
<div style="margin-bottom: 20px;">
    <p style="color: #007AFF; font-weight: 600; font-size: 14px; margin-bottom: 4px; text-transform: uppercase;">
        {datetime.now().strftime('%B %d, %A')}
    </p>
    <h1 style="margin: 0; padding: 0;">{TEXT['app_title']}</h1>
    <p style="color: #8E8E93; font-size: 18px; margin-top: 4px;">{TEXT['app_subtitle']}</p>
</div>
""", unsafe_allow_html=True)


# 닉네임 미입력 시 블러 처리 느낌의 경고
if not username:
    st.info(f"👉 {TEXT['msg_need_name']}")
    st.stop()


# 컨텐츠 컨테이너
with st.container():
    
    # Phase 0: Closed
    if data["status"] == "closed":
        st.subheader(TEXT["state_closed_title"])
        st.write(TEXT["state_closed_msg"])

    # Phase 1: Collecting
    elif data["status"] == "collecting":
        st.subheader(TEXT["state_collect_title"])
        st.markdown(TEXT["state_collect_desc"])
        
        my_submission = data["submissions"].get(username)
        
        if my_submission:
            # 제출 완료 카드
            st.markdown(f"""
            <div style="
                background-color: #34C759; 
                color: white; 
                padding: 16px; 
                border-radius: 16px; 
                text-align: center; 
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3);
            ">
                <div style="font-size: 14px; opacity: 0.9;">My Choice</div>
                <div style="font-size: 24px; font-weight: 700;">{my_submission}</div>
            </div>
            """, unsafe_allow_html=True)
            st.caption("Waiting for others...")
        else:
            # 입력 폼
            with st.form("candidate_form", clear_on_submit=True):
                new_menu = st.text_input(TEXT["input_candidate_label"], placeholder="예: 쉑쉑버거")
                st.markdown("<br>", unsafe_allow_html=True) # 간격
                submitted = st.form_submit_button(TEXT["btn_submit_candidate"])
                
                if submitted:
                    if new_menu.strip():
                        data["submissions"][username] = new_menu
                        save_data(data)
                        st.toast(TEXT["msg_submitted"])
                        st.rerun()
                    else:
                        st.warning("메뉴 이름을 입력해주세요.")

        # 후보 리스트 (Tag Cloud 스타일)
        st.markdown("---")
        st.markdown(f"##### Current Candidates ({len(data['submissions'])})")
        
        current_candidates = list(set(data["submissions"].values()))
        if current_candidates:
            # HTML로 예쁘게 렌더링
            tags_html = ""
            for menu in current_candidates:
                tags_html += f"""
                <span style="
                    display: inline-block;
                    background-color: #F2F2F7;
                    color: #007AFF;
                    padding: 8px 16px;
                    border-radius: 20px;
                    margin: 4px;
                    font-size: 14px;
                    font-weight: 500;
                ">
                    {menu}
                </span>
                """
            st.markdown(f"<div>{tags_html}</div>", unsafe_allow_html=True)

    # Phase 2: Voting
    elif data["status"] == "voting":
        st.subheader(TEXT["state_vote_title"])
        st.markdown(TEXT["state_vote_desc"])
        
        finalists = data["finalists"]
        
        # 3개 후보 카드 표시
        col1, col2, col3 = st.columns(3)
        col1.metric("Option 1", finalists[0])
        col2.metric("Option 2", finalists[1])
        col3.metric("Option 3", finalists[2])
        
        st.markdown("---")
        
        # 투표 폼
        with st.form("vote_form"):
            my_vote = data["final_votes"].get(username, finalists[0])
            if my_vote not in finalists:
                my_vote = finalists[0]
                
            st.write(f"**{username}**'s Pick:")
            choice = st.radio("Choose one", finalists, index=finalists.index(my_vote), label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            vote_submitted = st.form_submit_button(TEXT["btn_submit_vote"])
            
            if vote_submitted:
                data["final_votes"][username] = choice
                save_data(data)
                st.toast(TEXT["msg_voted"])
                st.rerun()

        # 결과
        st.markdown("---")
        st.subheader("Live Results")
        
        if data["final_votes"]:
            df = pd.DataFrame(list(data["final_votes"].items()), columns=["User", "Choice"])
            summary = df["Choice"].value_counts().reset_index()
            summary.columns = ["Restaurant", "Votes"]
            
            # Progress bar 스타일로 결과 표시
            for index, row in summary.iterrows():
                percentage = int((row["Votes"] / len(df)) * 100)
                st.markdown(f"""
                <div style="margin-bottom: 15px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                        <span style="font-weight:600; color:#1C1C1E;">{row['Restaurant']}</span>
                        <span style="color:#007AFF; font-weight:600;">{row['Votes']}명 ({percentage}%)</span>
                    </div>
                    <div style="width:100%; background-color:#E5E5EA; border-radius:10px; height:10px;">
                        <div style="width:{percentage}%; background-color:#007AFF; border-radius:10px; height:10px; transition:width 0.5s;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with st.expander("Show Details"):
                st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("No votes yet.")
