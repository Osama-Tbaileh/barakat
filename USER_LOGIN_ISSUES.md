# Why New Users Can't Login — Problems & Fixes

## Quick Summary

When you create a user on a client site (pos2, pos, etc.) and they try to login via the desktop app, 3 things go wrong. This document explains each one in simple terms.

---

## How the Desktop App Login Works (Background)

Before diving into the problems, you need to understand the login flow:

```
1. User types email + password in the desktop app
2. App logs into the MASTER site → gets a session token (SID)
3. App asks master: "which sites can this user access?" → master returns a list
4. User picks a site (e.g. pos2)
5. App calls verify_user_credentials(email, password) on master
   → master tries to login to pos2 with the SAME password
   → if successful, master creates a one-time SSO token
6. App uses that SSO token to login to pos2 → gets a pos2 session
7. App is now logged in and can use pos2
```

The key point: **the same password must work on BOTH master AND the client site.**

---

## Problem 1 — ImportError: Function Doesn't Exist

### What happened
When a user with access to exactly 1 site logs into master, the login returned HTTP 500 (server error) instead of success.

### Why it happened
The gateway app has two files that need to work together:
- `tenant_picker.py` — defines functions including one called `_create_sso_token` (private, starts with `_`)
- `session.py` — runs after every login and tries to import `generate_sso_token`

The problem: `generate_sso_token` **does not exist**. The function is named `_create_sso_token`. Someone wrote `session.py` expecting a function name that was never created.

```python
# session.py tries to do this:
from iztechvalley_gateway.api.tenant_picker import generate_sso_token  # ❌ doesn't exist!

# But tenant_picker.py only has:
def _create_sso_token(usr, site_names):  # private name with underscore
    ...
```

Python throws `ImportError: cannot import name 'generate_sso_token'` → the whole login fails with HTTP 500.

**Who gets hit by this?** Only users with exactly 1 accessible site. Users with 0 or multiple sites take a different code path and don't hit this line.

### How it was fixed
Added one line to `tenant_picker.py` on the server that creates an alias — same function, different name:

```python
# Added at the bottom of tenant_picker.py:
generate_sso_token = _create_sso_token  # ✅ now both names work
```

No logic changed. The function already existed, it just needed to be accessible under the expected name.

---

## Problem 2 — Login Returns "No App" Instead of "Logged In"

### What happened
After fixing Problem 1, the login to master returned HTTP 200 (success) but with `{"message": "No App"}` instead of `{"message": "Logged In"}`. The desktop app was getting a valid session cookie but the gateway was hijacking the response.

### Why it happened

**Step 1 — How Frappe runs multiple sites:**
Frappe runs all your sites (master, pos2, pos, fatima, etc.) in the **same Python process** with multiple workers. This means Python modules are loaded **once per worker** and shared across all sites.

**Step 2 — The poisoned variable:**
`session.py` has a line at the very top of the file (outside any function):

```python
# This runs ONCE when the module is first imported
FRONT_DOOR_SITE = frappe.get_site_config().get("front_door_domain", "login.iztechvalley.local")
```

Because this runs at import time (not at request time), whichever site causes the module to be imported first decides what `FRONT_DOOR_SITE` becomes — **for all sites in that worker**.

**Step 3 — pos2 "poisons" the variable for master:**
pos2's `site_config.json` had `front_door_domain: "master.35.158.120.8.nip.io"`.

If pos2 gets a request first → `session.py` is imported → `FRONT_DOOR_SITE = "master.35.158.120.8.nip.io"`.

Now when someone logs into master:
- `frappe.local.site = "master.35.158.120.8.nip.io"` (the site handling the request)
- `FRONT_DOOR_SITE = "master.35.158.120.8.nip.io"` (set by pos2 earlier)
- They match → the hook thinks "I am the front door site, run the SSO redirect logic"
- The hook runs → redirects the login response → returns `"No App"` instead of `"Logged In"`

**Visual example:**
```
Worker starts up
  ↓
pos2 gets a request first
  ↓ imports session.py
  ↓ FRONT_DOOR_SITE = "master.35.158.120.8.nip.io"  ← set from pos2's config
  ↓ (this value is now LOCKED for the lifetime of this worker)

Nancy tries to login to master
  ↓
session.py on_session_creation() fires
  ↓ checks: frappe.local.site ("master.35.158.120.8.nip.io")
  ↓         == FRONT_DOOR_SITE ("master.35.158.120.8.nip.io")  ← MATCH! (wrong)
  ↓ runs the SSO redirect code
  ↓ login response becomes "No App" ❌
```

### How it was fixed
Changed `front_door_domain` on ALL client sites from:
```
"master.35.158.120.8.nip.io"
```
to:
```
"master.35.158.120.8.nip.io:80"
```

The `:80` (port number) is the trick. `frappe.local.site` **never includes a port number** — it's always just the hostname. So now:

```
FRONT_DOOR_SITE = "master.35.158.120.8.nip.io:80"  (from pos2's config)
frappe.local.site = "master.35.158.120.8.nip.io"   (no port)

They don't match → hook returns early → login works ✅
```

Port 80 is the default HTTP port, so `http://master.35.158.120.8.nip.io:80/...` goes to the exact same server as `http://master.35.158.120.8.nip.io/...`. User sync still reaches master fine.

**Sites updated:** pos, pos2, fatima, petromall, ahmad (all 5 client sites).

---

## Problem 3 — Password Exists on Client Site but Not on Master

### What happened
Login to master returned HTTP 401 (wrong password). The user's password worked on pos2 but not on master.

### Why it happened

When the admin creates a user on pos2, two things happen:
1. pos2 creates the user and sends them a **welcome email** with a "Set your password" link
2. The gateway automatically creates the same user on master — but **without a password** and **without sending any email**

```
Admin creates fadel@demo.ps on pos2
  ↓
pos2 → welcome email → fadel sets password "abc123" on pos2 ✅
pos2 → sync to master → master creates fadel but with NO PASSWORD ❌
```

The desktop app's login flow (as explained at the top) requires:
1. Login to master with the password → needs master to have the password
2. `verify_user_credentials` re-authenticates against pos2 with the same password

Since step 1 fails (no password on master), the user can never login.

### How it was fixed

Copied the password hash directly from pos2's database into master's database via SQL.

**What is a password hash?**
Passwords are never stored as plain text. They're stored as a scrambled version called a "hash". Example:
- Plain text: `123456@ASD`
- Stored hash: `$pbkdf2-sha256$29000$FoIQYm...` (a long string)

When you login, the system hashes what you typed and compares it to the stored hash. Since both pos2 and master run the same Frappe version with the same hashing algorithm, the hash from pos2 works on master too.

**The fix (for each user):**
```sql
-- Read the hash from pos2
SELECT password FROM `__Auth` WHERE name="nancy@demo.ps"
→ $pbkdf2-sha256$29000$FoIQYm...

-- Copy it to master
INSERT INTO `__Auth` (doctype, name, fieldname, password, encrypted)
VALUES ("User", "nancy@demo.ps", "password", "$pbkdf2-sha256$...", 0)
```

**Users fixed:**
- `fadel@demo.ps` — password: `Demo@2026`
- `nancy@demo.ps` — password: `123456@ASD`

---

## What Needs to Happen for Every New User

Until the gateway app properly syncs passwords, every new user you create will have this same problem. After they set their password on the client site, you need to copy their hash to master.

**The command to run (replace `USER_EMAIL`, `CLIENT_DB`, and `MASTER_DB`):**
```bash
# Get the hash from the client site DB
HASH=$(sudo mysql -u root CLIENT_DB_NAME -sN -e "SELECT password FROM \`__Auth\` WHERE name='USER_EMAIL' AND fieldname='password'")

# Copy it to master
sudo mysql -u root MASTER_DB_NAME -e "INSERT INTO \`__Auth\` (doctype, name, fieldname, password, encrypted) VALUES ('User', 'USER_EMAIL', 'password', '$HASH', 0) ON DUPLICATE KEY UPDATE password='$HASH'"
```

**Where to find the DB names:**
- pos2: `_00b46aa7bddb8645` (from pos2's site_config.json)
- master: `_c18c02b9414a77d3` (from master's site_config.json)

**Example for a new user `ahmad@demo.ps` on pos2:**
```bash
HASH=$(sudo mysql -u root _00b46aa7bddb8645 -sN -e "SELECT password FROM \`__Auth\` WHERE name='ahmad@demo.ps' AND fieldname='password'")
sudo mysql -u root _c18c02b9414a77d3 -e "INSERT INTO \`__Auth\` (doctype, name, fieldname, password, encrypted) VALUES ('User', 'ahmad@demo.ps', 'password', '$HASH', 0) ON DUPLICATE KEY UPDATE password='$HASH'"
```

Run this on the EC2 server after the user has set their password.

---

## Summary Table

| Problem | Root Cause | Fix Applied | Permanent? |
|---|---|---|---|
| HTTP 500 ImportError | `generate_sso_token` function missing from gateway code | Added alias `generate_sso_token = _create_sso_token` to server file | No — will be overwritten on next `git pull` of gateway |
| "No App" / hook hijacking | `FRONT_DOOR_SITE` module variable poisoned by client site import | Added `:80` to `front_door_domain` on all client sites | Yes — persists in site_config.json |
| 401 on master / no password | Gateway creates users without password on master | Copy password hash from client DB to master DB manually | No — must repeat for every new user |

---

## The Permanent Fix (for the Gateway Team)

The gateway app needs two code changes:
1. Add `generate_sso_token` as a proper function in `tenant_picker.py` (not just an alias on the server file)
2. Fix `session.py` to read `front_door_domain` lazily inside the function (not at module level), so the multi-tenancy import-order race condition can't happen
3. When syncing a user from client to master, also sync their password (or trigger a "set password" email from master)
