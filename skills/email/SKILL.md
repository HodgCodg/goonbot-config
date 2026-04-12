---
name: email
description: Read emails via IMAP (O365/Exchange). Extract 2FA codes and check inbox.
metadata:
  openclaw:
    emoji: "📧"
---
# Email

```bash
python3 {baseDir}/scripts/email_reader.py inbox [N]
python3 {baseDir}/scripts/email_reader.py read ID
python3 {baseDir}/scripts/email_reader.py code  # extract 2FA code from latest email
```

Setup: `email_reader.py setup EMAIL PASSWORD [--server SERVER]`
