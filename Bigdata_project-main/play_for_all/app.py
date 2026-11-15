"""Run: python -m streamlit run app.py"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core import LEVEL_NAMES, recommend, validate_record

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="PLAY FOR ALL | 플레이와 분석", page_icon="🌿", layout="wide")
game_component = components.declare_component("play_for_all", path=str(ROOT / "frontend"))
st.title("PLAY FOR ALL")
st.caption("나에게 맞는 작은 도전 · Stage 1 시연과 설명 가능한 난이도 추천")
st.session_state.setdefault("records", {})
st.session_state.setdefault("game_key", 0)
st.session_state.setdefault("upload_key", 0)


def accept(raw):
    validated = validate_record(raw)
    records = st.session_state.records
    key = validated["round_id"]
    if key in records and records[key] != validated:
        raise ValueError("같은 round_id에 다른 내용이 있습니다. 기존 기록은 유지했습니다.")
    records[key] = validated
    return key


with st.sidebar:
    st.subheader("시연 안내")
    st.write("게임을 마치면 기록 분석 탭에 결과가 자동으로 연결됩니다.")
    st.info("현재 추천은 규칙 기반 시제품입니다. 학습된 AI나 효과가 검증된 복지서비스가 아닙니다.")
    st.caption("기록은 서버의 현재 세션 메모리에만 둡니다. 새로고침 전에 필요한 파일을 내려받으세요. 서버를 종료하면 메모리 기록이 사라집니다.")
    if st.button("현재 세션 기록 지우고 초기화"):
        st.session_state.records = {}
        st.session_state.game_key += 1
        st.session_state.upload_key += 1
        st.rerun()

play_tab, analysis_tab, data_tab = st.tabs(["01  게임 시작", "02  기록 분석", "03  데이터와 설계"])
with play_tab:
    raw = game_component(key=f"game_{st.session_state.game_key}", default=None)
    if raw is not None:
        try:
            accept(raw)
            st.success("1라운드 기록이 연결되었습니다. ‘02 기록 분석’ 탭에서 결과를 확인하세요.")
        except (ValueError, TypeError) as exc:
            st.error(f"기록을 읽을 수 없습니다: {exc}")

with analysis_tab:
    st.subheader("플레이를 이해하는 기록")
    st.caption("단독 HTML 게임에서 내려받은 JSON도 불러올 수 있습니다. 동일한 라운드는 중복 집계하지 않습니다.")
    files = st.file_uploader("게임 기록 JSON 불러오기", type="json", accept_multiple_files=True,
                             key=f"uploads_{st.session_state.upload_key}")
    for file in files:
        try:
            if file.size > 2_000_000:
                raise ValueError("파일은 2MB 이하여야 합니다.")
            accept(json.loads(file.getvalue().decode("utf-8-sig")))
        except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
            st.error(f"{file.name}: {exc}")
    records = st.session_state.records
    if not records:
        st.info("아직 완료된 기록이 없습니다. 게임을 한 번 완료하거나 기록 파일을 올려 주세요.")
    else:
        selected = st.selectbox("분석할 라운드", list(records), index=len(records)-1,
                                format_func=lambda rid: f"{records[rid]['completed_at']} · 재도전 {records[rid]['retry_count']}회 · {rid[-8:]}")
        record = records[selected]
        result = recommend(record)
        metrics = result["metrics"]
        cols = st.columns(4)
        cols[0].metric("정답률", f"{metrics['accuracy']:.0%}", f"{metrics['correct_count']} / 6 문항", delta_color="off")
        cols[1].metric("중앙 응답 시간", f"{metrics['median_seconds']:.1f}초")
        cols[2].metric("힌트 사용", f"{metrics['hint_count']}회")
        cols[3].metric("시간 초과 / 건너뜀", f"{metrics['timeout_count']} / {metrics['skip_count']}")
        st.write("라운드 목표 달성" if metrics["stage_success"] else "라운드 목표 미달성", "· 6문항 중 4개 이상 정답 기준")
        st.subheader("다음 활동 추천")
        st.write(f"**{LEVEL_NAMES[result['initial_level']]} → {LEVEL_NAMES[result['next_level']]}**")
        st.write(result["reason"])
        st.caption(f"다음 문항 제한 시간 제안: {result['next_seconds']:g}초 · 시간 지원 설정 유지 · rule_baseline_v1")
        st.warning("이 값은 다음 활동을 위한 추천입니다. 2라운드 실행과 추천 효과 검증은 아직 구현 범위에 포함하지 않았습니다.")
        rows = pd.DataFrame(record["questions"])
        chart = pd.DataFrame({"문항": rows.question_index.astype(str), "실제 응답 시간(초)": rows.response_ms/1000,
                              "제한 시간(초)": rows.limit_ms/1000}).set_index("문항")
        st.bar_chart(chart, horizontal=False)
        st.caption("응답 시간은 일시정지 시간을 제외합니다. 시간 초과는 제한 시간으로 기록하며 오답·건너뛰기도 중앙값에 포함합니다.")
        table = rows[["question_index", "correct", "outcome", "response_ms", "hint_used", "limit_ms"]].rename(columns={
            "question_index":"문항", "correct":"정답 여부", "outcome":"응답 유형", "response_ms":"응답 시간 ms", "hint_used":"힌트 사용", "limit_ms":"제한 시간 ms"})
        st.dataframe(table, hide_index=True, width="stretch")
        c1, c2 = st.columns(2)
        c1.download_button("이 라운드 JSON", json.dumps(record, ensure_ascii=False, indent=2),
                           file_name=f"play_for_all_{selected}.json", mime="application/json")
        c2.download_button("문항별 CSV", table.to_csv(index=False).encode("utf-8-sig"),
                           file_name="play_for_all_questions.csv", mime="text/csv")
        with st.expander("추천 규칙과 해석의 한계"):
            st.write("① 정답 3개 미만 또는 시간 초과 2회 이상: 한 단계 하향. ② 그 외 정답 5개 이상, 중앙 응답 시간/제한 시간 60% 이하, 힌트 1회 이하: 한 단계 상향. ③ 나머지: 유지. 난이도는 1~3 범위로 제한합니다.")
            st.write("시간 지원·큰 글씨 사용 자체에는 감점이 없습니다. 시간 비율은 지원 적용 후 제한 시간을 기준으로 계산합니다. 연령·장애 여부는 규칙에 사용하지 않습니다. 여섯 문항 결과는 인지능력 또는 장애 정도에 대한 진단이 아닙니다.")
        st.caption(f"현재 세션: {len(records)}개 라운드 · {len({r['participant_id'] for r in records.values()})}개 참여자 ID. 같은 사람이 다른 브라우저로 시작하면 다른 ID가 되므로 실제 고유 인원과 다를 수 있습니다.")

with data_tab:
    st.subheader("공개 데이터는 어디에 쓰이나요?")
    st.markdown("활용 후보는 [NIA 2025 디지털정보격차 실태조사](https://nia.or.kr/site/nia_kor/ex/bbs/View.do?bcIdx=29168&cbIdx=81623)입니다. 현재 앱에는 이 조사의 수치를 적재하거나 학습하지 않았습니다.")
    st.write("다음 단계에서는 연령·장애 집단의 디지털 접근·역량·활용 지표와 표본 규모를 확인하고 집단별 배경 분석에 사용합니다. 공개 집계 통계와 게임 참여자 기록을 동일 인물 자료처럼 결합하지 않습니다.")
    st.subheader("이번 버전에 구현한 것")
    st.write("기록 없는 연습 → 자동 초기 수준 → 6문항 플레이 → JSON 기록 → Streamlit 분석 → 다음 수준 추천")
    st.write("난이도 1은 AB 반복, 2는 ABC 반복, 3은 AAB 또는 ABB 반복입니다. 난이도 간 실제 난도 차이는 후속 사용자 시험에서 확인해야 합니다.")
    st.subheader("학습 모델을 붙이려면")
    st.write("동일 참여자의 현재 라운드 특징, 다음 적용 난이도와 다음 라운드 결과를 쌍으로 수집해야 합니다. 이후 참여자 단위로 학습·평가를 나누고 규칙 기반 방식과 의사결정나무의 예측 성능, 완료율 및 이용 편의성을 비교합니다. 현재 1라운드 파일만으로 다음 라운드 성공 모델을 학습하지 않습니다.")
    st.caption("출처 확인일: 2026-11-10 · 공개 통계 수치 및 실제 사용자 효과는 본 시연의 검증 결과가 아닙니다.")
