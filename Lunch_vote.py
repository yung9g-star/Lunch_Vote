import streamlit as st
import pandas as pd
import random
import json
import os
from datetime import datetime

# --- 설정 및 파일 경로 ---
DATA_FILE = "lunch_data.json"

# --- 데이터 관리 함수 (JSON 파일 사용) ---
def init_default_data():
    """기본 데이터 구조를 반환하고 파일로 저장합니다."""
    default_data = {
        "step": 0,  # 0: 후보 등록/투표 단계, 1: 최종 3곳 투표 단계
        "candidates": ["학식(교직원)", "김밥천국", "중국집", "피자", "편의점"], # 기본 후보
        "finalists": [], # 3개 선정된 리스트
        "final_votes": {} # {사용자명: 선택한식당}
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(default_data, f, ensure_ascii=False, indent=4)
    return default_data

def load_data():
    """데이터 파일을 불러오거나, 파일이 없거나 깨졌으면 새로 만듭니다."""
    if not os.path.exists(DATA_FILE):
        return init_default_data()
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # 파일이 깨졌을 경우 초기화
        return init_default_data()

def save_data(data):
    """변경된 데이터를 파일에 저장합니다."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"데이터 저장 중 오류가 발생했습니다: {e}")

# --- 앱 시작 ---
st.set_page_config(page_title="연구실 점심 투표", page_icon="🍚", layout="centered")

st.title("🍚 연구실 점심 메뉴 선정 🥢")
st.markdown("---")

# 데이터 로드
data = load_data()

# --- 사이드바: 내 정보 및 관리/배포 기능 ---
with st.sidebar:
    st.header("👤 내 정보")
    username = st.text_input("닉네임을 입력하세요", key="username_input")
    
    st.divider()
    
    st.header("⚙️ 관리 기능")
    if st.button("🗑️ 투표 완전 초기화 (내일 쓸 때)"):
        # 파일을 삭제하고 리로드하여 초기화
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            st.rerun()
            
    st.divider()
    
    # [배포 도우미] 영구 사용을 위한 안내
    with st.expander("☁️ 평생 무료로 배포하려면?"):
        st.markdown("""
        **Streamlit Community Cloud**를 이용하면 이 앱을 24시간 무료로 켜둘 수 있습니다.
        
        1. GitHub에 `app.py`와 `requirements.txt`를 올립니다.
        2. Streamlit Cloud에 가입 후 리포지토리를 연결합니다.
        3. 아래 버튼을 눌러 설정 파일을 다운로드하세요.
        """)
        
        # requirements.txt 내용
        reqs = "streamlit\npandas"
        
        # 다운로드 버튼 추가
        st.download_button(
            label="📄 requirements.txt 다운로드",
            data=reqs,
            file_name="requirements.txt",
            mime="text/plain",
            help="이 파일을 app.py와 같은 폴더에 저장하거나 GitHub에 올리세요."
        )

if not username:
    st.warning("👈 왼쪽 사이드바에서 먼저 **닉네임**을 입력해주세요!")
    st.info("닉네임을 입력해야 투표에 참여할 수 있습니다.")
    st.stop()

st.success(f"환영합니다, **{username}**님! 맛있는 점심을 골라보세요.")

# --- 단계별 로직 ---

# [단계 0] 후보 등록 및 확인
if data["step"] == 0:
    st.header("Step 1. 후보 등록 및 확인")
    st.markdown("오늘 가고 싶은 식당 리스트입니다. 없는 곳이 있다면 추가해주세요!")

    # 현재 후보 리스트 보여주기 (보기 좋게 칩 형태로 표시)
    st.markdown("### 📋 현재 후보 리스트")
    
    # 후보 리스트를 3열로 나누어 보여주기 (시각적 개선)
    cols = st.columns(3)
    for i, cand in enumerate(data["candidates"]):
        cols[i % 3].success(cand)

    st.markdown("") # 여백

    # 후보 추가하기
    with st.form("add_candidate_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_candidate = st.text_input("새로운 식당/메뉴 추가", placeholder="예: 학교 앞 떡볶이")
        with col2:
            submitted = st.form_submit_button("목록에 추가")
            
        if submitted:
            if new_candidate and new_candidate not in data["candidates"]:
                data["candidates"].append(new_candidate)
                save_data(data)
                st.toast(f"✅ '{new_candidate}' 추가 완료!")
                st.rerun()
            elif new_candidate in data["candidates"]:
                st.warning("⚠️ 이미 목록에 있습니다.")
            else:
                st.warning("⚠️ 식당 이름을 입력해주세요.")

    st.divider()
    
    # 3개 뽑기 버튼
    st.markdown("### 🎲 운명의 시간")
    st.write("후보가 충분히 모였으면 아래 버튼을 눌러 3곳을 무작위로 뽑습니다.")
    
    if st.button("🚀 랜덤으로 3곳 선정하기! (Step 2로 이동)", type="primary"):
        if len(data["candidates"]) < 3:
            st.error("❌ 후보가 3개 이상이어야 추첨할 수 있습니다!")
        else:
            data["finalists"] = random.sample(data["candidates"], 3)
            data["step"] = 1 # 단계 변경
            save_data(data)
            st.rerun()

# [단계 1] 최종 3곳 중 선택 및 인원 배분
elif data["step"] == 1:
    st.header("Step 2. 최종 선택 & 인원 배분")
    st.markdown("##### 오늘의 결선 진출 식당 3곳 🎉")
    st.info("가장 가고 싶은 곳을 선택하고 '결정' 버튼을 눌러주세요!")
    
    finalists = data["finalists"]
    
    # 투표 UI
    # 현재 나의 선택 상태 확인
    current_selection = data["final_votes"].get(username, None)
    index = 0
    if current_selection in finalists:
        index = finalists.index(current_selection)

    with st.form("vote_form"):
        vote = st.radio("어디로 갈까요?", finalists, index=index)
        submitted = st.form_submit_button("이곳으로 결정! 🗳️")
        
        if submitted:
            data["final_votes"][username] = vote
            save_data(data)
            st.toast(f"✅ {vote} 선택 완료!")
            st.rerun()

    st.divider()
    
    # 결과 보여주기
    st.subheader("📊 실시간 배분 현황")
    
    if data["final_votes"]:
        # 데이터프레임 변환
        df = pd.DataFrame(list(data["final_votes"].items()), columns=["닉네임", "선택한 식당"])
        
        # 식당별 인원 수 계산
        summary = df["선택한 식당"].value_counts().reset_index()
        summary.columns = ["식당", "인원(명)"]
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**📝 멤버별 선택**")
            st.dataframe(df, use_container_width=True, hide_index=True)
        with c2:
            st.markdown("**🔢 식당별 집계**")
            st.dataframe(summary, use_container_width=True, hide_index=True)
            
            # 간단한 막대 그래프
            st.bar_chart(data=summary.set_index("식당"))
            
    else:
        st.info("아직 투표한 사람이 없습니다. 1등으로 투표해보세요!")

    st.markdown("---")
    # 다시 1단계로 돌아가기
    if st.button("🔄 다시 추첨하기 (Step 1로 돌아가기)"):
        data["step"] = 0
        data["final_votes"] = {}
        data["finalists"] = []
        save_data(data)
        st.rerun()