# 기록 정의와 분석 설계

JSON 스키마 버전은 `1.0`, 라운드는 `stage=1`입니다. 한 파일에는 완료한 한 라운드의 6문항만 담깁니다.

| 필드 | 형식 및 단위 | 정의 |
|---|---|---|
| `participant_id` | 임의 문자열 | 페이지 안 재도전에 유지되는 가명 ID |
| `round_id` | 임의 문자열 | 매 라운드 고유 ID, 중복 가져오기 방지 |
| `completed_at` | ISO 8601 UTC | 완료 시각 |
| `recording_consent` | boolean | 기록 이용 동의, 완료 기록은 true |
| `retry_count` | 0 이상 정수 | 첫 시행 0, 같은 페이지 재도전마다 1 증가 |
| `initial_level` | 1~3 | 게임 경험으로 정한 1라운드 난이도 |
| `profile.experience` | new / sometimes / often / unspecified | 게임 경험 |
| `profile.age_group` | under40 / 40to64 / 65plus / unspecified | 선택 연령대 |
| `profile.disability` | yes / no / unspecified | 선택 장애 여부 |
| `profile.demographic_consent` | boolean | 선택 정보 기록 동의 |
| `profile.extra_time` | boolean | 제한 시간 1.5배 적용 여부 |
| `profile.large_text` | boolean | 큰 글씨 사용 여부 |
| `questions[].question_index` | 1~6 | 문항 순서 |
| `level` | 1~3 | 적용 난이도 |
| `cycle` | 정수 배열 | 반복 묶음, 0 동그라미 / 1 세모 / 2 네모 / 3 마름모 |
| `sequence` | 정수 배열 | 실제 보여 준 배열, 묶음 2회 이상 3회 미만 |
| `selected` | 0~3 또는 null | 고른 도형, 시간 초과·건너뜀은 null |
| `correct_answer` | 0~3 | 배열 다음에 오는 도형, 서버에서 재계산 |
| `correct` | boolean | 정답 여부, 서버에서 재계산 |
| `outcome` | answer / timeout / skip | 제출·시간 초과·건너뜀 |
| `response_ms` | 밀리초 | 일시정지 제외 응답 시간. 시간 초과는 제한 시간으로 고정 |
| `limit_ms` | 밀리초 | 해당 이용자에게 실제 적용한 제한 시간 |
| `hint_used` | boolean | 해당 문항의 힌트 사용 여부 |

## 집계 정의

정답률 = 정답 문항 수 / 6. 오답, 건너뜀, 시간 초과는 분모에 포함합니다. 중앙 응답 시간은 여섯 값을 정렬한 후 가운데 두 값의 평균입니다. 시간 비율은 각 문항 `response_ms / limit_ms`의 중앙값입니다. 라운드 목표 달성은 정답 4개 이상입니다. 힌트는 한 문항에서 한 번만 열 수 있습니다.

## 검증

`validate_record`는 허용된 필드만 반환합니다. 미동의, 미완료, 비정상 시간, 잘못된 패턴, 난이도·지원 설정 불일치를 거부합니다. 브라우저가 준 정답 점수를 그대로 신뢰하지 않고 다시 계산합니다. 파일의 순서와 형식은 검증하지만 기록의 진위나 실제 참여자 존재를 보증하지는 않습니다. 서버가 서명한 연구용 데이터가 아닙니다.

## 공개 데이터 연결 계획

NIA 조사에서 조사연도, 집단 정의, 표본수, 접근·역량·활용 지표의 단위와 기준을 먼저 정리합니다. 집계 자료는 `year, group, indicator, value, unit, sample_n, source_url` 같은 별도 통계표로 관리합니다. `participant_id`와 연결하지 않습니다. 원자료 사용 가능 여부와 이용 조건은 실제 확보 때 확인합니다.

## 후속 AI 학습 계획

현재 버전은 학습을 실행하지 않습니다. 2라운드 구현 후 동의된 데이터에 `previous_round_id, applied_next_level, next_stage_success, participant_id`를 추가하고, 이전 수행 특징만으로 다음 결과를 예측합니다. 다음 라운드 결과를 입력 특징으로 넣지 않습니다. 참여자 단위로 학습·검증·평가를 분리하고, 같은 사람의 재도전 기록이 서로 다른 분할에 섞이지 않게 합니다.

고정 난이도, 초기 정보만 쓴 규칙, 플레이 보정 규칙, 학습 모델을 비교합니다. 조건별 난이도 노출과 순서 효과가 달라질 수 있으므로 단순 관찰 자료만으로 개선 효과를 단정하지 않습니다. 정확도뿐 아니라 확률 보정, 목표 달성, 이탈, 만족도와 집단별 표본수·불확실성을 확인합니다. 이탈률에는 별도의 시작·중단 이벤트 수집이 필요합니다.
