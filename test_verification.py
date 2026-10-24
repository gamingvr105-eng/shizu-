import asyncio
import os
import sys
import py_compile
import unittest
import datetime

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath("."))

def compile_all_files():
    print("=" * 60)
    print("STEP 1: Compiling all Python source files...")
    print("=" * 60)
    total = 0
    errors = 0
    for root, dirs, files in os.walk("."):
        if any(skip in root for skip in ["_source_extracted", "_olympus_ref", ".git", "__pycache__"]):
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                total += 1
                try:
                    py_compile.compile(path, doraise=True)
                    print(f"  [OK] {path}")
                except Exception as e:
                    print(f"  [FAIL] {path}: {e}")
                    errors += 1
    print(f"\nCompilation complete: {total - errors}/{total} passed (Errors: {errors})\n")
    if errors > 0:
        raise RuntimeError(f"Syntax/Compilation errors found in {errors} file(s).")

async def test_database_and_cogs():
    print("=" * 60)
    print("STEP 2: Verifying Zero-Trust Database & Scope Engine...")
    print("=" * 60)
    from core.database import Database
    from core.enforcement import burst_tracker
    from core.scopes import ALL_OPERATIONAL_SCOPES

    test_db_path = "database/test_verification.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = Database(test_db_path)
    await db.connect()
    print("  [OK] Zero-Trust Database connected and schema created.")

    # Test Guild Config
    cfg = await db.get_guild_config(123456789)
    assert cfg["prefix"] == "?", "Default prefix mismatch"
    assert cfg["antinuke_enabled"] == False, "Default antinuke state mismatch"
    print("  [OK] Default guild config retrieved.")

    # Test Zero-Trust Additive Scopes
    await db.add_whitelist_entity(
        guild_id=123456789,
        entity_id=987654321,
        entity_type="user",
        scopes=["antinuke.channel.delete", "automod.bypass.all"],
        created_by=111111111,
        target_id=None,
        expires_at=None
    )
    scopes = await db.get_entity_scopes(123456789, 987654321)
    assert len(scopes) == 2, "Scope grant count mismatch"
    print("  [OK] Granular additive scope storage verified.")

    # Test Member scope check mock
    class MockMember:
        def __init__(self, uid):
            self.id = uid
            self.roles = []
            self.guild = None

    m = MockMember(987654321)
    has_ch = await db.has_scope(123456789, m, "antinuke.channel.delete")
    has_role = await db.has_scope(123456789, m, "antinuke.role.delete")
    has_automod = await db.has_scope(123456789, m, "automod.bypass.spam")
    assert has_ch == True, "Failed to resolve granted channel delete scope"
    assert has_role == False, "Resolved ungranted role delete scope (Default Deny violated)"
    assert has_automod == True, "Failed to resolve automod.bypass.all for spam"
    print("  [OK] Scope resolver (has_scope) and Default-Deny verified.")

    # Test Fixed Sliding-Window Burst Tracker
    burst_tracker.reset(123456789, 987654321)
    b1 = burst_tracker.record_and_check(123456789, 987654321) # 1st
    b2 = burst_tracker.record_and_check(123456789, 987654321) # 2nd
    b3 = burst_tracker.record_and_check(123456789, 987654321) # 3rd
    assert b1 == False and b2 == False and b3 == False, "Early burst trigger false positive"
    b4 = burst_tracker.record_and_check(123456789, 987654321) # 4th (breach!)
    assert b4 == True, "Burst limit did not trigger on 4th destructive action"
    print("  [OK] Fixed burst limit engine verified (3 actions in 10s).")

    # Test Bad Words
    await db.add_badword(123456789, "toxicterm")
    bw = await db.get_badwords(123456789)
    assert "toxicterm" in bw, "Badword storage failed"
    print("  [OK] Word-boundary blacklist storage verified.")

    # Test Case Tracking
    c_id = await db.create_case(123456789, "BAN", 555, "Target#0001", 666, "Mod#0001", "Breach Protocol")
    assert c_id == 1, "Case ID generation mismatch"
    print("  [OK] Disciplinary case ledger verified.")

    await db.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("=" * 60)
    print("STEP 3: Verifying Bot Extension Loading & Command Registration...")
    print("=" * 60)
    from core.bot import ShizuSecurity, COGS
    import config

    bot = ShizuSecurity()
    await bot.db.connect()

    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"  [OK] Loaded extension: {cog}")
        except Exception as e:
            print(f"  [FAIL] Failed loading {cog}: {e}")
            raise e

    registered_cmds = [cmd.name for cmd in bot.commands]
    print(f"\nTotal Registered Top-Level Commands ({len(registered_cmds)}):")
    print("  " + ", ".join(sorted(registered_cmds)))

    required_cmds = [
        "antinuke", "whitelist", "extraowner", "lockdown", "unlockdown", "backup", "restore",
        "automod", "badwords", "setlog",
        "ban", "unban", "kick", "timeout", "untimeout", "warn", "purge",
        "slowmode", "lock", "unlock", "hide", "unhide", "setnick", "role", "snipe",
        "security", "case", "modlogs", "warnings", "clearwarns",
        "stats", "ping", "setprefix", "topcheck", "help"
    ]
    for req in required_cmds:
        assert req in registered_cmds, f"Critical command '{req}' missing from bot registration!"
    print(f"  [PASS] All {len(required_cmds)} critical commands registered cleanly!")

    await bot.db.close()
    print("\n=" * 60)
    print("ALL TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    compile_all_files()
    asyncio.run(test_database_and_cogs())
