import aiosqlite
import os
import json
import datetime
from typing import Optional, Dict, Any, List, Tuple, Set
from core.scopes import ALL_OPERATIONAL_SCOPES, SCOPES_ADMIN, is_admin_scope

class Database:
    def __init__(self, db_path: str = "database/shizu_security.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Initializes the database connection and creates all required tables."""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self.create_tables()
        await self.migrate_v22_whitelist()

    async def close(self):
        """Closes the database connection cleanly."""
        if self.conn:
            await self.conn.close()

    async def create_tables(self):
        """Creates the entire database schema if it doesn't already exist."""
        queries = [
            # Guild configuration
            """
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '?',
                antinuke_enabled BOOLEAN DEFAULT FALSE,
                antibot_enabled BOOLEAN DEFAULT FALSE,
                antinuke_punishment TEXT DEFAULT 'ban',
                automod_enabled BOOLEAN DEFAULT FALSE,
                log_antinuke INTEGER DEFAULT NULL,
                log_automod INTEGER DEFAULT NULL,
                log_moderation INTEGER DEFAULT NULL,
                emergency_locked BOOLEAN DEFAULT FALSE,
                topcheck_enabled BOOLEAN DEFAULT TRUE
            );
            """,
            # Legacy whitelisted users (preserved for backward compatibility & migration)
            """
            CREATE TABLE IF NOT EXISTS whitelisted_users (
                guild_id INTEGER,
                user_id INTEGER,
                all_perms BOOLEAN DEFAULT FALSE,
                ban BOOLEAN DEFAULT FALSE,
                kick BOOLEAN DEFAULT FALSE,
                prune BOOLEAN DEFAULT FALSE,
                botadd BOOLEAN DEFAULT FALSE,
                serverup BOOLEAN DEFAULT FALSE,
                memup BOOLEAN DEFAULT FALSE,
                chcr BOOLEAN DEFAULT FALSE,
                chdl BOOLEAN DEFAULT FALSE,
                chup BOOLEAN DEFAULT FALSE,
                rlcr BOOLEAN DEFAULT FALSE,
                rlup BOOLEAN DEFAULT FALSE,
                rldl BOOLEAN DEFAULT FALSE,
                meneve BOOLEAN DEFAULT FALSE,
                mngweb BOOLEAN DEFAULT FALSE,
                mngstemo BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (guild_id, user_id)
            );
            """,
            # Zero-Trust Whitelist Entities (supports both Users and Roles)
            """
            CREATE TABLE IF NOT EXISTS whitelist_entities (
                guild_id INTEGER NOT NULL,
                entity_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL CHECK(entity_type IN ('user', 'role')),
                is_legacy_supreme BOOLEAN DEFAULT FALSE,
                created_at TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                PRIMARY KEY (guild_id, entity_id)
            );
            """,
            # Granular Additive Scopes (with optional target binding and expiration)
            """
            CREATE TABLE IF NOT EXISTS whitelist_scopes (
                guild_id INTEGER NOT NULL,
                entity_id INTEGER NOT NULL,
                scope TEXT NOT NULL,
                target_id INTEGER DEFAULT 0,
                expires_at TEXT DEFAULT NULL,
                PRIMARY KEY (guild_id, entity_id, scope, target_id)
            );
            """,
            # Security Audit Trail (captures grants, actions, and breach detections)
            """
            CREATE TABLE IF NOT EXISTS security_audit_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                actor_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                scope_required TEXT,
                target_id INTEGER,
                outcome TEXT NOT NULL CHECK(outcome IN ('ALLOWED', 'BREACH_STOPPED', 'REVERTED_UNCERTAIN')),
                incident_id TEXT DEFAULT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            );
            """,
            # Extra owners (multiple per guild supported)
            """
            CREATE TABLE IF NOT EXISTS extraowners (
                guild_id INTEGER,
                owner_id INTEGER,
                PRIMARY KEY (guild_id, owner_id)
            );
            """,
            # AutoMod rules per guild
            """
            CREATE TABLE IF NOT EXISTS automod_rules (
                guild_id INTEGER,
                rule_name TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                punishment TEXT DEFAULT 'delete',
                timeout_duration INTEGER DEFAULT 300,
                threshold INTEGER DEFAULT 5,
                PRIMARY KEY (guild_id, rule_name)
            );
            """,
            # AutoMod ignored entities (channels, roles, users)
            """
            CREATE TABLE IF NOT EXISTS automod_ignored (
                guild_id INTEGER,
                target_id INTEGER,
                target_type TEXT,
                PRIMARY KEY (guild_id, target_id, target_type)
            );
            """,
            # Bad words filter per guild
            """
            CREATE TABLE IF NOT EXISTS badwords (
                guild_id INTEGER,
                word TEXT,
                PRIMARY KEY (guild_id, word)
            );
            """,
            # Moderation Cases
            """
            CREATE TABLE IF NOT EXISTS moderation_cases (
                guild_id INTEGER,
                case_id INTEGER,
                action TEXT,
                target_id INTEGER,
                target_name TEXT,
                moderator_id INTEGER,
                moderator_name TEXT,
                reason TEXT,
                timestamp TEXT,
                PRIMARY KEY (guild_id, case_id)
            );
            """,
            # Moderation user warnings
            """
            CREATE TABLE IF NOT EXISTS user_warnings (
                warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                timestamp TEXT
            );
            """,
            # Emergency lockdown state storage
            """
            CREATE TABLE IF NOT EXISTS emergency_channels (
                guild_id INTEGER,
                channel_id INTEGER,
                PRIMARY KEY (guild_id, channel_id)
            );
            """,
            # Channel layout snapshots for instant recovery after a nuke
            """
            CREATE TABLE IF NOT EXISTS channel_snapshots (
                guild_id INTEGER,
                channel_id INTEGER,
                name TEXT,
                channel_type TEXT,
                category_name TEXT,
                category_id INTEGER,
                position INTEGER,
                topic TEXT,
                nsfw BOOLEAN,
                slowmode_delay INTEGER,
                overwrites_json TEXT,
                PRIMARY KEY (guild_id, channel_id)
            );
            """,
            # Role layout snapshots for instant recovery after a nuke
            """
            CREATE TABLE IF NOT EXISTS role_snapshots (
                guild_id INTEGER,
                role_id INTEGER,
                name TEXT,
                permissions INTEGER,
                color INTEGER,
                hoist BOOLEAN,
                mentionable BOOLEAN,
                position INTEGER,
                PRIMARY KEY (guild_id, role_id)
            );
            """,
            # Guild settings snapshot (server name, icon, system/afk channels, etc.)
            """
            CREATE TABLE IF NOT EXISTS guild_snapshots (
                guild_id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT,
                afk_timeout INTEGER,
                afk_channel_id INTEGER,
                system_channel_id INTEGER,
                rules_channel_id INTEGER,
                verification_level TEXT,
                default_notifications TEXT,
                vanity_code TEXT,
                timestamp TEXT
            );
            """,
            # Server emoji snapshots
            """
            CREATE TABLE IF NOT EXISTS emoji_snapshots (
                guild_id INTEGER,
                emoji_id INTEGER,
                name TEXT,
                animated BOOLEAN,
                url TEXT,
                roles_json TEXT,
                PRIMARY KEY (guild_id, emoji_id)
            );
            """,
            # Member role assignment snapshot
            """
            CREATE TABLE IF NOT EXISTS member_role_snapshots (
                guild_id INTEGER,
                user_id INTEGER,
                role_ids_json TEXT,
                timestamp TEXT,
                PRIMARY KEY (guild_id, user_id)
            );
            """
        ]
        for query in queries:
            await self.conn.execute(query)
        # Automatic column migration for antibot_enabled
        try:
            await self.conn.execute("ALTER TABLE guild_config ADD COLUMN antibot_enabled BOOLEAN DEFAULT FALSE")
        except Exception:
            pass
        await self.conn.commit()

    async def migrate_v22_whitelist(self):
        """Migrates legacy v2.2 whitelisted users to Zero-Trust whitelist_entities with 30-day Legacy-Supreme."""
        try:
            async with self.conn.execute("SELECT * FROM whitelisted_users") as cursor:
                legacy_rows = await cursor.fetchall()
        except Exception:
            return

        now = datetime.datetime.utcnow()
        expiry_30d = (now + datetime.timedelta(days=30)).isoformat()
        now_str = now.isoformat()

        for row in legacy_rows:
            guild_id = row["guild_id"]
            user_id = row["user_id"]

            # Check if entity already exists in new table
            async with self.conn.execute(
                "SELECT 1 FROM whitelist_entities WHERE guild_id = ? AND entity_id = ?",
                (guild_id, user_id)
            ) as check_cursor:
                if await check_cursor.fetchone():
                    continue

            # Insert entity as Legacy-Supreme
            await self.conn.execute(
                """
                INSERT OR IGNORE INTO whitelist_entities 
                (guild_id, entity_id, entity_type, is_legacy_supreme, created_at, created_by)
                VALUES (?, ?, 'user', TRUE, ?, 0)
                """,
                (guild_id, user_id, now_str)
            )

            # Assign all operational scopes with 30-day expiry
            for sc in ALL_OPERATIONAL_SCOPES:
                await self.conn.execute(
                    """
                    INSERT OR IGNORE INTO whitelist_scopes 
                    (guild_id, entity_id, scope, target_id, expires_at)
                    VALUES (?, ?, ?, 0, ?)
                    """,
                    (guild_id, user_id, sc, expiry_30d)
                )

        await self.conn.commit()

    # --- Guild Configuration Methods ---
    async def get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        async with self.conn.execute("SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
        # Default config
        default = {
            "guild_id": guild_id,
            "prefix": "?",
            "antinuke_enabled": False,
            "antibot_enabled": False,
            "antinuke_punishment": "ban",
            "automod_enabled": False,
            "log_antinuke": None,
            "log_automod": None,
            "log_moderation": None,
            "emergency_locked": False,
            "topcheck_enabled": True
        }
        await self.conn.execute(
            """
            INSERT OR IGNORE INTO guild_config (guild_id, prefix)
            VALUES (?, ?)
            """,
            (guild_id, "?")
        )
        await self.conn.commit()
        return default

    async def update_guild_config(self, guild_id: int, **kwargs):
        if not kwargs:
            return
        fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values())
        values.append(guild_id)
        await self.get_guild_config(guild_id)
        query = f"UPDATE guild_config SET {fields} WHERE guild_id = ?"
        await self.conn.execute(query, values)
        await self.conn.commit()

    async def get_prefix(self, guild_id: Optional[int]) -> str:
        if not guild_id:
            return "?"
        cfg = await self.get_guild_config(guild_id)
        return cfg.get("prefix", "?") or "?"

    async def set_prefix(self, guild_id: int, prefix: str):
        await self.update_guild_config(guild_id, prefix=prefix)

    async def get_antibot_status(self, guild_id: int) -> bool:
        """Returns True if Anti-Bot protection is enabled."""
        cfg = await self.get_guild_config(guild_id)
        return bool(cfg.get("antibot_enabled", False))

    async def set_antibot_status(self, guild_id: int, enabled: bool):
        """Arms or disarms Anti-Bot protection."""
        await self.update_guild_config(guild_id, antibot_enabled=enabled)

    # --- Extra Owner Methods ---
    async def is_extra_owner(self, guild_id: int, user_id: int) -> bool:
        async with self.conn.execute(
            "SELECT 1 FROM extraowners WHERE guild_id = ? AND owner_id = ?",
            (guild_id, user_id)
        ) as cursor:
            return await cursor.fetchone() is not None

    async def add_extra_owner(self, guild_id: int, user_id: int) -> bool:
        try:
            await self.conn.execute(
                "INSERT INTO extraowners (guild_id, owner_id) VALUES (?, ?)",
                (guild_id, user_id)
            )
            await self.conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def remove_extra_owner(self, guild_id: int, user_id: int) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM extraowners WHERE guild_id = ? AND owner_id = ?",
            (guild_id, user_id)
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def get_extra_owners(self, guild_id: int) -> List[int]:
        async with self.conn.execute(
            "SELECT owner_id FROM extraowners WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row["owner_id"] for row in rows]

    async def reset_extra_owners(self, guild_id: int):
        await self.conn.execute("DELETE FROM extraowners WHERE guild_id = ?", (guild_id,))
        await self.conn.commit()

    # --- Zero-Trust Whitelist Entity & Scope Methods ---
    async def add_whitelist_entity(
        self,
        guild_id: int,
        entity_id: int,
        entity_type: str,
        scopes: List[str],
        created_by: int,
        target_id: Optional[int] = None,
        expires_at: Optional[str] = None,
        is_supreme: bool = False
    ):
        """Adds or updates a whitelisted entity (user or role) with granular scopes."""
        now_str = datetime.datetime.utcnow().isoformat()
        t_id = target_id if target_id else 0

        # Insert or update entity header
        await self.conn.execute(
            """
            INSERT INTO whitelist_entities (guild_id, entity_id, entity_type, is_legacy_supreme, created_at, created_by)
            VALUES (?, ?, ?, FALSE, ?, ?)
            ON CONFLICT(guild_id, entity_id) DO UPDATE SET entity_type = excluded.entity_type
            """,
            (guild_id, entity_id, entity_type, now_str, created_by)
        )

        # Insert scopes
        for scope in scopes:
            await self.conn.execute(
                """
                INSERT OR REPLACE INTO whitelist_scopes (guild_id, entity_id, scope, target_id, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (guild_id, entity_id, scope, t_id, expires_at)
            )

        await self.conn.commit()

    async def remove_whitelist_entity(self, guild_id: int, entity_id: int) -> bool:
        """Removes a user or role completely from the whitelist."""
        cursor = await self.conn.execute(
            "DELETE FROM whitelist_entities WHERE guild_id = ? AND entity_id = ?",
            (guild_id, entity_id)
        )
        await self.conn.execute(
            "DELETE FROM whitelist_scopes WHERE guild_id = ? AND entity_id = ?",
            (guild_id, entity_id)
        )
        # Also clean up legacy table if present
        await self.conn.execute(
            "DELETE FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
            (guild_id, entity_id)
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def remove_whitelist_scope(self, guild_id: int, entity_id: int, scope: str, target_id: Optional[int] = None) -> bool:
        t_id = target_id if target_id else 0
        cursor = await self.conn.execute(
            "DELETE FROM whitelist_scopes WHERE guild_id = ? AND entity_id = ? AND scope = ? AND target_id = ?",
            (guild_id, entity_id, scope, t_id)
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def get_whitelist_entity(self, guild_id: int, entity_id: int) -> Optional[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM whitelist_entities WHERE guild_id = ? AND entity_id = ?",
            (guild_id, entity_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_entity_scopes(self, guild_id: int, entity_id: int) -> List[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM whitelist_scopes WHERE guild_id = ? AND entity_id = ?",
            (guild_id, entity_id)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_all_whitelist_entities(self, guild_id: int) -> List[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM whitelist_entities WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def reset_whitelist(self, guild_id: int):
        await self.conn.execute("DELETE FROM whitelist_entities WHERE guild_id = ?", (guild_id,))
        await self.conn.execute("DELETE FROM whitelist_scopes WHERE guild_id = ?", (guild_id,))
        await self.conn.execute("DELETE FROM whitelisted_users WHERE guild_id = ?", (guild_id,))
        await self.conn.commit()

    async def has_scope(
        self,
        guild_id: int,
        member: Any,
        required_scope: str,
        target_id: Optional[int] = None
    ) -> bool:
        """
        Evaluates whether a member possesses a required scope directly or via roles.
        Validates target-binding and expiration.
        """
        # Bot owners / global developers check
        global_owners = {1478730719571349545, 1509545584317562970}
        if member.id in global_owners:
            return True

        # Server owner always has full scope
        if hasattr(member, "guild") and member.guild and member.id == member.guild.owner_id:
            return True

        # Extra owners hold all operational + admin scopes
        if await self.is_extra_owner(guild_id, member.id):
            return True

        # Collect candidate entity IDs (User ID + Role IDs)
        candidate_ids = [member.id]
        if hasattr(member, "roles"):
            for r in member.roles:
                candidate_ids.append(r.id)

        now_str = datetime.datetime.utcnow().isoformat()
        t_id = target_id if target_id else 0

        # Query all active scopes for candidate IDs
        placeholders = ", ".join(["?"] * len(candidate_ids))
        query = f"""
        SELECT scope, target_id, expires_at 
        FROM whitelist_scopes 
        WHERE guild_id = ? AND entity_id IN ({placeholders})
        """
        params = [guild_id] + candidate_ids

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                scope = row["scope"]
                target = row["target_id"]
                expires_at = row["expires_at"]

                # Check expiration
                if expires_at and expires_at < now_str:
                    continue

                # Check scope match (support exact match or automod.bypass.all)
                matches_scope = (scope == required_scope)
                if not matches_scope and required_scope.startswith("automod.bypass.") and scope == "automod.bypass.all":
                    matches_scope = True

                if matches_scope:
                    # Check target binding: global (target == 0) or exact target match
                    if target == 0 or target == t_id:
                        return True

        return False

    async def is_whitelisted(self, guild_id: int, user_id: int, action: Optional[str] = None) -> bool:
        """Backward-compatible helper checking if user has any active whitelist entry."""
        async with self.conn.execute(
            "SELECT 1 FROM whitelist_entities WHERE guild_id = ? AND entity_id = ?",
            (guild_id, user_id)
        ) as cursor:
            if await cursor.fetchone():
                return True

        # Fallback to legacy table if not migrated
        async with self.conn.execute(
            "SELECT 1 FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        ) as cursor:
            return await cursor.fetchone() is not None

    # --- Security Audit Trail Methods ---
    async def log_security_audit(
        self,
        guild_id: int,
        actor_id: int,
        action_type: str,
        scope_required: str,
        target_id: Optional[int],
        outcome: str,
        incident_id: Optional[str] = None,
        details: Optional[str] = None
    ):
        """Logs an event to the security audit trail."""
        timestamp = datetime.datetime.utcnow().isoformat()
        await self.conn.execute(
            """
            INSERT INTO security_audit_events 
            (guild_id, actor_id, action_type, scope_required, target_id, outcome, incident_id, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (guild_id, actor_id, action_type, scope_required, target_id, outcome, incident_id, details, timestamp)
        )
        await self.conn.commit()

    async def get_security_audit_logs(self, guild_id: int, limit: int = 25) -> List[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM security_audit_events WHERE guild_id = ? ORDER BY event_id DESC LIMIT ?",
            (guild_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # --- AutoMod Rule Methods ---
    async def get_automod_rule(self, guild_id: int, rule_name: str) -> Dict[str, Any]:
        async with self.conn.execute(
            "SELECT * FROM automod_rules WHERE guild_id = ? AND rule_name = ?",
            (guild_id, rule_name)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
        # Default rule
        default = {
            "guild_id": guild_id,
            "rule_name": rule_name,
            "enabled": True,
            "punishment": "delete",
            "timeout_duration": 300,
            "threshold": 5
        }
        await self.conn.execute(
            """
            INSERT OR IGNORE INTO automod_rules (guild_id, rule_name, enabled, punishment, timeout_duration, threshold)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (guild_id, rule_name, True, "delete", 300, 5)
        )
        await self.conn.commit()
        return default

    async def update_automod_rule(self, guild_id: int, rule_name: str, **kwargs):
        await self.get_automod_rule(guild_id, rule_name)
        fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [guild_id, rule_name]
        query = f"UPDATE automod_rules SET {fields} WHERE guild_id = ? AND rule_name = ?"
        await self.conn.execute(query, values)
        await self.conn.commit()

    async def get_all_automod_rules(self, guild_id: int) -> List[Dict[str, Any]]:
        default_rules = ["spam", "invite", "link", "badwords", "caps", "mention", "emoji"]
        for r in default_rules:
            await self.get_automod_rule(guild_id, r)
        async with self.conn.execute(
            "SELECT * FROM automod_rules WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # --- AutoMod Ignored Methods ---
    async def add_automod_ignored(self, guild_id: int, target_id: int, target_type: str) -> bool:
        try:
            await self.conn.execute(
                "INSERT INTO automod_ignored (guild_id, target_id, target_type) VALUES (?, ?, ?)",
                (guild_id, target_id, target_type)
            )
            await self.conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def remove_automod_ignored(self, guild_id: int, target_id: int, target_type: str) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM automod_ignored WHERE guild_id = ? AND target_id = ? AND target_type = ?",
            (guild_id, target_id, target_type)
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def is_automod_ignored(self, guild_id: int, target_id: int, target_type: str) -> bool:
        async with self.conn.execute(
            "SELECT 1 FROM automod_ignored WHERE guild_id = ? AND target_id = ? AND target_type = ?",
            (guild_id, target_id, target_type)
        ) as cursor:
            return await cursor.fetchone() is not None

    async def get_all_automod_ignored(self, guild_id: int) -> List[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM automod_ignored WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # --- Bad Words Methods ---
    async def add_badword(self, guild_id: int, word: str) -> bool:
        try:
            await self.conn.execute(
                "INSERT INTO badwords (guild_id, word) VALUES (?, ?)",
                (guild_id, word.lower())
            )
            await self.conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def remove_badword(self, guild_id: int, word: str) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM badwords WHERE guild_id = ? AND word = ?",
            (guild_id, word.lower())
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def get_badwords(self, guild_id: int) -> List[str]:
        async with self.conn.execute(
            "SELECT word FROM badwords WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row["word"] for row in rows]

    async def clear_badwords(self, guild_id: int):
        await self.conn.execute("DELETE FROM badwords WHERE guild_id = ?", (guild_id,))
        await self.conn.commit()

    # --- Moderation Case Methods ---
    async def get_next_case_id(self, guild_id: int) -> int:
        async with self.conn.execute(
            "SELECT MAX(case_id) as max_id FROM moderation_cases WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row["max_id"]:
                return row["max_id"] + 1
            return 1

    async def create_case(
        self,
        guild_id: int,
        action: str,
        target_id: int,
        target_name: str,
        moderator_id: int,
        moderator_name: str,
        reason: Optional[str] = "No reason provided"
    ) -> int:
        case_id = await self.get_next_case_id(guild_id)
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        await self.conn.execute(
            """
            INSERT INTO moderation_cases 
            (guild_id, case_id, action, target_id, target_name, moderator_id, moderator_name, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (guild_id, case_id, action.upper(), target_id, target_name, moderator_id, moderator_name, reason, now)
        )
        await self.conn.commit()
        return case_id

    async def get_case(self, guild_id: int, case_id: int) -> Optional[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM moderation_cases WHERE guild_id = ? AND case_id = ?",
            (guild_id, case_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_user_cases(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM moderation_cases WHERE guild_id = ? AND target_id = ? ORDER BY case_id DESC",
            (guild_id, user_id)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # --- User Warnings Methods ---
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        cursor = await self.conn.execute(
            """
            INSERT INTO user_warnings (guild_id, user_id, moderator_id, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (guild_id, user_id, moderator_id, reason, now)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_warnings(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM user_warnings WHERE guild_id = ? AND user_id = ? ORDER BY warn_id DESC",
            (guild_id, user_id)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def clear_warning(self, guild_id: int, warn_id: int) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM user_warnings WHERE guild_id = ? AND warn_id = ?",
            (guild_id, warn_id)
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def clear_all_warnings(self, guild_id: int, user_id: int) -> int:
        cursor = await self.conn.execute(
            "DELETE FROM user_warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        await self.conn.commit()
        return cursor.rowcount

    # --- Emergency Channel Methods ---
    async def save_emergency_channels(self, guild_id: int, channel_ids: List[int]):
        await self.clear_emergency_channels(guild_id)
        for cid in channel_ids:
            await self.conn.execute(
                "INSERT INTO emergency_channels (guild_id, channel_id) VALUES (?, ?)",
                (guild_id, cid)
            )
        await self.conn.commit()

    async def get_emergency_channels(self, guild_id: int) -> List[int]:
        async with self.conn.execute(
            "SELECT channel_id FROM emergency_channels WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row["channel_id"] for row in rows]

    async def clear_emergency_channels(self, guild_id: int):
        await self.conn.execute("DELETE FROM emergency_channels WHERE guild_id = ?", (guild_id,))
        await self.conn.commit()

    # --- Channel Layout Snapshot Methods ---
    async def save_channel_snapshot(
        self,
        guild_id: int,
        channel_id: int,
        name: str,
        channel_type: str,
        category_name: Optional[str],
        category_id: Optional[int],
        position: int,
        topic: Optional[str],
        nsfw: bool,
        slowmode_delay: int,
        overwrites_json: str
    ):
        query = """
        INSERT OR REPLACE INTO channel_snapshots 
        (guild_id, channel_id, name, channel_type, category_name, category_id, position, topic, nsfw, slowmode_delay, overwrites_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.conn.execute(
            query,
            (guild_id, channel_id, name, channel_type, category_name, category_id, position, topic, nsfw, slowmode_delay, overwrites_json)
        )
        await self.conn.commit()

    async def get_channel_snapshot(self, guild_id: int, channel_id: int) -> Optional[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM channel_snapshots WHERE guild_id = ? AND channel_id = ?",
            (guild_id, channel_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_channel_snapshots(self, guild_id: int) -> List[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM channel_snapshots WHERE guild_id = ? ORDER BY position ASC",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def delete_channel_snapshot(self, guild_id: int, channel_id: int):
        await self.conn.execute(
            "DELETE FROM channel_snapshots WHERE guild_id = ? AND channel_id = ?",
            (guild_id, channel_id)
        )
        await self.conn.commit()

    # --- Role Layout Snapshot Methods ---
    async def save_role_snapshot(
        self,
        guild_id: int,
        role_id: int,
        name: str,
        permissions: int,
        color: int,
        hoist: bool,
        mentionable: bool,
        position: int
    ):
        query = """
        INSERT OR REPLACE INTO role_snapshots 
        (guild_id, role_id, name, permissions, color, hoist, mentionable, position)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.conn.execute(
            query,
            (guild_id, role_id, name, permissions, color, hoist, mentionable, position)
        )
        await self.conn.commit()

    async def get_role_snapshot(self, guild_id: int, role_id: int) -> Optional[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM role_snapshots WHERE guild_id = ? AND role_id = ?",
            (guild_id, role_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_role_snapshots(self, guild_id: int) -> List[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM role_snapshots WHERE guild_id = ? ORDER BY position ASC",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def delete_role_snapshot(self, guild_id: int, role_id: int):
        await self.conn.execute(
            "DELETE FROM role_snapshots WHERE guild_id = ? AND role_id = ?",
            (guild_id, role_id)
        )
        await self.conn.commit()

    # --- Guild Settings, Emoji & Member Role Snapshots ---
    async def save_guild_snapshot(
        self,
        guild_id: int,
        name: str,
        description: Optional[str],
        afk_timeout: int,
        afk_channel_id: Optional[int],
        system_channel_id: Optional[int],
        rules_channel_id: Optional[int],
        verification_level: str,
        default_notifications: str,
        vanity_code: Optional[str]
    ):
        now_str = datetime.datetime.utcnow().isoformat()
        query = """
        INSERT OR REPLACE INTO guild_snapshots
        (guild_id, name, description, afk_timeout, afk_channel_id, system_channel_id, rules_channel_id, verification_level, default_notifications, vanity_code, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.conn.execute(
            query,
            (guild_id, name, description, afk_timeout, afk_channel_id, system_channel_id, rules_channel_id, str(verification_level), str(default_notifications), vanity_code, now_str)
        )
        await self.conn.commit()

    async def get_guild_snapshot(self, guild_id: int) -> Optional[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM guild_snapshots WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def save_emoji_snapshot(
        self,
        guild_id: int,
        emoji_id: int,
        name: str,
        animated: bool,
        url: str,
        roles_json: str
    ):
        query = """
        INSERT OR REPLACE INTO emoji_snapshots
        (guild_id, emoji_id, name, animated, url, roles_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        await self.conn.execute(query, (guild_id, emoji_id, name, animated, url, roles_json))
        await self.conn.commit()

    async def get_all_emoji_snapshots(self, guild_id: int) -> List[Dict[str, Any]]:
        async with self.conn.execute(
            "SELECT * FROM emoji_snapshots WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def save_member_role_snapshot(self, guild_id: int, user_id: int, role_ids: List[int]):
        now_str = datetime.datetime.utcnow().isoformat()
        query = """
        INSERT OR REPLACE INTO member_role_snapshots (guild_id, user_id, role_ids_json, timestamp)
        VALUES (?, ?, ?, ?)
        """
        await self.conn.execute(query, (guild_id, user_id, json.dumps(role_ids), now_str))
        await self.conn.commit()

    async def get_member_role_snapshot(self, guild_id: int, user_id: int) -> Optional[List[int]]:
        async with self.conn.execute(
            "SELECT role_ids_json FROM member_role_snapshots WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row["role_ids_json"]:
                return json.loads(row["role_ids_json"])
            return None
