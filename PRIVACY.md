# 개인정보처리방침 (Privacy Policy) — gyan_publisher / insta-publisher

이 앱은 저장소 주인이 운영하는 자기 계정(인스타그램 · 유튜브)에 직접 만든 영상과 이미지를 올리고, 자기 게시물에 달린 댓글에 자료를 보내 주는 개인용 도구다.

## 쓰는 권한
- 인스타그램: 기본 정보(instagram_business_basic), 게시(instagram_business_content_publish), 댓글 읽기 · 답글(instagram_business_manage_comments), 비공개 답장 DM(instagram_business_manage_messages). 저장소 주인의 계정에서만 쓴다
- 유튜브: 영상 업로드(youtube.upload)

## 처리하는 정보
- 저장소 주인의 게시물에 댓글을 단 사람에게 같은 안내 DM 한 통과 공개 답글 한 줄을 보내기 위해, 그 댓글의 ID와 작성 시각만 읽는다
- 보낸 댓글의 ID와 보낸 시각만 기록해 같은 사람에게 두 번 보내지 않게 한다. 이름 · 사진 · 메시지 내용 같은 다른 정보는 저장하지 않고, 누구와도 공유하지 않는다
- 접근 토큰은 GitHub Actions 비밀값으로만 보관한다

## 데이터 삭제
- 기록 삭제를 원하면 인스타그램 @cashwood.lab 으로 DM 을 보내 주세요. 요청을 받은 뒤 7일 안에 그 댓글 ID 기록을 지운다
- 연결 해제: 인스타그램 설정 → 웹사이트 권한 → 앱 및 웹사이트, Google 계정 → 보안 → 타사 앱 액세스에서 언제든 끊을 수 있다

---

This app is a personal tool that publishes the owner's own content to the owner's own Instagram and YouTube accounts, and sends one identical guide message (private reply) and one short public reply to people who comment on the owner's posts. It reads only the comment ID and timestamp, stores only the IDs of comments already answered (to avoid duplicates), stores access tokens only as GitHub Actions secrets, and does not collect, store or share any other data. To request deletion of your record, send a DM to @cashwood.lab on Instagram; it will be deleted within 7 days.
