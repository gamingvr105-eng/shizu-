import os
import sys
import pymupdf
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' on all pages."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 755, "SHIZU SECURITY v2.3.0")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(138, 755, "• Professional Logging Architecture & Trigger Specification")
            self.drawRightString(576, 755, "Official Verification Preview")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(36, 747, 576, 747)
            
        # Footer (All Pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(36, 42, 576, 42)
        
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#0F172A"))
        self.drawString(36, 30, "SHIZU SECURITY")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(110, 30, "| Developers: VIPER & PRASHU | Owners: 1478730719571349545, 1509545584317562970")
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 30, page_text)
        
        self.restoreState()

def build_pdf(filename="Shizu_Security_Logging_Preview.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    DARK_TEXT = colors.HexColor("#0F172A")
    MUTED_TEXT = colors.HexColor("#475569")
    LIGHT_BG = colors.HexColor("#F8FAFC")
    BORDER_COLOR = colors.HexColor("#E2E8F0")
    DISCORD_BG = colors.HexColor("#1E1F22")
    DISCORD_EMBED = colors.HexColor("#2B2D31")
    DISCORD_TEXT = colors.HexColor("#DBDEE1")
    DISCORD_MUTED = colors.HexColor("#949BA4")
    RED_ACCENT = colors.HexColor("#DC2626")
    AMBER_ACCENT = colors.HexColor("#D97706")
    GREEN_ACCENT = colors.HexColor("#059669")
    BLUE_ACCENT = colors.HexColor("#2563EB")
    CODE_BG = colors.HexColor("#111827")

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=DARK_TEXT,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=MUTED_TEXT,
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=DARK_TEXT,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=DARK_TEXT,
        spaceBefore=6,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=DARK_TEXT,
        spaceAfter=5
    )
    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=DARK_TEXT
    )
    discord_title = ParagraphStyle(
        "DiscordTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    discord_body = ParagraphStyle(
        "DiscordBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=DISCORD_TEXT
    )
    discord_muted = ParagraphStyle(
        "DiscordMuted",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9.5,
        textColor=DISCORD_MUTED
    )
    discord_code = ParagraphStyle(
        "DiscordCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor("#A5F3FC")
    )
    th_style = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=DARK_TEXT
    )
    td_style = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9.5,
        textColor=DARK_TEXT
    )
    td_code = ParagraphStyle(
        "TDCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # =========================================================================
    # PAGE 1: COVER & ARCHITECTURAL SPECIFICATION
    # =========================================================================
    story.append(Paragraph("SHIZU SECURITY — LOGGING & TRIGGER SPECIFICATION", title_style))
    story.append(Paragraph(
        "<b>Version 2.3.0</b> • High-End Security & Moderation Logging Architecture • Direct Ban & Hierarchy Revert Matrix<br/>"
        "Engineered for Server Protection • Developed by <b>VIPER & PRASHU</b>",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceAfter=8))

    # Architectural Overview Box
    overview_html = (
        "<b>EXECUTIVE SUMMARY & CORE LOGGING POLICY</b><br/>"
        "Shizu Security v2.3.0 streamlines all security operations into a direct, predictable, and zero-clutter paradigm:<br/>"
        "• <b>Zero-Tolerance Anti-Nuke:</b> Unwhitelisted actors triggering any destructive action are <b>banned immediately</b> upon audit log identification.<br/>"
        "• <b>Whitelist Burst Defense:</b> Whitelisted staff performing rapid destructive actions (&ge; 3 in 10s) are treated as compromised tokens and <b>banned immediately</b>. Single isolated actions issue an immediate <b>warning</b>.<br/>"
        "• <b>Revert on Every Trigger:</b> 100% of destructive actions are automatically reverted back to the pre-incident snapshot.<br/>"
        "• <b>Hierarchy Defense:</b> Even if an offender has a higher role hierarchy than the bot (preventing a Discord ban), Shizu <b>reverts the action regardless</b> and dispatches an emergency escalation alert.<br/>"
        "• <b>Owner Direct Warnings:</b> For <b>EVERY</b> Anti-Nuke action, the Guild Owner receives an urgent Direct Message containing full forensic logs and security status.<br/>"
        "• <b>Clean 2-Channel Routing:</b> Only two dedicated channels: <code>#shizu-security-logs</code> and <code>#shizu-mod-logs</code>."
    )
    ov_table = Table(
        [[Paragraph(overview_html, callout_style)]],
        colWidths=[540]
    )
    ov_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3B82F6")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(ov_table)
    story.append(Spacer(1, 10))

    # Core Enforcement Flowchart Table
    story.append(Paragraph("1. Simplified Anti-Nuke Enforcement Workflow", h1_style))
    flow_data = [
        [
            Paragraph("<b>Trigger Event</b>", th_style),
            Paragraph("<b>Actor Status</b>", th_style),
            Paragraph("<b>Action Enforced</b>", th_style),
            Paragraph("<b>Self-Healing Revert</b>", th_style),
            Paragraph("<b>Owner Alert</b>", th_style)
        ],
        [
            Paragraph("Any Anti-Nuke Vector<br/>(Channel, Role, Webhook, Bot)", td_style),
            Paragraph("<font color='#DC2626'><b>Unwhitelisted</b></font><br/>Regular Member / Rogue Admin", td_style),
            Paragraph("<b>BAN DIRECTLY</b><br/>All permissions revoked immediately", td_style),
            Paragraph("<font color='#059669'><b>100% Revert</b></font><br/>Channel/role cloned, webhook deleted", td_style),
            Paragraph("<b>DM Log + Warn</b><br/>Instant High-Priority notification", td_style)
        ],
        [
            Paragraph("Mass Burst Trigger<br/>(&ge; 3 actions in 10s)", td_style),
            Paragraph("<font color='#D97706'><b>Whitelisted</b></font><br/>Staff member / Compromised token", td_style),
            Paragraph("<b>BAN DIRECTLY</b><br/>Roles stripped + Emergency lockdown", td_style),
            Paragraph("<font color='#059669'><b>100% Revert</b></font><br/>All nuked assets restored from snapshot", td_style),
            Paragraph("<b>DM Log + Warn</b><br/>Urgent Token Hijack escalation", td_style)
        ],
        [
            Paragraph("Isolated Action<br/>(1 action in 10s)", td_style),
            Paragraph("<font color='#059669'><b>Whitelisted</b></font><br/>Staff member accidental click", td_style),
            Paragraph("<b>WARN USER</b><br/>No ban issued, logged to security", td_style),
            Paragraph("<font color='#059669'><b>100% Revert</b></font><br/>Sensitive change reversed to protect guild", td_style),
            Paragraph("<b>DM Log + Warn</b><br/>Routine security warning to owner", td_style)
        ],
        [
            Paragraph("Hierarchy Blocked<br/>(Actor role &ge; Bot role)", td_style),
            Paragraph("<font color='#7C3AED'><b>Any Unwhitelisted</b></font><br/>Server Co-Owner / Higher Role", td_style),
            Paragraph("<b>FAILOVER TO REVERT</b><br/>Ban fails due to Discord API 403", td_style),
            Paragraph("<font color='#059669'><b>100% Revert</b></font><br/>Channel/role recreated without actor perms", td_style),
            Paragraph("<b>DM ESCALATION</b><br/>Urgent: Manual owner action required", td_style)
        ]
    ]
    t_flow = Table(flow_data, colWidths=[110, 100, 115, 115, 100])
    t_flow.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 10))

    # Hierarchy Explanation Box
    story.append(Paragraph("2. The Discord Bot Hierarchy Defense Mechanism", h1_style))
    hier_html = (
        "<b>HOW SHIZU HANDLES MEMBERS HIGHER IN HIERARCHY THAN THE BOT:</b><br/>"
        "In the Discord API, a bot cannot ban, kick, or modify roles of members whose highest role is equal to or higher than the bot's highest role, or the server owner.<br/>"
        "<b>The Shizu Defense Solution:</b><br/>"
        "1. <b>Reverts are independent of Actor Hierarchy:</b> Re-creating deleted channels, restoring deleted roles, purging unauthorized webhooks, and unbanning victims do <i>not</i> require hierarchy over the actor—they only require bot channel/guild permissions.<br/>"
        "2. <b>Instant Self-Healing:</b> The moment an unwhitelisted superior member nukes an asset, Shizu instantly restores it to pre-incident state.<br/>"
        "3. <b>Immediate Owner Escalation:</b> Shizu immediately alerts the Server Owner via DM with an <code>[EMERGENCY HIERARCHY ESCALATION]</code> notifying them that Shizu successfully healed the damage, but the offending user must be demoted or banned manually."
    )
    t_hier = Table([[Paragraph(hier_html, callout_style)]], colWidths=[540])
    t_hier.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ("BOX", (0, 0), (-1, -1), 1, RED_ACCENT),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_hier)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: COMPLETE TRIGGER CATALOG & REVERT MATRIX
    # =========================================================================
    story.append(Paragraph("3. Complete Anti-Nuke Triggers & Revert Matrix", h1_style))
    story.append(Paragraph(
        "Every destructive action on the server is intercepted by an event listener, correlated against the Discord Audit Log within 0.12s, and reverted.",
        body_style
    ))

    antinuke_data = [
        [
            Paragraph("<b>Trigger Vector</b>", th_style),
            Paragraph("<b>Audit Action</b>", th_style),
            Paragraph("<b>Detection & Enforcement Mechanism</b>", th_style),
            Paragraph("<b>Automated Revert Execution</b>", th_style)
        ],
        [
            Paragraph("<b>Anti-Channel Delete</b>", td_style),
            Paragraph("<code>CHANNEL_DELETE</code>", td_code),
            Paragraph("Fires when any channel is deleted. Identifies actor; bans unwhitelisted or warns isolated whitelisted.", td_style),
            Paragraph("<b>Instant Re-Creation:</b> Clones name, topic, category, NSFW, bitrate, slowmode, and explicit perms.", td_style)
        ],
        [
            Paragraph("<b>Anti-Channel Create</b>", td_style),
            Paragraph("<code>CHANNEL_CREATE</code>", td_code),
            Paragraph("Detects unauthorized rogue channels created during a raid or mass spam attack.", td_style),
            Paragraph("<b>Instant Deletion:</b> Rogue channel is deleted immediately from guild.", td_style)
        ],
        [
            Paragraph("<b>Anti-Channel Update</b>", td_style),
            Paragraph("<code>CHANNEL_UPDATE</code>", td_code),
            Paragraph("Detects unauthorized permission overrides (e.g. hiding channels or opening hidden channels).", td_style),
            Paragraph("<b>Permissions Restored:</b> Reverts all permission overwrites back to snapshot state.", td_style)
        ],
        [
            Paragraph("<b>Anti-Role Delete</b>", td_style),
            Paragraph("<code>ROLE_DELETE</code>", td_code),
            Paragraph("Detects role deletion. Banned directly if unwhitelisted; token burst defense applies.", td_style),
            Paragraph("<b>Instant Role Re-Creation:</b> Clones name, color, hoist, mentionable flag, and exact permissions.", td_style)
        ],
        [
            Paragraph("<b>Anti-Role Create</b>", td_style),
            Paragraph("<code>ROLE_CREATE</code>", td_code),
            Paragraph("Detects rogue roles created by malicious admins.", td_style),
            Paragraph("<b>Instant Deletion:</b> Rogue role is purged immediately.", td_style)
        ],
        [
            Paragraph("<b>Anti-Dangerous Perms</b>", td_style),
            Paragraph("<code>ROLE_UPDATE</code>", td_code),
            Paragraph("Fires if a role is granted Administrator, Ban Members, Manage Guild, or Manage Roles.", td_style),
            Paragraph("<b>Perms Stripped:</b> Strips dangerous permissions immediately to prevent privilege escalation.", td_style)
        ],
        [
            Paragraph("<b>Anti-Dangerous Role Assign</b>", td_style),
            Paragraph("<code>MEMBER_UPDATE</code>", td_code),
            Paragraph("Fires if an admin assigns an admin/whitelisted role to an unauthorized member.", td_style),
            Paragraph("<b>Role Revoked:</b> Automatically strips the role from recipient user.", td_style)
        ],
        [
            Paragraph("<b>Anti-Member Ban</b>", td_style),
            Paragraph("<code>MEMBER_BAN_ADD</code>", td_code),
            Paragraph("Intercepts unauthorized bans executed by rogue staff or hacked bots.", td_style),
            Paragraph("<b>Instant Unban:</b> Victim is automatically unbanned; rogue admin is banned.", td_style)
        ],
        [
            Paragraph("<b>Anti-Member Kick</b>", td_style),
            Paragraph("<code>MEMBER_KICK</code>", td_code),
            Paragraph("Intercepts rogue member kicks. Rogue actor is banned immediately.", td_style),
            Paragraph("<b>Alert + Invite:</b> Discord API cannot force-join members; alert + recovery invite logged.", td_style)
        ],
        [
            Paragraph("<b>Anti-Bot Add</b>", td_style),
            Paragraph("<code>BOT_ADD</code>", td_code),
            Paragraph("Fires when an unauthorized bot is invited to the guild without Supreme authority.", td_style),
            Paragraph("<b>Instant Kick:</b> Rogue bot kicked immediately; user who invited bot is banned.", td_style)
        ],
        [
            Paragraph("<b>Anti-Webhook Inject</b>", td_style),
            Paragraph("<code>WEBHOOK_CREATE</code>", td_code),
            Paragraph("Detects webhook creation used for mass web-nuke raids.", td_style),
            Paragraph("<b>Instant Deletion:</b> Rogue webhook purged immediately; creator banned.", td_style)
        ],
        [
            Paragraph("<b>Anti-Server Modify</b>", td_style),
            Paragraph("<code>GUILD_UPDATE</code>", td_code),
            Paragraph("Detects unauthorized server rename, icon deletion, splash nuke, or vanity URL change.", td_style),
            Paragraph("<b>Snapshot Restoration:</b> Restores server name, icon, and settings from DB.", td_style)
        ],
        [
            Paragraph("<b>Anti-Everyone Ping</b>", td_style),
            Paragraph("<code>MASS_MENTION</code>", td_code),
            Paragraph("Detects unauthorized users pinging @everyone or @here across channels.", td_style),
            Paragraph("<b>Message Purged + Muted:</b> Message deleted instantly; actor timed out/banned.", td_style)
        ],
        [
            Paragraph("<b>Anti-Prune</b>", td_style),
            Paragraph("<code>MEMBER_PRUNE</code>", td_code),
            Paragraph("Detects mass member pruning attempted by rogue administrators.", td_style),
            Paragraph("<b>Actor Banned:</b> Rogue actor banned instantly; emergency lockdown engaged.", td_style)
        ]
    ]
    t_an = Table(antinuke_data, colWidths=[110, 85, 175, 170])
    t_an.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_an)
    story.append(Spacer(1, 10))

    # AutoMod Triggers Section
    story.append(Paragraph("4. Complete AutoMod Trigger Specifications", h1_style))
    automod_data = [
        [
            Paragraph("<b>AutoMod Filter</b>", th_style),
            Paragraph("<b>Trigger Condition</b>", th_style),
            Paragraph("<b>Default Threshold</b>", th_style),
            Paragraph("<b>Enforcement & Mitigation</b>", th_style)
        ],
        [
            Paragraph("<b>Anti-Mass Mentions</b>", td_style),
            Paragraph("Excessive user or role mentions in a single message", td_style),
            Paragraph("<code>&gt; 5 mentions</code>", td_code),
            Paragraph("Message deleted • 10-minute timeout • Logged to Security", td_style)
        ],
        [
            Paragraph("<b>Anti-Everyone / Here</b>", td_style),
            Paragraph("Unauthorized use of @everyone or @here in chat", td_style),
            Paragraph("<code>Non-whitelisted</code>", td_code),
            Paragraph("Message deleted • 1-hour timeout • Alert to Owner", td_style)
        ],
        [
            Paragraph("<b>Anti-Spam / Flood</b>", td_style),
            Paragraph("Rapid message burst from single user", td_style),
            Paragraph("<code>5 msgs / 3.0s</code>", td_code),
            Paragraph("Messages purged • 5-minute timeout • Warn issued", td_style)
        ],
        [
            Paragraph("<b>Anti-Links / URLs</b>", td_style),
            Paragraph("HTTP/HTTPS links, phishing domains, IP grabbers", td_style),
            Paragraph("<code>All unwhitelisted</code>", td_code),
            Paragraph("Message deleted • Warn issued • Phishing domains auto-ban", td_style)
        ],
        [
            Paragraph("<b>Anti-Discord Invites</b>", td_style),
            Paragraph("Discord server invite links (discord.gg/*, etc.)", td_style),
            Paragraph("<code>All unwhitelisted</code>", td_code),
            Paragraph("Message deleted • 15-minute timeout • Advert log created", td_style)
        ],
        [
            Paragraph("<b>Anti-Bad Words</b>", td_style),
            Paragraph("Blacklisted profanity, slurs, regex matches", td_style),
            Paragraph("<code>Custom & Global List</code>", td_code),
            Paragraph("Message deleted • Verbal warn • Repeat triggers timeout", td_style)
        ],
        [
            Paragraph("<b>Anti-Caps</b>", td_style),
            Paragraph("Excessive uppercase characters in message", td_style),
            Paragraph("<code>&gt; 70% caps (len &gt; 8)</code>", td_code),
            Paragraph("Message deleted • Gentle rate warning to user", td_style)
        ],
        [
            Paragraph("<b>Anti-Emoji Spam</b>", td_style),
            Paragraph("Mass custom or unicode emojis in message", td_style),
            Paragraph("<code>&gt; 6 emojis / msg</code>", td_code),
            Paragraph("Message deleted • User warned", td_style)
        ],
        [
            Paragraph("<b>Anti-Zalgo Text</b>", td_style),
            Paragraph("Glitched, corrupted Unicode diacritic stacking", td_style),
            Paragraph("<code>Zalgo factor &gt; 0.4</code>", td_code),
            Paragraph("Message purged • User warned to clean font", td_style)
        ],
        [
            Paragraph("<b>Anti-Duplicate Text</b>", td_style),
            Paragraph("Repeating identical message across channels", td_style),
            Paragraph("<code>3 duplicates in 10s</code>", td_code),
            Paragraph("All copies purged • 10-minute timeout", td_style)
        ]
    ]
    t_am = Table(automod_data, colWidths=[110, 150, 110, 170])
    t_am.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_am)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: VISUAL LOGGING SHOWCASE (DISCORD EMBEDS 1 & 2)
    # =========================================================================
    story.append(Paragraph("5. Visual Logging Preview — #shizu-security-logs", h1_style))
    story.append(Paragraph(
        "Rendered directly with Shizu's obsidian dark palette (<code>#1E1F22</code> / <code>#2B2D31</code>), clear status badges, and forensic details.",
        body_style
    ))

    # Embed 1: Unwhitelisted Direct Ban
    embed1_content = [
        [
            Paragraph("<font color='#DC2626'><b>🚨 SHIZU ANTI-NUKE PROTECTION</b></font>", discord_title),
            Paragraph("<font color='#949BA4'><b>#shizu-security-logs • 10:55 AM</b></font>", discord_muted)
        ],
        [
            Paragraph("<b>Unauthorized Channel Deletion Intercepted</b><br/>"
                      "<font color='#DBDEE1'>An unauthorized administrator attempted to delete a server channel. Shizu Security intervened immediately.</font>", discord_body),
            Paragraph("", discord_body)
        ],
        [
            Paragraph("<b>👤 OFFENDER</b><br/>@RogueAdmin<br/><font color='#949BA4'>ID: 109876543210987654</font>", discord_body),
            Paragraph("<b>🛡️ WHITELIST STATUS</b><br/><font color='#DC2626'><b>❌ Unwhitelisted (No Bypass)</b></font><br/><font color='#949BA4'>Zero-Tolerance Enforcement</font>", discord_body)
        ],
        [
            Paragraph("<b>⚡ ACTION ENFORCED</b><br/><font color='#DC2626'><b>🔨 Permanently Banned</b></font><br/><font color='#059669'>Roles & permissions revoked</font>", discord_body),
            Paragraph("<b>🔄 SELF-HEALING STATUS</b><br/><font color='#059669'><b>✅ Channel Restored</b></font><br/><font color='#949BA4'>Cloned exact permissions & category</font>", discord_body)
        ],
        [
            Paragraph("<b>📋 TECHNICAL AUDIT DETAILS</b><br/>"
                      "• Target Channel: <code>#announcements (ID: 123456789012345)</code><br/>"
                      "• Audit Log Entry: <code>ID 134567890123456 (CHANNEL_DELETE)</code><br/>"
                      "• Owner DM Alert: <font color='#059669'>Delivered successfully to @ServerOwner</font>", discord_code),
            Paragraph("", discord_body)
        ],
        [
            Paragraph("<font color='#949BA4'>🔴 Shizu Security v2.3.0 • Automated Defense • 10:55:12 AM</font>", discord_muted),
            Paragraph("", discord_body)
        ]
    ]
    t_emb1 = Table(embed1_content, colWidths=[270, 250])
    t_emb1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DISCORD_BG),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#35373C")),
        ("LINEBEFORE", (0, 0), (0, -1), 4, RED_ACCENT),
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (0, 4), (1, 4)),
        ("SPAN", (0, 5), (1, 5)),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_emb1)
    story.append(Spacer(1, 10))

    # Embed 2: Whitelisted Burst Mass-Trigger Ban
    embed2_content = [
        [
            Paragraph("<font color='#D97706'><b>🚨 WHITELIST BURST THREAT INTERCEPTED</b></font>", discord_title),
            Paragraph("<font color='#949BA4'><b>#shizu-security-logs • 10:56 AM</b></font>", discord_muted)
        ],
        [
            Paragraph("<b>Compromised Whitelist Account Terminated</b><br/>"
                      "<font color='#DBDEE1'>A whitelisted staff member exceeded the mass-trigger rate limit (3 destructive actions in 10s). Suspected account token hijacking.</font>", discord_body),
            Paragraph("", discord_body)
        ],
        [
            Paragraph("<b>👤 OFFENDER</b><br/>@WhitelistedMod<br/><font color='#949BA4'>ID: 876543210987654321</font>", discord_body),
            Paragraph("<b>🛡️ WHITELIST STATUS</b><br/><font color='#D97706'><b>⚠️ Whitelisted (Burst Exceeded)</b></font><br/><font color='#DC2626'>3 actions within 4.2 seconds</font>", discord_body)
        ],
        [
            Paragraph("<b>⚡ ACTION ENFORCED</b><br/><font color='#DC2626'><b>🔨 Permanently Banned</b></font><br/><font color='#949BA4'>Emergency token defense</font>", discord_body),
            Paragraph("<b>🔄 RECOVERY STATE</b><br/><font color='#059669'><b>✅ 3 Channels Restored</b></font><br/><font color='#949BA4'>All nuked channels recreated</font>", discord_body)
        ],
        [
            Paragraph("<b>📋 THREAT ANALYSIS</b><br/>"
                      "• Triggered Actions: <code>Channel Delete (x3 within 4.2s)</code><br/>"
                      "• Account State: <font color='#DC2626'>Banned & Roles Stripped</font><br/>"
                      "• Owner Direct Alert: <font color='#D97706'>Dispatched with URGENT Priority</font>", discord_code),
            Paragraph("", discord_body)
        ],
        [
            Paragraph("<font color='#949BA4'>🟠 Shizu Security v2.3.0 • Mass-Trigger Defense • 10:56:04 AM</font>", discord_muted),
            Paragraph("", discord_body)
        ]
    ]
    t_emb2 = Table(embed2_content, colWidths=[270, 250])
    t_emb2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DISCORD_BG),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#35373C")),
        ("LINEBEFORE", (0, 0), (0, -1), 4, AMBER_ACCENT),
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (0, 4), (1, 4)),
        ("SPAN", (0, 5), (1, 5)),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_emb2)
    story.append(Spacer(1, 10))

    # Embed 3: Whitelisted Single Action Warn
    embed3_content = [
        [
            Paragraph("<font color='#FBBF24'><b>⚠️ WHITELIST SECURITY NOTICE</b></font>", discord_title),
            Paragraph("<font color='#949BA4'><b>#shizu-security-logs • 10:57 AM</b></font>", discord_muted)
        ],
        [
            Paragraph("<b>Whitelisted User Sensitive Action Detected</b><br/>"
                      "<font color='#DBDEE1'>A whitelisted staff member performed a protected action. Action was reverted and user was warned.</font>", discord_body),
            Paragraph("", discord_body)
        ],
        [
            Paragraph("<b>👤 WHITELISTED USER</b><br/>@TrustedMod<br/><font color='#949BA4'>ID: 554433221100998877</font>", discord_body),
            Paragraph("<b>🛡️ WHITELIST VERIFICATION</b><br/><font color='#059669'><b>✅ Whitelisted (Single Event)</b></font><br/><font color='#949BA4'>No mass-burst detected (1 of 3)</font>", discord_body)
        ],
        [
            Paragraph("<b>⚡ ACTION ENFORCED</b><br/><font color='#FBBF24'><b>⚠️ Warned (No Ban)</b></font><br/><font color='#949BA4'>Action reversed to protect guild</font>", discord_body),
            Paragraph("<b>🔄 PROTECTION ACTION</b><br/><font color='#059669'><b>✅ Webhook Deleted</b></font><br/><font color='#949BA4'>Rogue integration purged</font>", discord_body)
        ],
        [
            Paragraph("<b>📋 EVENT SUMMARY</b><br/>"
                      "• Action Type: <code>Webhook Creation in #staff-chat</code><br/>"
                      "• Webhook Name: <code>SpamHook (ID: 99887766554433)</code><br/>"
                      "• Owner DM Alert: <font color='#FBBF24'>Dispatched with Warning Context</font>", discord_code),
            Paragraph("", discord_body)
        ],
        [
            Paragraph("<font color='#949BA4'>🟡 Shizu Security v2.3.0 • Whitelist Guard • 10:57:30 AM</font>", discord_muted),
            Paragraph("", discord_body)
        ]
    ]
    t_emb3 = Table(embed3_content, colWidths=[270, 250])
    t_emb3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DISCORD_BG),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#35373C")),
        ("LINEBEFORE", (0, 0), (0, -1), 4, colors.HexColor("#FBBF24")),
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (0, 4), (1, 4)),
        ("SPAN", (0, 5), (1, 5)),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_emb3)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: MOD LOGS & SERVER OWNER DM WARNING FORMAT
    # =========================================================================
    story.append(Paragraph("6. Visual Logging Preview — #shizu-mod-logs", h1_style))
    story.append(Paragraph(
        "Staff moderation actions (bans, timeouts, warns, kicks, purges, channel locks) route cleanly to <code>#shizu-mod-logs</code>.",
        body_style
    ))

    # Embed 4: Mod Log Timeout
    embed4_content = [
        [
            Paragraph("<font color='#3B82F6'><b>🔨 MEMBER TIMEOUT</b></font>", discord_title),
            Paragraph("<font color='#949BA4'><b>CASE #1042 • 10:58 AM</b></font>", discord_muted)
        ],
        [
            Paragraph("<b>🎯 TARGET USER</b><br/>@Troublemaker<br/><font color='#949BA4'>ID: 998877665544332211</font>", discord_body),
            Paragraph("<b>👮 STAFF MODERATOR</b><br/>@HeadAdmin<br/><font color='#949BA4'>ID: 1478730719571349545</font>", discord_body)
        ],
        [
            Paragraph("<b>⏱️ DURATION</b><br/><font color='#D97706'><b>1 Hour (60 minutes)</b></font><br/><font color='#949BA4'>Expires at 11:58 AM</font>", discord_body),
            Paragraph("<b>💬 ORIGIN CHANNEL</b><br/>#general-chat<br/><font color='#949BA4'>ID: 77889900112233</font>", discord_body)
        ],
        [
            Paragraph("<b>📝 REASON</b><br/>Excessive toxicity and continuous spamming after verbal warning.", discord_body),
            Paragraph("", discord_body)
        ],
        [
            Paragraph("<font color='#949BA4'>🔵 Shizu Moderation System • Staff Action • 10:58:19 AM</font>", discord_muted),
            Paragraph("", discord_body)
        ]
    ]
    t_emb4 = Table(embed4_content, colWidths=[270, 250])
    t_emb4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DISCORD_BG),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#35373C")),
        ("LINEBEFORE", (0, 0), (0, -1), 4, BLUE_ACCENT),
        ("SPAN", (0, 3), (1, 3)),
        ("SPAN", (0, 4), (1, 4)),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_emb4)
    story.append(Spacer(1, 12))

    # Section 7: Direct Message to Server Owner (@owner)
    story.append(Paragraph("7. Direct Message to Server Owner (@owner) — High Priority Alert", h1_style))
    story.append(Paragraph(
        "Dispatched straight to the personal DMs of the Guild Owner for <b>EVERY</b> Anti-Nuke trigger (<code>Log + Warn</code>).",
        body_style
    ))

    # Embed 5: Owner DM Alert
    owner_dm_content = [
        [
            Paragraph("<font color='#FBBF24'><b>⚠️ URGENT SECURITY ALERT FOR SERVER OWNER</b></font>", discord_title),
            Paragraph("<font color='#EF4444'><b>ACTION TAKEN</b></font>", discord_title)
        ],
        [
            Paragraph("<b>👑 SERVER: Your Discord Community (ID: 123456789098765432)</b><br/>"
                      "<font color='#DBDEE1'>An Anti-Nuke trigger was executed on your server. Shizu Security automatically intercepted the event, neutralized the offender, and restored your server's state:</font>", discord_body),
            Paragraph("", discord_body)
        ],
        [
            Paragraph("<b>👤 TRIGGERED BY</b><br/>@RogueAdmin<br/><font color='#949BA4'>ID: 109876543210987654</font>", discord_body),
            Paragraph("<b>🛡️ WHITELIST STATUS</b><br/><font color='#DC2626'><b>❌ Unwhitelisted User</b></font><br/><font color='#949BA4'>Instant ban policy applied</font>", discord_body)
        ],
        [
            Paragraph("<b>⚡ SHIZU PUNISHMENT</b><br/><font color='#DC2626'><b>🔨 Permanently Banned</b></font><br/><font color='#059669'>All permissions revoked</font>", discord_body),
            Paragraph("<b>🔄 RECOVERY EXECUTED</b><br/><font color='#059669'><b>✅ Channel Auto-Recreated</b></font><br/><font color='#949BA4'>Cloned exact position & sync</font>", discord_body)
        ],
        [
            Paragraph("<b>💡 RECOMMENDED OWNER ACTION</b><br/>"
                      "<font color='#DBDEE1'>The threat has been neutralized and the deleted channel is restored. Please review your server roles. If this staff member was authorized, add them to the whitelist via <code>?whitelist add @user</code>.</font>", discord_body),
            Paragraph("", discord_body)
        ],
        [
            Paragraph("<font color='#949BA4'>👑 Shizu Security 24/7 Shield • Automated Owner Guard • 10:55:12 AM</font>", discord_muted),
            Paragraph("", discord_body)
        ]
    ]
    t_owner = Table(owner_dm_content, colWidths=[360, 160])
    t_owner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A1D20")),
        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#F59E0B")),
        ("LINEBEFORE", (0, 0), (0, -1), 4, colors.HexColor("#F59E0B")),
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (0, 4), (1, 4)),
        ("SPAN", (0, 5), (1, 5)),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_owner)
    story.append(Spacer(1, 10))

    # Hierarchy Escalation DM Box
    story.append(Paragraph("8. Hierarchy Escalation DM (When Offender Has Equal/Higher Role Than Bot)", h2_style))
    hier_dm_content = [
        [
            Paragraph("<font color='#EF4444'><b>🚨 EMERGENCY HIERARCHY ESCALATION</b></font>", discord_title),
            Paragraph("<font color='#FBBF24'><b>MANUAL ACTION REQUIRED</b></font>", discord_title)
        ],
        [
            Paragraph("<b>👑 SERVER: Your Discord Community</b><br/>"
                      "<font color='#DBDEE1'>An unwhitelisted user attempted a destructive action. The action was <b>SUCCESSFULLY REVERTED</b>, but the offender has a <b>higher role hierarchy than Shizu Security</b>. Shizu cannot ban this user automatically due to Discord permission restrictions.</font><br/><br/>"
                      "• <b>Offender:</b> @CoOwner (ID: 991122334455)<br/>"
                      "• <b>Attempted Action:</b> Channel Deletion (<code>#announcements</code>)<br/>"
                      "• <b>Revert Status:</b> <font color='#059669'><b>✅ Recreated Successfully</b></font><br/>"
                      "• <b>Immediate Owner Action:</b> <b>Please demote or ban @CoOwner manually in your server!</b>", discord_body),
            Paragraph("", discord_body)
        ]
    ]
    t_hier_dm = Table(hier_dm_content, colWidths=[360, 160])
    t_hier_dm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#261414")),
        ("BOX", (0, 0), (-1, -1), 1.5, RED_ACCENT),
        ("LINEBEFORE", (0, 0), (0, -1), 4, RED_ACCENT),
        ("SPAN", (0, 1), (1, 1)),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_hier_dm)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    out_pdf = "Shizu_Security_Logging_Preview.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_pdf(out_pdf)
