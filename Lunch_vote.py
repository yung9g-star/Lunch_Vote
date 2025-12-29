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
    "sidebar_title": "현재 참여자",
    
    # 상태별 메시지
    "state_closed_title": "⛔ 투표 대기 중",
    "state_closed_msg": "관리자가 투표를 시작할 때까지 잠시만 기다려주세요.",
    
    "state_collect_title": "Step 1. 메뉴 추천하기",
    "state_collect_desc": "오늘 먹고 싶은 식당을 **하나만** 추천해주세요.",
    "input_label": "추천할 식당 이름",
    "btn_submit": "이 메뉴로 추천하기",
    
    "state_vote_title": "Step 2. 최종 선택하기",
    "state_vote_desc": "선정된 3곳 중 가장 가고 싶은 곳을 선택하세요.",
    "btn_vote": "최종 선택 제출",
    
    # 관리자
    "admin_header": "관리자 기능 (Admin)",
    "btn_open": "▶ 투표 시작 (Session Open)",
    "btn_pick": "🎲 3곳 추첨 (Pick 3)",
    "btn_reroll": "🔄 다시 뽑기 (Re-roll)",
    "btn_reset": "🗑 데이터 초기화 (Reset)",
    
    # 알림
    "msg_done_suggest": "추천 완료! 다른 분들을 기다려주세요.",
    "msg_done_vote": "투표 완료! 결과를 확인하세요.",
    "err_no_name": "왼쪽 사이드바에서 닉네임을 먼저 입력해주세요.",
    "err_min_cand": "후보가 3개 이상이어야 합니다."
}

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
            # 데이터 구조 호환성 체크
            if "submissions" not in data or "status" not in data:
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

# 레이아웃 설정 (기본)
st.set_page_config(page_title="점심 투표", page_icon="🍚", layout="centered")

# 데이터 로드
data = load_data()

# --- 사이드바 ---
with st.sidebar:
    st.header(TEXT["sidebar_title"])
    
    # 닉네임 입력
    username = st.text_input("닉네임 (이름)", key="user_name")
    
    st.markdown("---")
    
    # 참여자 목록 표시
    active_users = list(set(data["submissions"].keys()) | set(data["final_votes"].keys()))
    
    if active_users:
        st.success(f"현재 {len(active_users)}명 참여 중")
        # 깔끔한 목록 표시
        for user in active_users:
            st.text(f"👤 {user}")
    else:
        st.info("아직 참여자가 없습니다.")

    st.markdown("---")
    
    # 관리자 패널
    with st.expander(TEXT["admin_header"]):
        pw = st.text_input("비밀번호", type="password")
        if pw == ADMIN_PASSWORD:
            st.success("관리자 권한 확인됨")
            
            # 관리자 버튼들
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
            st.error("비밀번호가 틀렸습니다.")

# --- 메인 화면 ---

st.title(TEXT["app_title"])
st.caption(TEXT["app_subtitle"])
st.markdown("---")

# 닉네임 체크
if not username:
    st.warning(TEXT["err_no_name"])
    st.stop()

# 상태 0: 닫힘
if data["status"] == "closed":
    st.info(TEXT["state_closed_title"])
    st.write(TEXT["state_closed_msg"])

# 상태 1: 메뉴 모집
elif data["status"] == "collecting":
    st.header(TEXT["state_collect_title"])
    st.write(TEXT["state_collect_desc"])
    
    # 입력 폼
    with st.container():
        if username in data["submissions"]:
            st.success(f"✅ {TEXT['msg_done_suggest']}")
            st.info(f"**내가 추천한 메뉴:** {data['submissions'][username]}")
        else:
            with st.form("suggest_form"):
                menu = st.text_input(TEXT["input_label"])
                submit = st.form_submit_button(TEXT["btn_submit"], use_container_width=True)
                
                if submit:
                    if menu.strip():
                        data["submissions"][username] = menu
                        save_data(data)
                        st.rerun()
                    else:
                        st.warning("메뉴 이름을 입력해주세요.")
    
    st.divider()
    
    # 후보 리스트 보여주기 (기본 컴포넌트 사용)
    st.subheader(f"📋 현재 추천된 메뉴 ({len(data['submissions'])})")
    
    cands = list(set(data["submissions"].values()))
    if cands:
        cols = st.columns(3)
        for i, c in enumerate(cands):
            # 가장 안정적인 st.success 박스로 표시
            cols[i%3].success(c)
    else:
        st.write("아직 등록된 메뉴가 없습니다.")

# 상태 2: 투표
elif data["status"] == "voting":
    st.header(TEXT["state_vote_title"])
    st.write(TEXT["state_vote_desc"])
    
    finalists = data["finalists"]
    
    # 후보 3개 강조 (Metrics)
    col1, col2, col3 = st.columns(3)
    col1.metric("1번 후보", finalists[0])
    col2.metric("2번 후보", finalists[1])
    col3.metric("3번 후보", finalists[2])
    
    st.divider()
    
    # 투표 폼
    st.subheader(f"🗳️ {username}님의 선택")
    
    # 이전 선택값 불러오기
    prev_choice = data["final_votes"].get(username, finalists[0])
    if prev_choice not in finalists:
        prev_choice = finalists[0]
    
    with st.form("vote_form"):
        choice = st.radio("하나를 선택해주세요", finalists, index=finalists.index(prev_choice))
        submit_vote = st.form_submit_button(TEXT["btn_vote"], type="primary", use_container_width=True)
        
        if submit_vote:
            data["final_votes"][username] = choice
            save_data(data)
            st.rerun()
            
    # 결과 그래프
    if data["final_votes"]:
        st.divider()
        st.subheader("📊 실시간 득표 현황")
        
        df = pd.DataFrame(list(data["final_votes"].items()), columns=["닉네임", "선택"])
        counts = df["선택"].value_counts()
        
        st.bar_chart(counts)
        
        with st.expander("상세 투표 내역 보기"):
            st.dataframe(df, use_container_width=True, hide_index=True)
