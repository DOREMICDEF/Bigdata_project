
import streamlit as st
import streamlit.components.v1 as components
import json
import os

from analysis import analysis_page


# ---------------------------------
# 기본 설정
# ---------------------------------

st.set_page_config(
    page_title="PLAY FOR ALL",
    page_icon="🎮",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


if "page" not in st.session_state:
    st.session_state.page = "upload"

if "game_data" not in st.session_state:
    st.session_state.game_data = None


# ---------------------------------
# 메인 화면
# ---------------------------------

def upload_page():



    st.title("🎮 PLAY FOR ALL")

    st.subheader("게임이 어려워도 괜찮아요. 내 속도로 함께해요.")

    st.info(
        "게임이 익숙하지 않거나 어렵게 느껴지는 분들도 차근차근 즐길 수 있어요. "
        "연습 문제부터 시작하고, 필요하면 글씨를 키우거나 생각할 시간을 늘려 보세요."
    )
    st.markdown("**이렇게 시작해요**  \n① 게임하러 가기 → ② 연습으로 익히기 → ③ 도형 문제에 도전하기")
    st.caption("처음에는 ‘연습만 하기’를 선택해도 좋아요. 게임을 마친 뒤 기록 파일을 올리면 정답률과 응답 시간을 확인할 수 있어요.")

    st.subheader("내 게임 기록 살펴보기")

    st.write(
        "게임을 완료한 후 다운로드한 JSON 파일을 업로드하세요."
    )

    st.write("데이터 파일이 없으신가요? 그렇다면 게임을 진행해주세요.")

    st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #A8DFA3;
        color: #24452A;
        border: none;
    }

    div.stButton > button[kind="primary"]:hover {
        background-color: #8DCE87;
        color: #24452A;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("🎮 게임하러 가기", type="primary"):

        st.session_state.page = "game"
        st.rerun()

    st.divider()

    # ---------------------------------
    # 게임 기록 업로드
    # ---------------------------------

    st.subheader("📁 게임 기록 업로드")

    st.write("JSON 파일을 선택하세요.")

    uploaded_file = st.file_uploader(
        "JSON 파일을 선택하세요.",
        type=["json"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None:

        try:
            data = json.load(uploaded_file)

            required_keys = [
                "schema_version",
                "stage",
                "participant_id",
                "round_id",
                "profile",
                "initial_level",
                "questions"
            ]

            missing_keys = [
                key for key in required_keys
                if key not in data
            ]

            if missing_keys:

                st.error("필수 데이터가 누락된 파일입니다.")
                st.write("누락된 항목:", missing_keys)

            elif not isinstance(data["questions"], list):

                st.error("문제 기록 데이터의 형식이 올바르지 않습니다.")

            else:

                st.success("JSON 파일을 정상적으로 불러왔습니다!")

                st.divider()

                st.subheader("📋 업로드된 파일 정보")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("진행 단계", data["stage"])

                with col2:
                    st.metric("초기 난이도", data["initial_level"])

                with col3:
                    st.metric("문제 수", len(data["questions"]))

     
                experience = data["profile"].get(
                    "experience",
                    "미설정"
                )

                experience_labels = {
                    "unspecified": "응답하지 않음",
                    "new": "처음이거나 거의 하지 않아요",
                    "sometimes": "가끔 해요",
                    "often": "자주 해요"
                }

                experience_korean = experience_labels.get(
                    experience,
                    experience
                )

                st.write("**파일명:**", uploaded_file.name)

                st.write(
                    "**참여자 ID:**",
                    data["participant_id"]
                )

                st.write(
                    "**게임 경험:**",
                    experience_korean
                )

                with st.expander("JSON 원본 데이터 확인"):
                    st.json(data)

                st.session_state.game_data = data

                st.divider()

                if st.button(
                    "분석 페이지로 이동 →",
                    type="primary"
                ):

                    st.session_state.page = "analysis"
                    st.rerun()

        except json.JSONDecodeError:

            st.error("JSON 파일 형식이 올바르지 않습니다.")

        except Exception as e:

            st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    else:

        st.info("분석할 게임 기록 파일을 업로드해주세요.")


# ---------------------------------
# 게임 화면
# ---------------------------------

def game_page():

    st.title("🎮 PLAY FOR ALL")
    st.subheader("게임 플레이")
    st.info("처음이어도 괜찮아요! 아래에서 ‘연습만 하기’로 시작해 보세요. 글씨 크게 보기와 생각할 시간 1.5배 받기도 선택할 수 있어요.")


    game_path = os.path.join(BASE_DIR, "PLAY_FOR_ALL.html")

    if os.path.exists(game_path):

        with open(game_path, "r", encoding="utf-8") as file:
            html_code = file.read()

        components.html(
            html_code,
            height=850,
            scrolling=True
        )

    else:

        st.error("game.html 파일을 찾을 수 없습니다.")

    st.divider()

    if st.button("← 메인 화면으로 돌아가기"):

        st.session_state.page = "upload"
        st.rerun()


# ---------------------------------
# 페이지 이동
# ---------------------------------

if st.session_state.page == "upload":

    upload_page()

elif st.session_state.page == "analysis":

    if st.session_state.game_data is not None:

        analysis_page(st.session_state.game_data)

    else:

        st.session_state.page = "upload"
        st.rerun()

elif st.session_state.page == "game":

    game_page()
