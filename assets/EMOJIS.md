# 🎨 Shizu Security — Animated Emoji Directory & Configuration

Every confirmation, alert, log embed, and status response in **Shizu Security v2.3.0** uses professional animated Discord emojis matching the signature aesthetic of Shizu Music.

---

## ⚡ Active Animated Emojis

| Constant Name | Animated Format | Visual Purpose |
|---|---|---|
| `ANIM_SUCCESS` | `<a:tick:1261574239354621963>` | Action confirmations, successful restorations, whitelist grants |
| `ANIM_WARN` | `<a:Warning:1299512982006665216>` | Warning notices, rate limits, disarmed states, transient notices |
| `ANIM_ALERT` | `<a:alert:1272569018183843874>` | Security breaches, lockdown triggers, unauthorized privilege escalations |
| `ANIM_SHIELD` | `<a:gears:1261577892752789586>` | Real-time defense operations, snapshot backups, self-healing restorations |
| `ANIM_LOADING` | `<a:RedLoading:1246777916621197424>` | Processing background operations, audit log lookups, latency tests |
| `ANIM_HAMMER` | `<a:olympus_WarnFlash:1272569018183843874>` | Moderation disciplinary sanctions (ban, kick, timeout, purge) |

---

## 🔧 How to Customize Emoji IDs

All emoji strings are centralized in [`config/config.py`](file:///c:/Users/xdvip/Videos/security%20bot/config/config.py).  
If you want to use custom animated emojis from your own Discord server:

1. Upload the animated GIF emojis to your Discord server or application.
2. In Discord, type `\:emoji_name:` in any channel and press Enter to reveal the exact syntax:
   ```text
   <a:custom_name:123456789012345678>
   ```
3. Update the constants in `config/config.py`:
   ```python
   ANIM_SUCCESS = "<a:your_check_tick:123456789012345678>"
   ANIM_WARN = "<a:your_warning:123456789012345678>"
   ANIM_ALERT = "<a:your_alert:123456789012345678>"
   ANIM_SHIELD = "<a:your_shield:123456789012345678>"
   ANIM_LOADING = "<a:your_loading:123456789012345678>"
   ANIM_HAMMER = "<a:your_hammer:123456789012345678>"
   ```
4. Restart the bot. Shizu Security will immediately render your custom animated emojis across all embeds and responses.
