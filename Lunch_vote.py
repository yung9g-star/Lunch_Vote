import streamlit as st
import pandas as pd
import random
import json
import os
import time
from datetime import datetime

# ==========================================
# [1. 설정 및 소프트 코딩 구역]
# ==========================================

# 기본 설정값
CONFIG = {
    "ADMIN_PASSWORD": "1079",
    "DATA_FILE": "lunch_data.json",
    "PAGE_TITLE": "점심 투표 시스템",
    "PAGE_ICON": "🍚",
}

# 모든 텍스트 메시지 (여기만 수정하면 문구 변경 가능)
TEXT = {
    "sidebar_header": "사용자 접속",
    "sidebar_welcome": "접속자: **{}** 님",
    "sidebar_logout_info": "※ 이름을 변경하려면 아래 버튼을 누르십시오.",
    "sidebar_input_name": "성함",
    "sidebar_placeholder_name": "본인 성함을 입력하세요",
    "sidebar_btn_login": "입장하기",
    "sidebar_btn_logout": "나가기 (데이터 삭제)",
    "sidebar_refresh": "🔄 실시간 현황 새로고침", # 새로고침 버튼 텍스트 추가
    "sidebar_current_users": "현재 참여 인원: {}명",
    "sidebar_no_users": "참여자가 없습니다.",
    
    # 관리자 관련
    "admin_header": "관리자 전용 기능",
    "admin_pw_label": "관리자 비밀번호",
    "admin_success": "관리자 권한 인증됨",
    "admin_session_header": "#### 세션 관리",
    "admin_date_label": "투표 날짜 설정",
    "admin_btn_open": "투표 세션 시작",
    "admin_progress_header": "#### 진행 관리",
    "admin_btn_pick": "추천 마감 및 후보 3곳 추첨",
    "admin_btn_reroll": "후보 재추첨",
    "admin_btn_reset": "데이터 초기화",
    
    # 메인 타이틀
    "title_default": "🍚 연구실 점심 메뉴 선정",
    "title_date": "📅 {} 점심 메뉴 선정",
    
    # 상태 0: 닫힘
    "closed_title": "투표 세션 대기",
    "closed_msg": "현재 활성화된 투표가 없습니다.\n관리자의 세션 시작을 대기해 주십시오.",
    
    # 상태 1: 추천
    "collect_title": "Step 1. 식당 메뉴 추천",
    "collect_desc": "금일 방문을 희망하는 식당 **1곳**을 입력해 주십시오.",
    "collect_success_msg": "추천이 정상적으로 등록되었습니다.",
    "collect_my_pick": "**등록된 메뉴:** {}",
    "collect_modify_info": "※ 수정이 필요하면 아래에 다시 입력하여 등록하십시오.",
    "collect_input_label": "식당 이름 입력",
    "collect_btn_submit": "추천 등록",
    "collect_list_header": "📋 현재 등록된 메뉴 ({})",
    "collect_no_menu": "등록된 메뉴가 없습니다.",
    
    # 상태 2: 투표
    "vote_title": "Step 2. 최종 방문지 선택",
    "vote_desc": "무작위로 선정된 3곳 중, 본인이 방문할 식당을 선택해 주십시오.",
    "vote_user_header": "🗳️ **{}** 연구원님의 선택",
    "vote_label": "방문 희망 식당 선택",
    "vote_btn_submit": "선택 완료",
    "vote_result_header": "📊 식당별 방문 인원 현황",
    "vote_total_count": "총 {}명",
    "vote_no_selection": "선택 인원 없음",
    
    # 에러 및 알림 메시지
    "msg_login_required": "좌측 사이드바에서 성함을 입력 후 '입장하기'를 눌러주십시오.",
    "msg_name_empty": "성함을 입력해 주십시오.",
    "msg_menu_empty": "메뉴 이름을 입력해 주십시오.",
    "msg_min_cand_error": "후보가 최소 3개 이상이어야 추첨이 가능합니다.",
    "toast_open": "투표 세션이 시작되었습니다! 🎉",
    "toast_pick": "후보 3곳이 선정되었습니다! 투표를 시작하세요.",
    "toast_reroll": "후보가 재추첨되었습니다.",
    "toast_reset": "데이터가 초기화되었습니다.",
    "toast_suggest_done": "추천 등록 완료! 👌",
    "toast_vote_done": "투표 완료! 🗳️",
    "toast_refreshed": "최신 현황을 불러왔습니다."
}

# ==========================================
# [2. 스타일 및 유틸리티 함수]
# ==========================================

def inject_smooth_css():
    """부드러운 애니메이션과 깔끔한 UI를 위한 안전한 CSS 주입"""
    st.markdown("""
    <style>
        /* 버튼 호버 시 부드러운 색상 전환 */
        div.stButton > button {
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* 성공 메시지 박스 스타일 */
        div[data-testid="stNotification"] {
            transition: opacity 0.5s ease-in-out;
            border-radius: 8px;
        }
        
        /* Expander 헤더 부드럽게 */
        .streamlit-expanderHeader {
            transition: background-color 0.2s;
        }
        
        /* 라디오 버튼 선택 영역 */
        div[role="radiogroup"] {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    """세션 상태 초기화"""
    # URL 파라미터 확인 (새로고침 방지)
    if "name" in st.query_params:
        st.session_state.locked_name = st.query_params["name"]
    
    if "locked_name" not in st.session_state:
        st.session_state.locked_name = None

# ==========================================
# [3. 데이터 관리 함수]
# ==========================================

def get_default_data():
    return {
        "status": "closed",      # closed, collecting, voting
        "target_date": "",       
        "submissions": {},       # { user: menu }
        "finalists": [],         # [menu1, menu2, menu3]
        "final_votes": {}        # { user: choice }
    }

def load_data():
    if not os.path.exists(CONFIG["DATA_FILE"]):
        return get_default_data()
    try:
        with open(CONFIG["DATA_FILE"], "r", encoding="utf-8") as f:
            data = json.load(f)
            # 호환성 검사
            if "submissions" not in data or "target_date" not in data:
                return get_default_data()
            return data
    except:
        return get_default_data()

def save_data(data):
    try:
        with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

# ==========================================
# [4. UI 컴포넌트 함수]
# ==========================================

def render_sidebar(data):
    """사이드바 영역 렌더링"""
    with st.sidebar:
        st.header(TEXT["sidebar_header"])
        
        # 0. 새로고침 버튼 (항상 노출)
        if st.button(TEXT["sidebar_refresh"], use_container_width=True):
            st.toast(TEXT["toast_refreshed"], icon="🔄")
            st.rerun()

        st.markdown("---")

        # 1. 로그인/로그아웃 로직
        if st.session_state.locked_name:
            st.success(TEXT["sidebar_welcome"].format(st.session_state.locked_name))
            
            if st.button(TEXT["sidebar_btn_logout"], type="secondary", use_container_width=True):
                # 데이터 삭제 로직
                user = st.session_state.locked_name
                if user in data["submissions"]: del data["submissions"][user]
                if user in data["final_votes"]: del data["final_votes"][user]
                save_data(data)
                
                # 세션 초기화
                st.session_state.locked_name = None
                if "name" in st.query_params:
                    del st.query_params["name"]
                st.rerun()
                
            st.caption(TEXT["sidebar_logout_info"])
        else:
            with st.form("login_form"):
                name_val = st.text_input(TEXT["sidebar_input_name"], placeholder=TEXT["sidebar_placeholder_name"])
                if st.form_submit_button(TEXT["sidebar_btn_login"], use_container_width=True):
                    if name_val.strip():
                        st.session_state.locked_name = name_val
                        st.query_params["name"] = name_val
                        st.rerun()
                    else:
                        st.warning(TEXT["msg_name_empty"])

        st.markdown("---")
        
        # 2. 참여 현황
        active_users = list(set(data["submissions"].keys()) | set(data["final_votes"].keys()))
        if active_users:
            st.markdown(TEXT["sidebar_current_users"].format(len(active_users)))
            for user in active_users:
                st.text(f"- {user}")
        else:
            st.caption(TEXT["sidebar_no_users"])

        st.markdown("---")
        
        # 3. 관리자 패널
        render_admin_panel(data)

def render_admin_panel(data):
    """관리자 패널 렌더링"""
    with st.expander(TEXT["admin_header"]):
        pw = st.text_input(TEXT["admin_pw_label"], type="password")
        
        if pw == CONFIG["ADMIN_PASSWORD"]:
            st.success(TEXT["admin_success"])
            
            # (1) 세션 시작
            st.markdown(TEXT["admin_session_header"])
            default_date = datetime.now().date()
            pick_date = st.date_input(TEXT["admin_date_label"], value=default_date)
            
            if st.button(TEXT["admin_btn_open"], use_container_width=True):
                new_data = get_default_data()
                new_data["status"] = "collecting"
                new_data["target_date"] = pick_date.strftime("%Y-%m-%d")
                save_data(new_data)
                st.toast(TEXT["toast_open"], icon="🎉")
                time.sleep(0.5)
                st.rerun()
            
            st.markdown("---")
            st.markdown(TEXT["admin_progress_header"])

            # (2) 추첨
            if data["status"] == "collecting":
                if st.button(TEXT["admin_btn_pick"], type="primary", use_container_width=True):
                    cands = list(set(data["submissions"].values()))
                    if len(cands) < 3:
                        st.error(TEXT["msg_min_cand_error"])
                    else:
                        data["finalists"] = random.sample(cands, 3)
                        data["status"] = "voting"
                        save_data(data)
                        st.toast(TEXT["toast_pick"], icon="🎲")
                        time.sleep(0.5)
                        st.rerun()
            
            # (3) 재추첨
            if data["status"] == "voting":
                if st.button(TEXT["admin_btn_reroll"], type="primary", use_container_width=True):
                    cands = list(set(data["submissions"].values()))
                    if len(cands) >= 3:
                        data["finalists"] = random.sample(cands, 3)
                        data["final_votes"] = {}
                        save_data(data)
                        st.toast(TEXT["toast_reroll"], icon="🔄")
                        st.rerun()
            
            # (4) 초기화
            if st.button(TEXT["admin_btn_reset"], use_container_width=True):
                if os.path.exists(CONFIG["DATA_FILE"]):
                    os.remove(CONFIG["DATA_FILE"])
                st.toast(TEXT["toast_reset"], icon="🗑️")
                time.sleep(0.5)
                st.rerun()

# ==========================================
# [5. 메인 앱 실행]
# ==========================================

def main():
    st.set_page_config(page_title=CONFIG["PAGE_TITLE"], page_icon=CONFIG["PAGE_ICON"], layout="centered")
    inject_smooth_css()
    init_session_state()
    
    data = load_data()
    username = st.session_state.locked_name

    # 사이드바 렌더링
    render_sidebar(data)

    # 타이틀
    if data["target_date"]:
        st.title(TEXT["title_date"].format(data["target_date"]))
    else:
        st.title(TEXT["title_default"])
    st.markdown("---")

    # 로그인 체크
    if not username:
        st.warning(TEXT["msg_login_required"])
        st.stop()

    # --- Phase Logic ---
    
    # 0. 닫힘 상태
    if data["status"] == "closed":
        st.info(TEXT["closed_title"])
        st.write(TEXT["closed_msg"])

    # 1. 추천 상태 (Collecting)
    elif data["status"] == "collecting":
        st.header(TEXT["collect_title"])
        st.write(TEXT["collect_desc"])
        
        # 입력 폼
        with st.container():
            if username in data["submissions"]:
                st.success(TEXT["collect_success_msg"])
                st.info(TEXT["collect_my_pick"].format(data['submissions'][username]))
                st.caption(TEXT["collect_modify_info"])
            
            with st.form("suggest_form"):
                menu = st.text_input(TEXT["collect_input_label"])
                if st.form_submit_button(TEXT["collect_btn_submit"], use_container_width=True):
                    if menu.strip():
                        data["submissions"][username] = menu
                        save_data(data)
                        st.toast(TEXT["toast_suggest_done"], icon="👌")
                        st.rerun()
                    else:
                        st.warning(TEXT["msg_menu_empty"])
        
        st.divider()
        st.subheader(TEXT["collect_list_header"].format(len(data["submissions"])))
        
        cands = list(set(data["submissions"].values()))
        if cands:
            cols = st.columns(3)
            for i, c in enumerate(cands):
                cols[i%3].success(c)
        else:
            st.write(TEXT["collect_no_menu"])

    # 2. 투표 상태 (Voting)
    elif data["status"] == "voting":
        st.header(TEXT["vote_title"])
        st.write(TEXT["vote_desc"])
        
        finalists = data["finalists"]
        
        # 투표 폼
        with st.container():
            st.subheader(TEXT["vote_user_header"].format(username))
            
            prev_choice = data["final_votes"].get(username, finalists[0])
            if prev_choice not in finalists:
                prev_choice = finalists[0]
            
            with st.form("vote_form"):
                choice = st.radio(TEXT["vote_label"], finalists, index=finalists.index(prev_choice))
                if st.form_submit_button(TEXT["vote_btn_submit"], type="primary", use_container_width=True):
                    data["final_votes"][username] = choice
                    save_data(data)
                    st.toast(TEXT["toast_vote_done"], icon="🗳️")
                    st.balloons()
                    st.rerun()
        
        st.divider()
        
        # 결과 현황 (박스형)
        st.subheader(TEXT["vote_result_header"])
        
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
                st.markdown(TEXT["vote_total_count"].format(count))
                
                if count > 0:
                    members = "\n".join([f"- {u}" for u in vote_groups[rest]])
                    st.info(members)
                else:
                    st.caption(TEXT["vote_no_selection"])

if __name__ == "__main__":
    main()
