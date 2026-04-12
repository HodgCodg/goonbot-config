# Procedure: Ensuring Permanent Dashboard Changes

## The Problem
"Edit failed" or "Changes not served" usually occurs when:
1. The file was edited on disk, but the running process (Flask/Systemd) is still using the old version in memory.
2. The edit was made to a file that is not actually being served (e.g., editing a template when the server is serving a hardcoded string).
3. The server crashed after the edit and didn't restart.

## The Fix Procedure (The "GoonBot Guarantee")

Whenever editing the Status Dashboard or any running service, follow these steps in order:

### 1. Verify the Target
- Ensure the file being edited is the one actually used by the running process.
- If the server uses a hardcoded `DASHBOARD_HTML` string, edit that string in the `.py` file, NOT a separate `.html` file.

### 2. Atomic Edit & Verify Disk
- Perform the edit.
- **Immediately** run `cat` or `grep` on the file to confirm the changes are physically present on the disk.

### 3. Force Process Reload
- For the Status Dashboard (Systemd User Service):
  ```bash
  systemctl --user restart status-dashboard.service
  ```
- Check the logs to ensure it started correctly:
  ```bash
  journalctl --user -u status-dashboard.service -n 20
  ```

### 4. End-to-End Verification (The "User's Eye" Check)
- Do NOT assume the restart worked. 
- Use `curl` to fetch the page and `grep` for a unique string from the new changes:
  ```bash
  curl -s http://localhost:8081 | grep "unique-new-string"
  ```
- If the `grep` fails, the change is not served. Re-examine the target file.

### 5. Final Confirmation
- Only report success to Zach after Step 4 passes.

---
**Failure Mode Recovery:**
If `curl` fails after a restart:
- Check if a duplicate process is running on the port: `netstat -tulpn | grep 8081`
- If a "ghost" process exists, kill it: `fuser -k 8081/tcp` then restart the service.
