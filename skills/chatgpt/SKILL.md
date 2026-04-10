---
name: chatgpt
description: ChatGPT integration via session token.
metadata:
  openclaw:
    emoji: "🤖"
---
# ChatGPT

```bash
python3 {baseDir}/scripts/chatgpt.py setup TOKEN
python3 {baseDir}/scripts/chatgpt.py ask "question"
```

Requires setup with browser session token from chatgpt.com cookies (`__Secure-next-auth.session-token`).
