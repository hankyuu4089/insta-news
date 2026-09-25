publish.py

import os, re, sys, time, requests

pid = sys.argv[1]
if not re.fullmatch(r"\d{8}-\d{4}", pid):
    sys.exit("잘못된 id")
repo = os.environ["GITHUB_REPOSITORY"]
ig, tok = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
G = "https://graph.facebook.com/v21.0"


def notify(t):
    requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
                  data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": t}, timeout=30)


def check(r):
    if not r.ok:
        raise RuntimeError(r.text[:300])
    return r.json()


try:
    caption = open(f"out/{pid}.txt", encoding="utf-8").read()
    url = f"https://raw.githubusercontent.com/{repo}/main/out/{pid}.mp4"
    for _ in range(6):  # raw.githubusercontent.com에 방금 push한 커밋이 반영될 때까지 대기
        if requests.head(url, timeout=15).ok:
            break
        time.sleep(5)
    cid = check(requests.post(f"{G}/{ig}/media", data={"media_type": "REELS", "video_url": url,
                "caption": caption, "access_token": tok}, timeout=60))["id"]
    for _ in range(60):
        s = requests.get(f"{G}/{cid}", params={"fields": "status_code", "access_token": tok},
                         timeout=30).json().get("status_code")
        if s == "FINISHED":
            break
        if s == "ERROR":
            raise RuntimeError("인스타에서 영상 처리 실패")
        time.sleep(10)
    else:
        raise RuntimeError("영상 처리 시간 초과")
    mid = check(requests.post(f"{G}/{ig}/media_publish", data={"creation_id": cid,
                "access_token": tok}, timeout=60))["id"]
    link = requests.get(f"{G}/{mid}", params={"fields": "permalink", "access_token": tok},
                        timeout=30).json().get("permalink", "")
    notify(f"✅ 인스타그램에 발행했어요\n{link}")
except Exception as e:
    notify(f"⚠️ 발행 실패: {e}")
    raise
