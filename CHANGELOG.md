# 📝 SHIZU SECURITY CHANGELOG

## 🚀 Version 2.3.0 — Zero-Trust Architecture & Profile Assets
* **Default Deny Kernel:** Administrative Discord permissions alone do NOT confer trust. Every event resolves: `Actor -> Active Scopes -> Required Scope -> Burst Limit -> Allow or Breach`.
* **Granular Additive Scopes:** Implemented canonical scope registry across Channels, Roles, Members, Webhooks/Bots, Server/Emojis, AutoMod Bypass, and Moderation.
* **Supreme Bundle:** Grants all operational and recovery scopes while strictly excluding Admin scopes (`whitelist.manage`, `extraowner.manage`, `security.configure`, `lockdown.toggle`).
* **Fixed Sliding-Window Burst Throttle:** Hardcoded to **3 destructive actions in 10.0 seconds** to halt hijacked administrator tokens and rogue automation.
* **Audit Uncertainty Rule:** If audit log cannot correlate an actor within 5.0 seconds, the bot safely reverts the damage and logs the incident ticket, but never bans an innocent user.
* **Role Whitelisting Security Trap:** Whitelisting a role means anyone below Extra Owner who assigns that role to a member trips an immediate breach.
* **Interactive Whitelist UI:** `?whitelist add <@user|@role>` launches an interactive panel with multi-select sections, Supreme button, and optional modal for target ID and expiration.
* **Unified Help & Setup Center:** `?help` upgraded to a multi-page interactive dashboard with persistent components, inline toggles, modals for prefix and bad words, and authorization re-checks.
* **Animated Bot Assets:** Generated high-definition animated avatar GIF (512×512) and animated banner GIF (960×384) starring the Shizu mascot with HUD reticles and 3D rolling cyber grid.
* **One-Click Profile Applicator:** Added `set_bot_profile.py` for automated profile uploading to Discord.
* **Clean Animated Emojis:** Standardized clean animated emojis (`<a:tick:...>`, `<a:alert:...>`, `<a:gears:...>`, `<a:Warning:...>`) across all embeds and audit logs.

---

## 1. Streamlined Core Architecture (v2.2.0)
* **Removed Anti-Raid Subsystem (`cogs/antiraid`):** Completely eradicated `antiraid` listeners, commands, and database clutter per user request. This eliminates all risk of false positives from viral invite spikes or kicking legitimate new Discord users.
* **Streamlined Core Modules:** The bot now focuses 100% on its three essential pillars:
  1. **Anti-Nuke Protection & Disaster Recovery**
  2. **Real-Time AutoMod**
  3. **Hierarchy-Safe Moderation**

---

## 2. Cons Resolved in v2.2.0

### A. AutoMod Anti-Invite False Positives (Resolved)
* **Previous Con:** The invite filter previously blocked all Discord invite links indiscriminately, including the server's own vanity URL and active server invites.
* **Resolution:** Upgraded `cogs/automod/listener.py` to inspect the invite code: if it matches the guild's `vanity_url_code` or any active server invite generated on the guild, it is automatically permitted. External server invites remain strictly blocked.

### B. Purge 14-Day Discord API Error (Resolved)
* **Previous Con:** Purging channels containing messages older than 14 days could trigger Discord's `400 Bad Request` bulk deletion error.
* **Resolution:** Added an automated `after = utcnow() - 14 days` filter to `ctx.channel.purge`, guaranteeing that messages older than 14 days are safely excluded from bulk calls, eliminating API crashes.

### C. Manual Backup Burden (Resolved)
* **Previous Con:** Reconstructing nuked channels previously required staff to remember to take manual snapshots.
* **Resolution:** Snapshotting is now **100% automated**. The bot automatically captures and updates channel and role snapshots on startup (`on_ready`) and during channel/role modifications.

### D. Re-Creating Nuked Channels with Exact Permissions (Resolved)
* **Previous Con:** Basic bots recreate channels with default public permissions, exposing private staff channels.
* **Resolution:** Reconstructs the exact role and user permission overwrite dictionary from snapshots so private/staff channels remain secure upon recreation.

### E. Rogue Channel Deletion (Resolved)
* **Previous Con:** Nuke scripts that spam 20+ channels could flood the server before an admin reacted.
* **Resolution:** Deletes the rogue channel on entry, bans the creator, and sweeps the server to delete any other matching channels created in the burst window.

---

## 3. Verification & Test Summary
* **Python Compilation:** 22/22 Python source files compiled with 0 syntax errors.
* **Extension Loading:** All 8 modular extensions loaded into `ShizuSecurity` bot instance without warnings.
* **Command Registry:** 35 top-level commands verified and registered cleanly.
* **Dependencies:** Clean, lean, and standalone (no Lavalink, Wavelink, FFmpeg, or audio dependencies).
