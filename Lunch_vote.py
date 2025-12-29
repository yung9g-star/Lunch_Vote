import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import datetime

# ==========================================
# [설정 및 텍스트 구역]
# ==========================================

ADMIN_PASSWORD = "1079"
DATA_FILE = "lunch_data.json"

TEXT = {
    "sidebar_title": "사용자 접속",
    
    # 상태별 메시지
    "state_closed_title": "투표 세션 대기",
    "state_closed_msg": "현재 활성화된 투표가 없습니다. 관리자의 세션 시작을 대기해 주십시오.",
    
    "state_collect_title": "Step 1. 식당 메뉴 추천",
    "state_collect_desc": "금일 방문을 희망하는 식당 **1곳**을 입력해 주십시오.",
    "input_label": "식당 이름 입력",
    "btn_submit": "추천 등록",
    
    "state_vote_title": "Step 2. 최종 방문지 선택",
    "state_vote_desc": "무작위로 선정된 3곳 중, 본인이 방문할 식당을 선택해 주십시오.",
    "btn_vote": "선택 완료",
    
    # 관리자
    "admin_header": "관리자 전용 기능",
    "btn_open": "투표 세션 시작",
    "btn_pick": "추천 마감 및 후보 3곳 추첨",
    "btn_reroll": "후보 재추첨",
    "btn_reset": "데이터 초기화",
    
    # 알림
    "msg_done_suggest": "추천이 정상적으로 등록되었습니다.",
    "err_no_name": "좌측 사이드바에서 성함을 입력 후 '입장하기'를 눌러주십시오.",
    "err_min_cand": "후보가 최소 3개 이상이어야 추첨이 가능합니다."
}

# ==========================================
# [데이터 관리 함수]
# ==========================================

def init_default_data():
    default_data = {
        "status": "closed",      # closed, collecting, voting
        "target_date": "",       # 투표 대상 날짜 (예: 2024-05-20)
        "submissions": {},       # { "사용자명": "식당명" }
        "finalists": [],         # [식당1, 식당2, 식당3]
        "final_votes": {}        # { "사용자명": "선택한식당" }
    }
    save_data(default_data)
    return default_data

def load_data():
    if not os.path.exists(DATA_FILE):
        return init_default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "submissions" not in data or "target_date" not in data:
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
# [앱 실행 및 레이아웃]
# ==========================================

st.set_page_config(page_title="점심 투표 시스템", page_icon="🍚", layout="centered")

# 데이터 로드
data = load_data()

# [세션 상태 관리] 이름 고정 및 URL 연동 로직
# 1. URL에 name 파라미터가 있으면 가져옴 (새로고침 방어)
if "name" in st.query_params:
    st.session_state.locked_name = st.query_params["name"]

if "locked_name" not in st.session_state:
    st.session_state.locked_name = None

# --- 사이드바 ---
with st.sidebar:
    st.header(TEXT["sidebar_title"])
    
    # 1. 사용자 입장 (이름 고정 기능 + 로그아웃)
    if st.session_state.locked_name:
        st.success(f"접속자: **{st.session_state.locked_name}** 님")
        
        # 이름 변경 (로그아웃) 버튼
        if st.button("이름 변경 / 로그아웃", type="secondary", use_container_width=True):
            st.session_state.locked_name = None
            # URL 파라미터 초기화 (Streamlit 버전에 따라 다를 수 있음, 최신 기준)
            if "name" in st.query_params:
                del st.query_params["name"]
            st.rerun()
            
        username = st.session_state.locked_name
    else:
        with st.form("login_form"):
            input_name = st.text_input("성함", placeholder="본인 성함을 입력하세요")
            btn_login = st.form_submit_button("입장하기")
            
            if btn_login:
                if input_name.strip():
                    st.session_state.locked_name = input_name
                    # URL에 이름 저장 -> 새로고침 해도 유지됨
                    st.query_params["name"] = input_name
                    st.rerun()
                else:
                    st.warning("성함을 입력해 주십시오.")
        username = None

    st.markdown("---")
    
    # 2. 현재 참여 현황
    active_users = list(set(data["submissions"].keys()) | set(data["final_votes"].keys()))
    if active_users:
        st.markdown(f"**현재 참여 인원: {len(active_users)}명**")
        for user in active_users:
            st.text(f"- {user}")
    else:
        st.caption("참여자가 없습니다.")

    st.markdown("---")
    
    # 3. 관리자 패널
    with st.expander(TEXT["admin_header"]):
        pw = st.text_input("관리자 비밀번호", type="password")
        if pw == ADMIN_PASSWORD:
            st.success("관리자 권한 인증됨")
            
            # (1) 투표 시작
            st.markdown("#### 세션 관리")
            default_date = datetime.now().date()
            pick_date = st.date_input("투표 날짜 설정", value=default_date)
            
            if st.button(TEXT["btn_open"], use_container_width=True):
                data = init_default_data()
                data["status"] = "collecting"
                data["target_date"] = pick_date.strftime("%Y-%m-%d")
                save_data(data)
                st.rerun()
            
            st.markdown("---")
            st.markdown("#### 진행 관리")

            # (2) 추첨
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
            
            # (3) 재추첨
            if data["status"] == "voting":
                if st.button(TEXT["btn_reroll"], type="primary", use_container_width=True):
                    cands = list(set(data["submissions"].values()))
                    if len(cands) >= 3:
                        data["finalists"] = random.sample(cands, 3)
                        data["final_votes"] = {}
                        save_data(data)
                        st.rerun()
            
            # (4) 초기화
            if st.button(TEXT["btn_reset"], use_container_width=True):
                os.remove(DATA_FILE)
                st.rerun()

# --- 메인 화면 ---

# 타이틀
if data["target_date"]:
    st.title(f"📅 {data['target_date']} 점심 메뉴 선정")
else:
    st.title("🍚 연구실 점심 메뉴 선정")

st.markdown("---")

# 이름 미입력 시 차단
if not username:
    st.warning(TEXT["err_no_name"])
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
    st.write(TEXT["state_collect_desc"])
    
    with st.container():
        # 이미 제출했는지 확인
        if username in data["submissions"]:
            st.success(TEXT["msg_done_suggest"])
            st.info(f"**등록된 메뉴:** {data['submissions'][username]}")
            st.caption("※ 수정이 필요하면 아래에 다시 입력하여 등록하십시오.")
        
        with st.form("suggest_form"):
            menu = st.text_input(TEXT["input_label"])
            submit = st.form_submit_button(TEXT["btn_submit"], use_container_width=True)
            
            if submit:
                if menu.strip():
                    data["submissions"][username] = menu
                    save_data(data)
                    st.rerun()
                else:
                    st.warning("메뉴 이름을 입력해 주십시오.")
    
    st.divider()
    
    # 현재 등록된 후보 리스트
    st.subheader(f"📋 현재 등록된 메뉴 ({len(data['submissions'])})")
    
    cands = list(set(data["submissions"].values()))
    if cands:
        cols = st.columns(3)
        for i, c in enumerate(cands):
            cols[i%3].success(c)
    else:
        st.write("등록된 메뉴가 없습니다.")

# ==========================================
# Phase 2: 투표 (Voting)
# ==========================================
elif data["status"] == "voting":
    st.header(TEXT["state_vote_title"])
    st.write(TEXT["state_vote_desc"])
    
    finalists = data["finalists"]
    
    with st.container():
        st.subheader(f"🗳️ **{username}** 연구원님의 선택")
        
        prev_choice = data["final_votes"].get(username, finalists[0])
        if prev_choice not in finalists:
            prev_choice = finalists[0]
        
        with st.form("vote_form"):
            choice = st.radio("방문 희망 식당 선택", finalists, index=finalists.index(prev_choice))
            submit_vote = st.form_submit_button(TEXT["btn_vote"], type="primary", use_container_width=True)
            
            if submit_vote:
                data["final_votes"][username] = choice
                save_data(data)
                st.rerun()
            
    st.divider()
    
    st.subheader("📊 식당별 방문 인원 현황")
    
    vote_groups = {rest: [] for rest in finalists}
    for user, selected in data["final_votes"].items():
        if selected in vote_groups:
            vote_groups[selected].append(user)
            
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    
    for i, rest in enumerate(finalists):
        with cols[i]:
            st.markdown(f"### {rest}")
            count = len(vote_groups[rest])
            st.markdown(f"**총 {count}명**")
            
            if count > 0:
                members = "\n".join([f"- {u}" for u in vote_groups[rest]])
                st.info(members)
            else:
                st.caption("선택 인원 없음")
