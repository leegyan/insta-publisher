# insta-publisher

인스타그램 공식 API(Instagram API with Instagram Login)로 캐러셀 게시물 · 릴스 · 스토리를 정해진 시각에 자동 게시한다(게시 1건 = 캐러셀 + 릴스 + 그 릴스 영상을 스토리로, 이 순서). 스토리에는 API로 캡션 · 링크 스티커를 넣을 수 없다(보는 사람은 화면 위 계정 이름을 눌러 프로필로 간다). GitHub Actions(공개 저장소, 요금 없음)에서 30분마다 실행된다.

## 구조
| 위치 | 내용 |
|---|---|
| `main` 가지 | 코드(publish.py · enqueue.py · accounts.json · 워크플로우)와 `기록/게시기록.jsonl`(게시 결과) |
| `queue` 가지 | 게시 대기 발간물(`posts/<계정>/<게시물ID>/01.jpg… · post.json`). 매번 부모 없는 커밋 1개로 덮어써서 지난 이미지 이력이 쌓이지 않는다 |
| Actions 비밀값 | 계정마다 토큰(`IG_TOKEN_...`), 토큰 갱신용 `GH_ADMIN_TOKEN`. 저장소 파일에는 토큰을 적지 않는다 |

## 흐름
1. 작업 세션이 `python3 enqueue.py <발간물폴더> <계정> <게시시각>` → PNG를 JPEG로 바꿔 queue 가지에 넣는다. 릴스는 `--reel <릴스판폴더>`(mp4 1개 + 커버.jpg + 캡션.txt) → 릴스와 같은 영상의 스토리를 함께 넣는다. 커버.jpg 는 INSTA `공용/tools/reel_cover.py` 가 만들고 cover_url 로 넘긴다(없으면 대기열에 넣지 않음). 지운 릴스를 다시 올릴 때는 `--reel-only --id-suffix _재게시1` 스토리만은 `--story <릴스판폴더>`
2. `인스타그램 게시` 워크플로우(30분마다): 게시 시각이 지난 발간물을 장마다 컨테이너 → 캐러셀 컨테이너 → media_publish로 게시 → 결과를 게시기록에 적고 queue에서 뺀다
3. `토큰 갱신` 워크플로우(매주 월요일): 계정마다 토큰을 갱신(60일 유효)하고 비밀값을 바꾼다

## 계정 추가
`accounts.json`의 accounts에 `"아이디": {"ig_user_id": "숫자", "token_secret": "IG_TOKEN_이름"}`을 넣고, 같은 이름의 비밀값에 토큰을 넣는다.

## 주의
- queue 가지의 이미지 · 캡션은 게시 전까지 공개 저장소에서 누구나 볼 수 있다
- 공개 저장소의 예약 워크플로우는 저장소 활동이 60일 없으면 GitHub가 멈춘다(게시기록 커밋이 활동으로 잡힘)
- 실패하면 워크플로우가 실패로 끝나고 GitHub가 저장소 주인에게 메일을 보낸다(GitHub 기본 알림)
