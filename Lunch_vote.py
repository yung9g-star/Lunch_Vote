import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import datetime

# ==========================================
# [설정 구역] 멘트와 설정을 여기서 자유롭게 수정하세요 (소프트 코딩)
# ==========================================

ADMIN_PASSWORD = "1079"  # 관리자 비밀번호
DATA_FILE = "lunch_data.json"

# UI에 표시될 텍스트들 (이 부분을 수정하면 화면 글자가 바뀝니다)
TEXT = {
    "app_title": "🌞 맛있는 연구실 점심 투표 🍽️",
    "sidebar_title": "👤 참가자 현황",
    "sidebar_name_label": "닉네임 (본인 이름)",
    "sidebar_participants_list": "📢 현재 접속/참여 중인 멤버",
    
    # 상태별 메인 화면 멘트
    "state_closed_title": "😴 아직 투표가 열리지 않았습니다",
    "state_closed_msg": "관리자가 투표를 시작할 때까지 잠시만 기다려주세요!",
    
    "state_collect_title": "Step 1. 먹고 싶은 메뉴 추천하기 😋",
    "state_collect_desc": "오늘 땡기는 식당을 딱 **1곳**만 적어주세요. (모두의 의견을 모아 추첨합니다)",
    "input_candidate_label": "추천 식당 이름",
    "btn_submit_candidate": "이걸로 추천하기 👆",
    
    "state_vote_title": "Step 2. 최종 결정의 시간 🗳️",
    "state_vote_desc": "랜덤으로 선정된 3곳입니다! 가장 가고 싶은 곳에 투표해주세요.",
    "btn_submit_vote": "최종 결정 완료 👆",
    
    # 관리자 버튼 멘트
    "admin_section": "🛡️ 관리자 기능 (Admin)",
    "btn_open_voting": "📅 투표 시작하기 (세션 오픈)",
    "btn_pick_3": "🎲 추천 마감 & 3곳 랜덤 뽑기",
    "btn_reroll": "♻️ 후보가 별로인가요? 3곳 다시 뽑기 (재추첨)",
    "btn_reset": "🗑️ 데이터 완전 초기화",
    
    # 알림 메시지
    "msg_need_name": "왼쪽 사이드바에서 이름을 먼저 입력해주세요!",
    "msg_already_submitted": "이미 메뉴를 추천하셨습니다. (1인 1추천)",
    "msg_submitted": "추천이 완료되었습니다!",
    "msg_voted": "투표가 완료되었습니다!",
    "msg_admin_only": "관리자만 실행할 수 있습니다.",
    "msg_pw_wrong": "비밀번호가 틀렸습니다.",
    "msg_no_candidates": "후보가 없거나 부족합니다. 3개 이상이어야 추첨 가능합니다.",
}

# ==========================================
# [시스템 로직] 데이터 관리 함수
# ==========================================

def init_default_data():
    """데이터가 없을 때 초기 구조를 생성합니다."""
    default_data = {
        "status": "closed",  # 상태: closed(닫힘), collecting(모집중), voting(투표중)
        "open_date": "",     # 투표 시작 날짜
        "submissions": {},   # { "사용자명": "추천식당" } -> 1인 1메뉴
        "finalists": [],     # 선정된 3곳 리스트
        "final_votes": {}    # { "사용자명": "선택한식당" }
    }
    save_data(default_data)
    return default_data

def load_data():
    """데이터 파일을 불러옵니다."""
    if not os.path.exists(DATA_FILE):
        return init_default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # [수정됨] 데이터 호환성 검사
            # 만약 구버전 데이터(submissions 키가 없음)가 남아있다면 초기화
            if "submissions" not in data or "status" not in data:
                return init_default_data()
            return data
    except:
        # 파일이 깨졌거나 읽을 수 없으면 초기화
        return init_default_data()

def save_data(data):
    """데이터를 저장합니다."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"저장 오류: {e}")

# ==========================================
# [앱 시작] UI 구성
# ==========================================

st.set_page_config(page_title="점심 투표", page_icon="🍚", layout="centered")

# 데이터 로드
data = load_data()

# --- 사이드바 (참가자 정보 & 관리자) ---
with st.sidebar:
    st.header(TEXT["sidebar_title"])
    
    # 1. 닉네임 입력 (필수)
    username = st.text_input(TEXT["sidebar_name_label"], key="user_input")
    
    st.divider()
    
    # 2. 현재 참가자 리스트 보여주기 (누가 추천/투표했는지)
    st.subheader(TEXT["sidebar_participants_list"])
    
    # 추천 단계 참가자 vs 투표 단계 참가자
    # load_data에서 구조를 보장하므로 이제 안전하게 keys() 호출 가능
    active_users = set(data["submissions"].keys()) | set(data["final_votes"].keys())
    
    if active_users:
        for user in active_users:
            # 상태 표시 (메뉴제출완료 / 투표완료)
            status_icon = "✅" 
            st.text(f"{status_icon} {user}")
    else:
        st.caption("아직 참가자가 없습니다.")
        
    st.divider()

    # 3. 관리자 기능 (맨 아래에 배치, Expander로 숨김)
    with st.expander(TEXT["admin_section"]):
        admin_pw = st.text_input("Password", type="password")
        is_admin = (admin_pw == ADMIN_PASSWORD)
        
        if is_admin:
            st.success("Admin Mode On")
            
            # 관리자 기능 1: 투표 시작 (오픈)
            if st.button(TEXT["btn_open_voting"], use_container_width=True):
                data = init_default_data() # 초기화
                data["status"] = "collecting"
                data["open_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(data)
                st.rerun()
            
            # 관리자 기능 2: 3개 추첨 (Step 1 -> 2)
            if data["status"] == "collecting":
                if st.button(TEXT["btn_pick_3"], type="primary", use_container_width=True):
                    # 중복 제거한 식당 리스트 확보
                    candidates_list = list(set(data["submissions"].values()))
                    
                    if len(candidates_list) < 3:
                        st.error(f"❌ {TEXT['msg_no_candidates']} (현재 {len(candidates_list)}개)")
                    else:
                        data["finalists"] = random.sample(candidates_list, 3)
                        data["status"] = "voting"
                        save_data(data)
                        st.rerun()

            # 관리자 기능 3: 재추첨 (Voting 단계에서 맘에 안 들 때)
            if data["status"] == "voting":
                if st.button(TEXT["btn_reroll"], type="primary", use_container_width=True):
                    candidates_list = list(set(data["submissions"].values()))
                    if len(candidates_list) >= 3:
                        # 다시 뽑고, 기존 투표 기록 초기화
                        data["finalists"] = random.sample(candidates_list, 3)
                        data["final_votes"] = {} 
                        save_data(data)
                        st.toast("♻️ 재추첨 완료! 투표가 초기화되었습니다.")
                        st.rerun()
                    else:
                        st.error("후보가 부족해 재추첨할 수 없습니다.")

            # 관리자 기능 4: 완전 초기화
            st.markdown("---")
            if st.button(TEXT["btn_reset"], use_container_width=True):
                os.remove(DATA_FILE)
                st.rerun()
        else:
            if admin_pw:
                st.error(TEXT["msg_pw_wrong"])

# --- 메인 화면 로직 ---

st.title(TEXT["app_title"])
if data["open_date"]:
    st.caption(f"📅 Open Date: {data['open_date']}")
st.markdown("---")

# 닉네임 체크
if not username:
    st.warning(f"👈 {TEXT['msg_need_name']}")
    st.stop()

# ==========================================
# Phase 0: 닫힘 (Closed)
# ==========================================
if data["status"] == "closed":
    st.info(TEXT["state_closed_title"])
    st.write(TEXT["state_closed_msg"])

# ==========================================
# Phase 1: 메뉴 추천 (Collecting)
# ==========================================
elif data["status"] == "collecting":
    st.header(TEXT["state_collect_title"])
    st.markdown(TEXT["state_collect_desc"])
    
    # 내 제출 현황
    my_submission = data["submissions"].get(username)
    
    if my_submission:
        st.success(f"🙆‍♂️ **{username}**님은 **[{my_submission}]**을(를) 추천하셨습니다!")
        st.caption("다른 사람들의 추천을 기다리는 중...")
    else:
        # 입력 폼 (엔터 대신 버튼 클릭 유도)
        with st.form("candidate_form", clear_on_submit=True):
            new_menu = st.text_input(TEXT["input_candidate_label"])
            submitted = st.form_submit_button(TEXT["btn_submit_candidate"])
            
            if submitted:
                if new_menu.strip():
                    data["submissions"][username] = new_menu
                    save_data(data)
                    st.toast(TEXT["msg_submitted"])
                    st.rerun()
                else:
                    st.warning("메뉴 이름을 입력해주세요.")

    # 현재 모인 후보들 보여주기 (중복 없이 칩 형태로)
    st.divider()
    st.subheader(f"📋 현재 추천된 메뉴들 ({len(data['submissions'])}명 참여 중)")
    
    current_candidates = list(set(data["submissions"].values()))
    if current_candidates:
        cols = st.columns(4)
        for i, menu in enumerate(current_candidates):
            cols[i % 4].info(menu)
    else:
        st.write("아직 등록된 메뉴가 없습니다. 1등으로 등록해보세요!")

# ==========================================
# Phase 2: 최종 투표 (Voting)
# ==========================================
elif data["status"] == "voting":
    st.header(TEXT["state_vote_title"])
    st.markdown(TEXT["state_vote_desc"])
    
    finalists = data["finalists"]
    
    # 3개 후보 보여주기 (크게 강조)
    c1, c2, c3 = st.columns(3)
    c1.metric("기호 1번", finalists[0])
    c2.metric("기호 2번", finalists[1])
    c3.metric("기호 3번", finalists[2])
    
    st.divider()
    
    # 투표 폼
    with st.form("vote_form"):
        st.write(f"**{username}**님의 선택은?")
        
        # 라디오 버튼 선택
        my_vote = data["final_votes"].get(username, finalists[0])
        # 만약 이전에 투표한 게 리스트에 없으면(재추첨 등) 초기화
        if my_vote not in finalists:
            my_vote = finalists[0]
            
        choice = st.radio("메뉴 선택", finalists, index=finalists.index(my_vote), label_visibility="collapsed")
        vote_submitted = st.form_submit_button(TEXT["btn_submit_vote"])
        
        if vote_submitted:
            data["final_votes"][username] = choice
            save_data(data)
            st.toast(TEXT["msg_voted"])
            st.rerun()

    # 투표 결과 (실시간)
    st.divider()
    st.subheader("📊 투표 현황")
    
    if data["final_votes"]:
        df = pd.DataFrame(list(data["final_votes"].items()), columns=["닉네임", "선택"])
        
        # 집계
        summary = df["선택"].value_counts().reset_index()
        summary.columns = ["식당", "득표수"]
        
        col_res1, col_res2 = st.columns([1, 2])
        
        with col_res1:
            st.dataframe(summary, hide_index=True, use_container_width=True)
        with col_res2:
            st.bar_chart(summary.set_index("식당"))
            
        # 누가 어디 찍었는지 (투명성)
        with st.expander("누가 어디 찍었는지 보기"):
            st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("아직 투표한 사람이 없습니다.")
