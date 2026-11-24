
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


if "menu" not in st.session_state:
    st.session_state.menu = "홈"

if "game_data" not in st.session_state:
    st.session_state.game_data = None


# ---------------------------------
# 사이드바 메뉴
# ---------------------------------

st.markdown("""
<style>

/* 사이드바 위쪽 여백 줄이기 */
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 0px !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding: 0px 16px !important;
}

/* 로고를 왼쪽 위로 이동 */
section[data-testid="stSidebar"] .sidebar-logo {
    font-size: 20px !important;
    font-weight: bold !important;
    white-space: nowrap;
    margin-top: -35px !important;
    margin-bottom: 15px !important;
    padding: 0px !important;
    text-align: left !important;
}

/* 메뉴 버튼 기본 모양 제거 */
section[data-testid="stSidebar"] [data-testid="stButton"] {
    margin-top: 0px !important;
    margin-bottom: 2px !important;
}

section[data-testid="stSidebar"] [data-testid="stButton"] button {
    width: 100% !important;
    height: 38px !important;
    min-height: 38px !important;

    border: none !important;
    outline: none !important;
    box-shadow: none !important;

    padding: 5px 10px !important;
    border-radius: 7px !important;

    justify-content: flex-start !important;
    text-align: left !important;
}

/* 버튼 내부 글자 왼쪽 정렬 */
section[data-testid="stSidebar"] [data-testid="stButton"] button > div {
    width: 100% !important;
    justify-content: flex-start !important;
}

section[data-testid="stSidebar"] [data-testid="stButton"] button p {
    width: 100% !important;
    text-align: left !important;
    margin: 0 !important;
}

/* 선택되지 않은 메뉴 */
section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {
    background: transparent !important;
    color: #333333 !important;
}

/* 선택된 메뉴 */
section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
    background: #E8DDF5 !important;
    color: #573477 !important;
}

/* 마우스를 올렸을 때 */
section[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"]:hover {
    background: #F2EDF8 !important;
}

</style>
""", unsafe_allow_html=True)


# 로고
st.sidebar.markdown(
    """
    <div class="sidebar-logo">
        🎮 PLAY FOR ALL
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.divider()


# 메뉴 버튼
if st.sidebar.button(
    "🏠  홈",
    type="primary" if st.session_state.menu == "홈" else "secondary",
    use_container_width=True
):
    st.session_state.menu = "홈"
    st.rerun()


if st.sidebar.button(
    "🎮  게임하기",
    type="primary" if st.session_state.menu == "게임하기" else "secondary",
    use_container_width=True
):
    st.session_state.menu = "게임하기"
    st.rerun()


if st.sidebar.button(
    "📊  기록 분석",
    type="primary" if st.session_state.menu == "기록 분석" else "secondary",
    use_container_width=True
):
    st.session_state.menu = "기록 분석"
    st.rerun()


menu = st.session_state.menu


# ---------------------------------
# 홈 화면
# ---------------------------------

def home_page():

    st.title("🎮 PLAY FOR ALL")

    st.subheader("게임이 어려워도 괜찮아요. 내 속도로 함께해요.")

    st.info(
        "게임이 익숙하지 않거나 어렵게 느껴지는 분들도 차근차근 즐길 수 있어요. "
        "연습 문제부터 시작하고, 필요하면 글씨를 키우거나 생각할 시간을 늘려 보세요."
    )
    st.markdown("**이렇게 시작해요**  \n① 게임하러 가기 → ② 연습으로 익히기 → ③ 도형 문제에 도전하기")
    st.caption("처음에는 ‘연습만 하기’를 선택해도 좋아요. 게임을 마친 뒤 기록 파일을 올리면 정답률과 응답 시간을 확인할 수 있어요.")

    st.divider()

    # ---------------------------------
    # 바로가기 버튼 스타일
    # ---------------------------------

    st.markdown("""
    <style>

    /* 홈 화면 바로가기 버튼 */
    div.stButton > button[kind="primary"] {
        background-color: #A8DFA3 !important;
        color: #24452A !important;
        border: 1px solid #A8DFA3 !important;
    }

    /* 마우스를 올렸을 때 */
    div.stButton > button[kind="primary"]:hover {
        background-color: #8DCE87 !important;
        color: #24452A !important;
        border: 1px solid #8DCE87 !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # ---------------------------------
    # 바로가기
    # ---------------------------------

    st.subheader("무엇을 해볼까요?")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎮 게임 바로가기")
        st.write("직접 게임을 진행하고 나에게 맞는 방식으로 문제를 풀어보세요.")

        if st.button(
            "게임하러 가기 →",
            type="primary",
            use_container_width=True,
            key="home_game_button"
        ):
            st.session_state.menu = "게임하기"
            st.rerun()

    with col2:
        st.markdown("### 📊 게임 기록 분석")
        st.write("게임을 완료한 후 기록 파일을 업로드하고 나의 결과를 확인해보세요.")

        if st.button(
            "기록 분석하기 →",
            type="primary",
            use_container_width=True,
            key="home_analysis_button"
        ):
            st.session_state.menu = "기록 분석"
            st.rerun()

    st.divider()

    # ---------------------------------
    # 프로젝트 소개
    # ---------------------------------

    st.markdown("""
    ### 💡 프로젝트 소개

    사람마다 게임을 이해하고 문제를 해결하는 속도는 다릅니다.

    PLAY FOR ALL은 이러한 차이를 고려하여 사용자가 자신의 수준에 맞게
    게임을 진행할 수 있도록 지원합니다.

    - **쉬운 게임 환경**: 연습 문제를 통해 게임에 익숙해질 수 있습니다.
    - **사용자 맞춤 설정**: 글씨 크기와 생각할 시간을 조절할 수 있습니다.
    - **게임 기록 분석**: 정답률과 응답 시간 등을 확인할 수 있습니다.
    - **개인별 게임 경험**: 자신의 속도에 맞춰 게임을 즐길 수 있습니다.
    """)


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

        st.error("PLAY_FOR_ALL.html 파일을 찾을 수 없습니다.")


# ---------------------------------
# 기록 분석 화면
# ---------------------------------

def record_page():

    st.title("📊 게임 기록 분석")

    st.subheader("나의 게임 기록 살펴보기")

    st.write(
        "게임을 완료한 후 다운로드한 JSON 파일을 업로드하세요."
    )

    st.info("아직 게임 기록 파일이 없다면 먼저 게임을 진행해주세요.")

    st.divider()

    # ---------------------------------
    # JSON 파일 업로드
    # ---------------------------------

    st.subheader("📁 게임 기록 업로드")

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
                st.session_state.game_data = None

            elif not isinstance(data["questions"], list):

                st.error("문제 기록 데이터의 형식이 올바르지 않습니다.")
                st.session_state.game_data = None

            else:

                st.success("JSON 파일을 정상적으로 불러왔습니다!")

                st.session_state.game_data = data

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

        except json.JSONDecodeError:

            st.error("JSON 파일 형식이 올바르지 않습니다.")
            st.session_state.game_data = None

        except Exception as e:

            st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
            st.session_state.game_data = None

    # ---------------------------------
    # 게임 기록 분석 결과
    # ---------------------------------

    st.divider()

    st.subheader("📈 분석 결과")

    if st.session_state.game_data is not None:

        analysis_page(st.session_state.game_data)

    else:

        st.info("게임 기록을 업로드하면 이곳에 분석 결과가 표시됩니다.")


# ---------------------------------
# 페이지 이동
# ---------------------------------

if menu == "홈":

    home_page()

elif menu == "게임하기":

    game_page()

elif menu == "기록 분석":

    record_page()
