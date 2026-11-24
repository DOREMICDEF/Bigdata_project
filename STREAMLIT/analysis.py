
import streamlit as st
import statistics
import plotly.express as px


# ==================================
# 분석 페이지
# ==================================

def analysis_page(data):

    st.title("🎮 PLAY FOR ALL")
    st.subheader("게임 기록 분석")

    st.divider()

    questions = data["questions"]

    if len(questions) == 0:

        st.warning("분석할 문제 기록이 없습니다.")

    else:

        # --------------------------------
        # 1. 정답 및 오답 계산
        # --------------------------------

        correct_count = sum(
            1 for q in questions
            if q.get("correct") is True
        )

        wrong_count = len(questions) - correct_count

        accuracy = correct_count / len(questions) * 100

        # --------------------------------
        # 2. 응답 시간 계산
        # --------------------------------

        response_times = [
            q["response_ms"] / 1000
            for q in questions
            if isinstance(q.get("response_ms"), (int, float))
            and q["response_ms"] >= 0
        ]

        if response_times:

            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)

        else:

            avg_time = 0
            median_time = 0

        # --------------------------------
        # 3. 힌트 및 시간 초과 계산
        # --------------------------------

        hint_count = sum(
            1 for q in questions
            if q.get("hint_used") is True
        )

        timeout_count = sum(
            1 for q in questions
            if q.get("outcome") == "timeout"
        )

        # --------------------------------
        # 4. 주요 분석 결과
        # --------------------------------

        st.subheader("📌 주요 분석 결과")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "정답률",
                f"{accuracy:.1f}%"
            )

        with col2:
            st.metric(
                "평균 응답 시간",
                f"{avg_time:.2f}초"
            )

        with col3:
            st.metric(
                "중앙값 응답 시간",
                f"{median_time:.2f}초"
            )

        col4, col5, col6 = st.columns(3)

        with col4:
            st.metric(
                "정답 수",
                f"{correct_count}개"
            )

        with col5:
            st.metric(
                "오답 수",
                f"{wrong_count}개"
            )

        with col6:
            st.metric(
                "힌트 사용",
                f"{hint_count}회"
            )

        st.metric(
            "시간 초과 횟수",
            f"{timeout_count}회"
        )

        

        # --------------------------------
        # 5. 그래프와 상세 기록을 한 줄에 배치
        # --------------------------------

        st.divider()

        col1, col2 = st.columns([1, 1])

        # 왼쪽: 선그래프
        with col1:

            st.subheader("⏱️ 응답 시간 변화")

            chart_data = []

            for q in questions:

                response = q.get("response_ms")

                if isinstance(response, (int, float)) and response >= 0:

                    chart_data.append({
                        "문제": f"{q.get('question_index', '-') }번",
                        "응답 시간(초)": response / 1000
                    })

            if chart_data:

                # 선그래프 생성
                fig = px.line(
                    chart_data,
                    x="문제",
                    y="응답 시간(초)",
                    markers=True,
                    text="응답 시간(초)",
                    title="문제별 응답 시간 변화"
                )

                # 점 위에 응답 시간 표시
                fig.update_traces(
                    mode="lines+markers+text",
                    texttemplate="%{text:.2f}초",
                    textposition="top center",
                    cliponaxis=False
                )

                # 그래프 여백 및 크기 설정
                max_time = max(
                    item["응답 시간(초)"]
                    for item in chart_data
                )

                fig.update_layout(
                    xaxis_title="문제",
                    yaxis_title="응답 시간(초)",
                    showlegend=False,
                    height=400,
                    margin=dict(
                        l=70,
                        r=40,
                        t=100,
                        b=70
                    )
                )

                # X축과 Y축 글씨 잘림 방지
                fig.update_xaxes(
                    tickangle=0,
                    automargin=True
                )

                fig.update_yaxes(
                    range=[0, max_time * 1.25],
                    automargin=True
                )

                # 그래프 출력
                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info("응답 시간 데이터가 없습니다.")

        # 오른쪽: 문제별 상세 기록
        with col2:

            st.subheader("📝 문제별 상세 기록")

            result_table = []

            for q in questions:

                if q.get("correct") is True:

                    result = "정답"

                elif q.get("outcome") == "timeout":

                    result = "시간 초과"

                else:

                    result = "오답"

                response = q.get("response_ms")

                if isinstance(response, (int, float)):

                    response = f"{response / 1000:.2f}초"

                else:

                    response = "기록 없음"

                result_table.append({

                    "문제 번호": q.get("question_index", "-"),

                    "난이도": q.get("level", "-"),

                    "결과": result,

                    "응답 시간": response,

                    "힌트": "사용" if q.get("hint_used") is True else "미사용"

                })

            # 데이터 개수에 따라 표 높이 자동 조절
            table_height = (len(result_table) + 1) * 35

            st.dataframe(
                result_table,
                use_container_width=True,
                hide_index=True,
                height=table_height
            )


        # --------------------------------
        # 7. JSON 원본 확인
        # --------------------------------

        st.divider()

        with st.expander("JSON 원본 데이터 확인"):

            st.json(data)

    # --------------------------------
    # 8. 업로드 페이지로 돌아가기
    # --------------------------------

    
