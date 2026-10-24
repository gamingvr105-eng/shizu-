# 🛡️ SHIZU SECURITY — Standalone Discord Security Bot

High-performance, streamlined Discord defense system engineered exclusively for **Anti-Nuke protection**, **real-time AutoMod**, and **hierarchy-safe moderation**.

---

## 👥 Developers & Ownership
* **Developers:** `VIPER & PRASHU`
* **Bot Owners:** `1478730719571349545`, `1509545584317562970`
* **Version:** `2.3.0` (Zero-Trust Edition)
* **Architecture:** Standalone Python 3.10+ / 3.11 with `discord.py 2.x` and asynchronous SQLite (`aiosqlite`).

---

## ⚡ Core Pillars

### 1. 🛡️ Anti-Nuke & Disaster Recovery
* **Auto-Recreate Nuked Channels:** When an unauthorized administrator deletes a channel, the bot immediately bans the attacker and recreates the channel with its exact name, category, topic, NSFW flag, slowmode, and **exact role/member permission overwrites**.
* **Instant Rogue Channel Deletion:** When an attacker tries to spam-create nuke channels (e.g. `nuked-by-xyz`), the bot bans the creator, deletes the rogue channel on sight, and purges any matching spam channels created in the burst window.
* **Role Protection:** Recreates nuked roles with exact permissions and color; deletes rogue roles created by attackers on sight.
* **Privilege Escalation Interception:** Strips dangerous administrative permissions if an unwhitelisted user assigns them to an alt account, and bans the perpetrator.
* **Auto-Unban on Malicious Ban:** Reverts unauthorized bans and bans the attacker.
* **Rogue Bot & Webhook Destruction:** Rogue bot invites and unauthorized webhooks are destroyed immediately.
* **Disaster Recovery Snapshots:** `?backup` takes an instant snapshot of all channels, categories, roles, and permission trees. `?restore channels` or `?restore roles` recreates missing structures with one command.
* **Emergency Server Lockdown:** `?lockdown` freezes all public speech across channels during an emergency, with safe recovery via `?unlockdown`.

### 2. ⚡ Real-Time AutoMod
* **Anti-Spam / Flood:** Deletes rapid message bursts and repeated duplicate text.
* **Anti-Invite with Own-Server Exemption:** Blocks foreign Discord invites while automatically permitting your server's own vanity URL and active server invite links.
* **Anti-Link with Media Whitelist:** Blocks external URLs while allowing safe media (Tenor, Giphy, Spotify tracks, Discord CDN).
* **Bad-Word Filtering:** Multi-word customizable blacklist with word-boundary (`\b`) matching (`?badwords add/remove/list/clear`).
* **Anti-Caps, Mentions & Emojis:** Prevents uppercase shouting, mass mention pings, and emoji flooding.
* **Custom Punishments & Exemptions:** Each rule can be set to `delete`, `warn`, `timeout <mins>`, `kick`, or `ban`, with channel/role/user exemptions (`?automod ignore`).

### 3. 🔨 Hierarchy-Safe Moderation
* **Strict Hierarchy Enforcement:** Never allows staff to moderate superiors, server owners, or bot developers.
* **Commands:** `ban`, `unban`, `kick`, `timeout` (mute), `untimeout`, `warn`, `purge` (up to 500, auto-capped to 14 days), `slowmode`, `lock`, `unlock`, `hide`, `unhide`, `role add/remove`, `setnick`, and `snipe`.
* **Moderation Case IDs:** Every disciplinary action generates a persistent Case ID with timestamp, target, moderator, and reason (`?case <id>`, `?modlogs <user>`).
* **Warnings Ledger:** Formal warning ledger with reasons and moderator tracking (`?warnings <user>`, `?clearwarns <user> [id]`).

---

## 🎨 Shizu Signature UI
* **No User Pinging:** All replies use `mention_author=False` for clean chat interactions.
* **Sleek Minimalist Dark Embeds:** Styled in pure black (`color=0x000000`).
* **Animated Emoji Integration:**
  * `<a:tick:1261574239354621963>` — Success confirmations
  * `<a:Warning:1299512982006665216>` — Errors and alerts
  * `<a:gears:1261577892752789586>` — Shield operations & backups
  * `<a:RedLoading:1246777916621197424>` — Processing indicators

---

## 📌 Command Reference

### Anti-Nuke & Recovery
| Command | Description |
|---|---|
| `?antinuke` | Anti-nuke control menu & status |
| `?antinuke enable` | Activates real-time breach protection |
| `?antinuke disable` | Deactivates anti-nuke protection |
| `?antinuke punishment <ban\|kick\|strip>` | Configures breach penalty |
| `?antinuke status` | Displays detailed protection dashboard |
| `?backup` | Saves layout snapshot of all channels, roles, and overwrites |
| `?restore channels` | Recreates any missing channels from snapshot |
| `?restore roles` | Recreates any missing roles from snapshot |
| `?whitelist add <@user>` | Adds user to Anti-Nuke whitelist |
| `?whitelist remove <@user>` | Removes user from whitelist |
| `?whitelist list` | Lists all whitelisted users |
| `?whitelist check <@user>` | Checks user whitelist permissions |
| `?whitelist reset` | Clears all whitelisted users |
| `?extraowner add <@user>` | Assigns an Extra Owner (Server Owner only) |
| `?extraowner remove <@user>` | Removes an Extra Owner |
| `?extraowner list` | Lists all Extra Owners |
| `?lockdown` | Engages emergency server-wide text lockdown |
| `?unlockdown` | Restores normal channel permissions |

### AutoMod
| Command | Description |
|---|---|
| `?automod` | AutoMod control dashboard |
| `?automod enable\|disable` | Globally toggles AutoMod |
| `?automod status` | Displays all rules, states, and penalties |
| `?automod rule <rule> <enable\|disable>` | Toggles specific rule |
| `?automod punish <rule> <action> [mins]` | Configures punishment for a rule |
| `?automod threshold <rule> <number>` | Sets threshold for caps, mentions, etc. |
| `?automod ignore <channel\|role\|user> <target>` | Exempts target from AutoMod |
| `?automod unignore <channel\|role\|user> <target>` | Removes exemption |
| `?automod ignored` | Lists all exemptions |
| `?badwords add <word>` | Adds word to filter |
| `?badwords remove <word>` | Removes word from filter |
| `?badwords list` | Lists blacklisted words |
| `?badwords clear` | Clears all blacklisted words |

### Moderation
| Command | Description |
|---|---|
| `?ban <member\|id> [reason]` | Bans user with DM notice and case logging |
| `?unban <user_id> [reason]` | Unbans user by ID |
| `?kick <member> [reason]` | Kicks member with DM notice |
| `?timeout <member> <duration> [reason]` | Times out member (e.g. `10m`, `1h`, `1d`) |
| `?untimeout <member> [reason]` | Removes active timeout |
| `?warn <member> [reason]` | Issues formal warning |
| `?purge <amount> [@user]` | Deletes up to 500 messages |
| `?slowmode <seconds> [channel]` | Configures channel slowmode |
| `?lock [channel] [reason]` | Locks a text channel |
| `?unlock [channel]` | Unlocks a text channel |
| `?hide [channel]` | Hides text channel from members |
| `?unhide [channel]` | Makes channel visible again |
| `?role add <member> <role>` | Assigns role (hierarchy checked) |
| `?role remove <member> <role>` | Removes role (hierarchy checked) |
| `?setnick <member> [nickname]` | Changes or resets nickname |
| `?snipe [channel]` | Views last deleted message |

### Cases & System
| Command | Description |
|---|---|
| `?security` | Comprehensive server security dashboard |
| `?case <case_id>` | Views complete case information |
| `?modlogs <user>` | Views user moderation history |
| `?warnings <member>` | Views user warning history |
| `?clearwarns <member> [id]` | Clears member warnings |
| `?setlog <antinuke\|automod\|mod> <#channel>` | Configures dedicated log channel |
| `?setprefix <prefix>` | Configures custom server prefix |
| `?ping` | Shows bot gateway & roundtrip latency |
| `?stats` | Displays bot statistics and developers |
| `?help [command]` | Interactive dropdown help menu |

---

## 🚀 Setup & Execution
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `.env`:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   DEFAULT_PREFIX=?
   OWNER_IDS=1478730719571349545,1509545584317562970
   ```
3. Run Shizu Security:
   ```bash
   python main.py
   ```
