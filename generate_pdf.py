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
        
        # Draw header (on pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 755, "SHIZU SECURITY v2.3.0")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(138, 755, "— Official Zero-Trust Technical Manual & Command Directory")
            self.drawRightString(576, 755, "Zero-Trust Edition")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(36, 747, 576, 747)
            
        # Draw footer (all pages)
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

def build_pdf(filename="Shizu_Security_Manual.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#090D16")
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569")
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#090D16"),
        spaceBefore=7,
        spaceAfter=4,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    
    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    
    td_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#1E293B")
    )
    
    td_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#0F172A")
    )

    td_code_style = ParagraphStyle(
        'TableCellCode',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=7.8,
        leading=9.5,
        textColor=colors.HexColor("#0F172A")
    )
    
    box_text_style = ParagraphStyle(
        'BoxText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # PAGE 1: TITLE & ZERO-TRUST CORE
    header_data = [
        [
            Paragraph("<b>SHIZU SECURITY</b> <font size=11 color='#64748B'>v2.3.0</font>", title_style),
            Paragraph("<b>ZERO-TRUST DEFENSE MANUAL</b><br/><font size=8 color='#64748B'>Autonomous Discord Defense & Moderation Architecture</font>", ParagraphStyle('HRight', parent=subtitle_style, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[330, 210])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#090D16"), spaceBefore=0, spaceAfter=8))

    meta_info = [
        [
            Paragraph("<b>Product:</b> Shizu Security Bot (Standalone Edition)", box_text_style),
            Paragraph("<b>Developers:</b> VIPER & PRASHU", box_text_style)
        ],
        [
            Paragraph("<b>Core Architecture:</b> v2.3.0 Zero-Trust & Scopes", box_text_style),
            Paragraph("<b>Bot Owners:</b> 1478730719571349545, 1509545584317562970", box_text_style)
        ],
        [
            Paragraph("<b>Runtime:</b> Python 3.10+ / 3.11 | discord.py 2.x | aiosqlite", box_text_style),
            Paragraph("<b>Interface UI:</b> Pure Black (0x000000), Animated Emojis, No-Ping Replies", box_text_style)
        ]
    ]
    meta_table = Table(meta_info, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('PADDING', (0,0), (-1,-1), 5.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Executive Summary & Zero-Trust Principles", h1_style))
    summary_text = (
        "<b>Shizu Security v2.3.0</b> operates on the principle of <b>Default Deny</b>: administrative permissions granted "
        "via Discord roles do NOT imply trust. Every sensitive event is intercepted and verified: "
        "<code>Actor &rarr; Active Scopes &rarr; Required Scope &rarr; Burst Limit &rarr; Allow or Breach</code>. "
        "If an actor is uncertain from audit logs, Shizu reverts the damage and logs but never bans an innocent user. "
        "Even trusted users are bound by a fixed sliding-window burst limit (3 destructive actions in 10s) to neutralize token hijacking."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1.1 Core Zero-Trust Pillars", h2_style))
    pillars_data = [
        [
            Paragraph("<b>🛡️ Anti-Nuke Zero-Trust</b>", th_style),
            Paragraph("<b>⚡ Real-Time AutoMod</b>", th_style),
            Paragraph("<b>🔨 Hierarchy Moderation</b>", th_style)
        ],
        [
            Paragraph(
                "• <b>Default Deny:</b> Every action requires explicit additive scope.<br/>"
                "• <b>Auto-Recreate Nuked Channels:</b> Clones deleted channels with exact overwrites.<br/>"
                "• <b>Fixed Burst Throttling:</b> 3 actions in 10s trips immediate breach response.<br/>"
                "• <b>Audit Uncertainty Rule:</b> Revert and log, never ban if actor is uncertain.<br/>"
                "• <b>Whitelist Trap:</b> Whitelisting a role blocks assignment by sub-owners.",
                td_style
            ),
            Paragraph(
                "• <b>Anti-Spam / Flood:</b> 5 msgs in 5s or 3 rapid duplicate text hashes.<br/>"
                "• <b>Smart Anti-Invite:</b> Blocks foreign links; auto-permits server vanity URL.<br/>"
                "• <b>Anti-Link & Media Whitelist:</b> Whitelists Tenor, Giphy, Spotify, CDN.<br/>"
                "• <b>Regex Bad Words:</b> Exact word-boundary (<code>\\b</code>) dictionary filtering.<br/>"
                "• <b>Fixed Sensitivity:</b> Calibrated thresholds eliminate false flags.",
                td_style
            ),
            Paragraph(
                "• <b>Strict Hierarchy Enforcement:</b> Superiors and owners immune to sub-staff.<br/>"
                "• <b>Disciplinary Arsenal:</b> Ban, unban, kick, timeout (mute), warn, lock, hide.<br/>"
                "• <b>14-Day Safe Purge:</b> Auto-capped to 14 days to prevent API crashes.<br/>"
                "• <b>Permanent Case IDs:</b> Every disciplinary action generates a Case ID.<br/>"
                "• <b>Interactive Setup:</b> <code>?help</code> interactive dashboard with persistent views.",
                td_style
            )
        ]
    ]
    pillars_table = Table(pillars_data, colWidths=[180, 180, 180])
    pillars_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('PADDING', (0,0), (-1,-1), 5.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(pillars_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1.2 Shizu Visual & Audio Interface Aesthetics", h2_style))
    ui_info = [
        [
            Paragraph("<b>Zero-Ping Interactions:</b> All responses enforce <code>mention_author=False</code>, keeping channels completely silent.", td_style),
            Paragraph("<b>Minimalist Dark Embeds:</b> Styled in pure obsidian black (<code>color=0x000000</code>) matching Shizu Music.", td_style)
        ],
        [
            Paragraph("<b>Animated Confirmations:</b> Features high-definition animated Discord emojis (<code>&lt;a:tick:...&gt;</code>, <code>&lt;a:alert:...&gt;</code>, <code>&lt;a:gears:...&gt;</code>).", td_style),
            Paragraph("<b>Hierarchy Failsafes:</b> Commands fail safely with informative embeds if bot permissions or role positions are insufficient.", td_style)
        ]
    ]
    ui_table = Table(ui_info, colWidths=[270, 270])
    ui_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFFFF")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(ui_table)

    # PAGE 2: ZERO-TRUST WHITELIST & SCOPES
    story.append(PageBreak())
    story.append(Paragraph("2. Zero-Trust Authorization & Granular Scopes", h1_style))
    story.append(Paragraph(
        "Shizu Security replaces arbitrary administrator trust with additive scopes. "
        "A user or role must possess the explicit scope required for an action, optionally constrained by target ID and expiration.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.1 Canonical Scope Registry", h2_style))
    scope_registry = [
        [
            Paragraph("<b>Section</b>", th_style),
            Paragraph("<b>Granular Scopes</b>", th_style),
            Paragraph("<b>Operational Boundary & Rules</b>", th_style)
        ],
        [
            Paragraph("<b>Channels</b>", td_bold_style),
            Paragraph("<code>antinuke.channel.create</code><br/><code>antinuke.channel.edit</code><br/><code>antinuke.channel.delete</code>", td_code_style),
            Paragraph("Allows creating, editing topics/names, or deleting channels/categories. Monitored under fixed 3-in-10s burst limit.", td_style)
        ],
        [
            Paragraph("<b>Roles</b>", td_bold_style),
            Paragraph("<code>antinuke.role.create</code><br/><code>antinuke.role.edit</code><br/><code>antinuke.role.delete</code><br/><code>antinuke.role.assign</code>", td_code_style),
            Paragraph("Allows managing roles. <b>Hard Guard:</b> <code>role.assign</code> NEVER grants Administrator, Ban Members, or Manage Guild.", td_style)
        ],
        [
            Paragraph("<b>Members</b>", td_bold_style),
            Paragraph("<code>antinuke.member.ban</code><br/><code>antinuke.member.kick</code>", td_code_style),
            Paragraph("Allows banning or kicking members. Subject to hierarchy validation and burst limits.", td_style)
        ],
        [
            Paragraph("<b>Webhooks & Bots</b>", td_bold_style),
            Paragraph("<code>antinuke.webhook.manage</code><br/><code>antinuke.bot.add</code>", td_code_style),
            Paragraph("Allows managing webhooks or inviting external bots. Unauthorized bots are banned on sight.", td_style)
        ],
        [
            Paragraph("<b>AutoMod Bypass</b>", td_bold_style),
            Paragraph("<code>automod.bypass.all</code><br/><code>automod.bypass.&lt;rule&gt;</code>", td_code_style),
            Paragraph("Bypasses all AutoMod filters or specific rules (spam, invite, link, badwords, caps, mention, emoji).", td_style)
        ],
        [
            Paragraph("<b>Admin Scopes</b><br/><font size=7 color='#DC2626'>Owner/Extra Only</font>", td_bold_style),
            Paragraph("<code>whitelist.manage</code><br/><code>extraowner.manage</code><br/><code>security.configure</code><br/><code>lockdown.toggle</code>", td_code_style),
            Paragraph("Strictly reserved for Server Owner and Extra Owners. <b>EXCLUDED from Supreme</b> to prevent escalation.", td_style)
        ]
    ]
    scope_table = Table(scope_registry, colWidths=[80, 185, 275])
    scope_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(scope_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2.2 Breach Countermeasures & Revert Map", h2_style))
    revert_data = [
        [
            Paragraph("<b>Breach Event</b>", th_style),
            Paragraph("<b>Stop Action</b>", th_style),
            Paragraph("<b>Punish Action</b>", th_style),
            Paragraph("<b>Automated Self-Healing Reversion</b>", th_style)
        ],
        [
            Paragraph("<b>Channel Delete</b>", td_bold_style),
            Paragraph("Strip dangerous roles", td_style),
            Paragraph("<font color='#B91C1C'><b>Ban Attacker</b></font>", td_style),
            Paragraph("Instantly clones channel with exact name, topic, slowmode, and <b>permission overwrites</b>.", td_style)
        ],
        [
            Paragraph("<b>Rogue Channel Spam</b>", td_bold_style),
            Paragraph("Strip dangerous roles", td_style),
            Paragraph("<font color='#B91C1C'><b>Ban Attacker</b></font>", td_style),
            Paragraph("Deletes rogue channel on sight + sweeps matching burst spam channels.", td_style)
        ],
        [
            Paragraph("<b>Role Delete</b>", td_bold_style),
            Paragraph("Strip dangerous roles", td_style),
            Paragraph("<font color='#B91C1C'><b>Ban Attacker</b></font>", td_style),
            Paragraph("Recreates role from snapshot with exact name, color, and permissions.", td_style)
        ],
        [
            Paragraph("<b>Whitelisted Role Trap</b>", td_bold_style),
            Paragraph("Remove role from target", td_style),
            Paragraph("<font color='#B91C1C'><b>Ban Attacker</b></font>", td_style),
            Paragraph("Anyone below Extra Owner assigning a whitelisted role trips an instant breach.", td_style)
        ],
        [
            Paragraph("<b>Unauthorized Ban</b>", td_bold_style),
            Paragraph("Strip dangerous roles", td_style),
            Paragraph("<font color='#B91C1C'><b>Ban Attacker</b></font>", td_style),
            Paragraph("Instantly unbans the targeted victim.", td_style)
        ],
        [
            Paragraph("<b>Rogue Bot / Webhook</b>", td_bold_style),
            Paragraph("Strip dangerous roles", td_style),
            Paragraph("<font color='#B91C1C'><b>Ban Inviter</b></font>", td_style),
            Paragraph("Bans rogue bot immediately / deletes all unauthorized webhooks.", td_style)
        ],
        [
            Paragraph("<b>Audit Uncertainty</b>", td_bold_style),
            Paragraph("Log incident ticket", td_style),
            Paragraph("<b>No Ban</b> (Safety rule)", td_style),
            Paragraph("Damage reverted cleanly; owner alerted with Incident ID.", td_style)
        ]
    ]
    revert_table = Table(revert_data, colWidths=[105, 110, 85, 240])
    revert_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(revert_table)

    # PAGE 3: AUTOMOD WATERFALL
    story.append(PageBreak())
    story.append(Paragraph("3. AutoMod Waterfall & Smart Filtering", h1_style))
    story.append(Paragraph(
        "Chat messages are scanned through an optimized short-circuit pipeline. "
        "Thresholds are fixed internally to eliminate configuration bloat and false positives.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3.1 Evaluation Cascade & Smart Whitelists", h2_style))
    automod_steps = [
        [
            Paragraph("<b>Stage</b>", th_style),
            Paragraph("<b>Checkpoint</b>", th_style),
            Paragraph("<b>Logic & Evaluation Rule</b>", th_style),
            Paragraph("<b>Result</b>", th_style)
        ],
        [
            Paragraph("<b>Stage 1</b>", td_code_style),
            Paragraph("<b>Bot & Webhook Bypass</b>", td_bold_style),
            Paragraph("Author is a bot (<code>author.bot</code>) or webhook payload.", td_style),
            Paragraph("<font color='#15803D'><b>BYPASS</b></font> (Never scan bots)", td_style)
        ],
        [
            Paragraph("<b>Stage 2</b>", td_code_style),
            Paragraph("<b>Executive Immunity</b>", td_bold_style),
            Paragraph("Author is Global Bot Owner, Server Owner, or Extra Owner.", td_style),
            Paragraph("<font color='#15803D'><b>BYPASS</b></font> (Root leadership)", td_style)
        ],
        [
            Paragraph("<b>Stage 3</b>", td_code_style),
            Paragraph("<b>Additive Scope Check</b>", td_bold_style),
            Paragraph("Author has <code>automod.bypass.all</code> or specific <code>automod.bypass.&lt;rule&gt;</code>.", td_style),
            Paragraph("<font color='#15803D'><b>BYPASS</b></font> (Staff bypass)", td_style)
        ],
        [
            Paragraph("<b>Stage 4</b>", td_code_style),
            Paragraph("<b>Granular Exemptions</b>", td_bold_style),
            Paragraph("Channel in ignored channels OR Role in ignored roles OR Member in ignored users.", td_style),
            Paragraph("<font color='#15803D'><b>BYPASS</b></font> (Configured exemption)", td_style)
        ],
        [
            Paragraph("<b>Stage 5</b>", td_code_style),
            Paragraph("<b>Smart Media Whitelist</b>", td_bold_style),
            Paragraph("Server vanity URL & active server invites permitted; Tenor, Giphy, Spotify, CDN allowed.", td_style),
            Paragraph("<font color='#15803D'><b>PERMITTED</b></font> (Safe content)", td_style)
        ],
        [
            Paragraph("<b>Stage 6</b>", td_code_style),
            Paragraph("<b>Rule Violation</b>", td_bold_style),
            Paragraph("Triggers Spam, Foreign Invite, Links, Bad Words, Caps, Mentions, or Emojis.", td_style),
            Paragraph("<font color='#B91C1C'><b>ENFORCE PENALTY</b></font>", td_style)
        ]
    ]
    automod_steps_table = Table(automod_steps, colWidths=[55, 135, 220, 130])
    automod_steps_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#FEF2F2")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(automod_steps_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.2 Fixed Calibrated Thresholds & Punishments", h2_style))
    automod_matrix = [
        [
            Paragraph("<b>Rule Name</b>", th_style),
            Paragraph("<b>Detection Mechanism & Algorithm</b>", th_style),
            Paragraph("<b>Fixed Calibrated Threshold</b>", th_style),
            Paragraph("<b>Configurable Penalties</b>", th_style)
        ],
        [
            Paragraph("<b>Anti-Spam</b>", td_bold_style),
            Paragraph("Sliding window tracking message frequency & duplicate content hashes", td_style),
            Paragraph("5 msgs / 5 sec or 3 duplicates", td_style),
            Paragraph("delete, warn, timeout (1-1440m)", td_style)
        ],
        [
            Paragraph("<b>Anti-Invite</b>", td_bold_style),
            Paragraph("Discord invite regex matching with server vanity bypass", td_style),
            Paragraph("Instant on foreign invite", td_style),
            Paragraph("delete, warn, timeout, kick, ban", td_style)
        ],
        [
            Paragraph("<b>Anti-Link</b>", td_bold_style),
            Paragraph("URL detection excluding whitelisted media domains", td_style),
            Paragraph("Instant on non-whitelisted URL", td_style),
            Paragraph("delete, warn, timeout", td_style)
        ],
        [
            Paragraph("<b>Bad Words</b>", td_bold_style),
            Paragraph("Case-insensitive word boundary (<code>\\bword\\b</code>) regex matching", td_style),
            Paragraph("Instant on exact word match", td_style),
            Paragraph("delete, warn, timeout, kick, ban", td_style)
        ],
        [
            Paragraph("<b>Anti-Caps</b>", td_bold_style),
            Paragraph("Uppercase character ratio on messages exceeding 8 characters", td_style),
            Paragraph("70% uppercase ratio", td_style),
            Paragraph("delete, warn, timeout", td_style)
        ],
        [
            Paragraph("<b>Mass Mention</b>", td_bold_style),
            Paragraph("Count of unique member pings, role pings, and @everyone tags", td_style),
            Paragraph("5 unique pings / msg", td_style),
            Paragraph("delete, warn, timeout, kick", td_style)
        ],
        [
            Paragraph("<b>Emoji Spam</b>", td_bold_style),
            Paragraph("Combined count of Unicode emojis and custom Discord emojis", td_style),
            Paragraph("6 emojis / msg", td_style),
            Paragraph("delete, warn", td_style)
        ]
    ]
    automod_matrix_table = Table(automod_matrix, colWidths=[80, 210, 115, 135])
    automod_matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(automod_matrix_table)

    # PAGE 4: ANTI-NUKE & RECOVERY COMMANDS
    story.append(PageBreak())
    story.append(Paragraph("4. Command Directory: Anti-Nuke & Recovery", h1_style))
    story.append(Paragraph(
        "Complete syntax and permission requirements for Anti-Nuke defense, disaster recovery snapshots, "
        "and emergency locks. Default prefix <code>?</code> (configurable via <code>?setprefix</code>).",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1 Anti-Nuke & Disaster Recovery Commands (17 Commands)", h2_style))
    antinuke_cmds = [
        [
            Paragraph("<b>Command Syntax</b>", th_style),
            Paragraph("<b>Required Permission</b>", th_style),
            Paragraph("<b>Detailed Functional Description</b>", th_style)
        ],
        [
            Paragraph("<code>?antinuke</code>", td_code_style),
            Paragraph("Manage Server", td_style),
            Paragraph("Opens the interactive Anti-Nuke dashboard displaying real-time protection metrics.", td_style)
        ],
        [
            Paragraph("<code>?antinuke enable</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Arms real-time defense across channels, roles, webhooks, and bot additions.", td_style)
        ],
        [
            Paragraph("<code>?antinuke disable</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Disarms Anti-Nuke countermeasures (emergency maintenance use only).", td_style)
        ],
        [
            Paragraph("<code>?antinuke punishment &lt;act&gt;</code>", td_code_style),
            Paragraph("Server Owner", td_style),
            Paragraph("Sets default penalty executed upon breach detection: <code>ban</code>, <code>kick</code>, or <code>strip</code>.", td_style)
        ],
        [
            Paragraph("<code>?antinuke status</code>", td_code_style),
            Paragraph("Manage Server", td_style),
            Paragraph("Displays active status, configured punishment, and whitelisted staff counts.", td_style)
        ],
        [
            Paragraph("<code>?backup</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Takes an instant database snapshot of all channels, categories, roles, and permission overwrites.", td_style)
        ],
        [
            Paragraph("<code>?restore channels</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Restores all deleted channels from snapshot with exact permission overwrites.", td_style)
        ],
        [
            Paragraph("<code>?restore roles</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Restores all deleted roles from snapshot with exact colors and permissions.", td_style)
        ],
        [
            Paragraph("<code>?whitelist add &lt;@user|@role&gt;</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Opens interactive multi-select section panel, Supreme button, and target/expiry modal.", td_style)
        ],
        [
            Paragraph("<code>?whitelist remove &lt;@user|@role&gt;</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Revokes entity whitelist status, placing them back under zero-trust monitoring.", td_style)
        ],
        [
            Paragraph("<code>?whitelist list</code>", td_code_style),
            Paragraph("Manage Server", td_style),
            Paragraph("Displays all currently whitelisted users and roles in the server.", td_style)
        ],
        [
            Paragraph("<code>?whitelist check &lt;@user|@role&gt;</code>", td_code_style),
            Paragraph("Manage Server", td_style),
            Paragraph("Checks active scopes, targets, and expiration countdown for a member or role.", td_style)
        ],
        [
            Paragraph("<code>?whitelist reset</code>", td_code_style),
            Paragraph("Server Owner Only", td_style),
            Paragraph("Wipes all users and roles from the Anti-Nuke whitelist (emergency reset failsafe).", td_style)
        ],
        [
            Paragraph("<code>?extraowner add &lt;@user&gt;</code>", td_code_style),
            Paragraph("Server Owner Only", td_style),
            Paragraph("Designates a trusted co-owner authorized to configure defenses and whitelists.", td_style)
        ],
        [
            Paragraph("<code>?extraowner remove &lt;@user&gt;</code>", td_code_style),
            Paragraph("Server Owner Only", td_style),
            Paragraph("Revokes Extra Owner privileges from a user.", td_style)
        ],
        [
            Paragraph("<code>?extraowner list</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Lists all designated Extra Owners for the server.", td_style)
        ],
        [
            Paragraph("<code>?lockdown</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Freezes all text channels instantly by stripping <code>Send Messages</code> from @everyone.", td_style)
        ],
        [
            Paragraph("<code>?unlockdown</code>", td_code_style),
            Paragraph("Owner / Extra Owner", td_style),
            Paragraph("Restores standard public chatting permissions across all server channels.", td_style)
        ]
    ]
    antinuke_table = Table(antinuke_cmds, colWidths=[160, 115, 265])
    antinuke_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(antinuke_table)
    story.append(Spacer(1, 8))

    antinuke_note = [
        [
            Paragraph(
                "<b>💡 Operational Tip: Whitelist Trap & Role Whitelisting</b><br/>"
                "• <b>Role Whitelisting Security Trap:</b> When a role is added to the whitelist, anyone below Extra Owner who assigns that role to a member automatically triggers a breach. This stops privilege escalation via alt accounts.<br/>"
                "• <b>Fixed Burst Throttling:</b> Even if a user possesses the <code>antinuke.channel.delete</code> scope, executing 3 deletions within 10.0s trips the burst throttle, stripping dangerous roles and banning the actor.",
                box_text_style
            )
        ]
    ]
    antinuke_note_table = Table(antinuke_note, colWidths=[540])
    antinuke_note_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
    ]))
    story.append(antinuke_note_table)

    # PAGE 5: AUTOMOD & SYSTEM COMMANDS
    story.append(PageBreak())
    story.append(Paragraph("5. Command Directory: AutoMod, Cases & System", h1_style))
    story.append(Paragraph(
        "Complete command reference for AutoMod rule management, custom word blacklists, audit case lookups, "
        "and core bot system diagnostics.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("5.1 AutoMod & Word Blacklist Commands (12 Commands)", h2_style))
    automod_cmds = [
        [
            Paragraph("<b>Command Syntax</b>", th_style),
            Paragraph("<b>Required Permission</b>", th_style),
            Paragraph("<b>Detailed Functional Description</b>", th_style)
        ],
        [
            Paragraph("<code>?automod</code>", td_code_style),
            Paragraph("Manage Guild", td_style),
            Paragraph("Opens the AutoMod management dashboard and rule status embed.", td_style)
        ],
        [
            Paragraph("<code>?automod enable|disable</code>", td_code_style),
            Paragraph("Manage Guild", td_style),
            Paragraph("Globally enables or disables all AutoMod message scanners.", td_style)
        ],
        [
            Paragraph("<code>?automod status</code>", td_code_style),
            Paragraph("Manage Guild", td_style),
            Paragraph("Displays active status, fixed thresholds, and configured penalties for each rule.", td_style)
        ],
        [
            Paragraph("<code>?automod rule &lt;rule&gt; &lt;on|off&gt;</code>", td_code_style),
            Paragraph("Manage Guild", td_style),
            Paragraph("Toggles specific rule: spam, invite, link, badwords, caps, mention, emoji.", td_style)
        ],
        [
            Paragraph("<code>?automod punish &lt;rule&gt; &lt;act&gt; [m]</code>", td_code_style),
            Paragraph("Manage Guild", td_style),
            Paragraph("Configures rule penalty: delete, warn, timeout [mins], kick, ban.", td_style)
        ],
        [
            Paragraph("<code>?automod ignore &lt;type&gt; &lt;tgt&gt;</code>", td_code_style),
            Paragraph("Manage Guild", td_style),
            Paragraph("Exempts a <code>channel</code>, <code>role</code>, or <code>user</code> from AutoMod.", td_style)
        ],
        [
            Paragraph("<code>?automod unignore &lt;type&gt; &lt;tgt&gt;</code>", td_code_style),
            Paragraph("Manage Guild", td_style),
            Paragraph("Removes an active AutoMod exemption from a target.", td_style)
        ],
        [
            Paragraph("<code>?automod ignored</code>", td_code_style),
            Paragraph("Manage Guild", td_style),
            Paragraph("Displays all active channel, role, and member exemptions.", td_style)
        ],
        [
            Paragraph("<code>?badwords add &lt;word&gt;</code>", td_code_style),
            Paragraph("Manage Messages", td_style),
            Paragraph("Adds exact word to blacklist (uses exact word-boundary regex).", td_style)
        ],
        [
            Paragraph("<code>?badwords remove &lt;word&gt;</code>", td_code_style),
            Paragraph("Manage Messages", td_style),
            Paragraph("Removes a word from the active server blacklist.", td_style)
        ],
        [
            Paragraph("<code>?badwords list</code>", td_code_style),
            Paragraph("Manage Messages", td_style),
            Paragraph("Lists all blacklisted terms in an ephemeral/private embed.", td_style)
        ],
        [
            Paragraph("<code>?badwords clear</code>", td_code_style),
            Paragraph("Manage Guild", td_style),
            Paragraph("Clears all blacklisted terms from the database.", td_style)
        ]
    ]
    automod_table = Table(automod_cmds, colWidths=[160, 115, 265])
    automod_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(automod_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("5.2 Cases, Logging & System Commands (10 Commands)", h2_style))
    system_cmds = [
        [
            Paragraph("<b>Command Syntax</b>", th_style),
            Paragraph("<b>Required Permission</b>", th_style),
            Paragraph("<b>Detailed Functional Description</b>", th_style)
        ],
        [
            Paragraph("<code>?security</code>", td_code_style),
            Paragraph("Manage Server", td_style),
            Paragraph("Full server defense overview (Anti-Nuke, AutoMod, Logging, Whitelist counts).", td_style)
        ],
        [
            Paragraph("<code>?case &lt;case_id&gt;</code>", td_code_style),
            Paragraph("Moderate Members", td_style),
            Paragraph("Fetches forensic case details: action, target, moderator, reason, and timestamp.", td_style)
        ],
        [
            Paragraph("<code>?modlogs &lt;user&gt;</code>", td_code_style),
            Paragraph("Moderate Members", td_style),
            Paragraph("Displays user's full disciplinary history with all recorded Case IDs.", td_style)
        ],
        [
            Paragraph("<code>?warnings &lt;member&gt;</code>", td_code_style),
            Paragraph("Moderate Members", td_style),
            Paragraph("Lists active warnings for a member with warning IDs and dates.", td_style)
        ],
        [
            Paragraph("<code>?clearwarns &lt;member&gt; [id]</code>", td_code_style),
            Paragraph("Manage Messages", td_style),
            Paragraph("Clears a specific warning ID or wipes all warnings for a member.", td_style)
        ],
        [
            Paragraph("<code>?setlog &lt;type&gt; &lt;#channel&gt;</code>", td_code_style),
            Paragraph("Manage Server", td_style),
            Paragraph("Binds log channel for type: <code>antinuke</code>, <code>automod</code>, or <code>mod</code>.", td_style)
        ],
        [
            Paragraph("<code>?setprefix &lt;prefix&gt;</code>", td_code_style),
            Paragraph("Administrator", td_style),
            Paragraph("Sets custom command prefix for the server (persisted in SQLite).", td_style)
        ],
        [
            Paragraph("<code>?ping</code>", td_code_style),
            Paragraph("Everyone", td_style),
            Paragraph("Shows Discord WebSocket heartbeat and roundtrip message latency.", td_style)
        ],
        [
            Paragraph("<code>?stats</code>", td_code_style),
            Paragraph("Everyone", td_style),
            Paragraph("Displays bot uptime, guild/user count, RAM usage, and developer credits.", td_style)
        ],
        [
            Paragraph("<code>?help [command]</code>", td_code_style),
            Paragraph("Everyone", td_style),
            Paragraph("Unified interactive Help & Setup Center with persistent controls.", td_style)
        ]
    ]
    system_table = Table(system_cmds, colWidths=[160, 115, 265])
    system_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(system_table)

    # PAGE 6: MODERATION COMMANDS
    story.append(PageBreak())
    story.append(Paragraph("6. Command Directory: Hierarchy-Safe Moderation", h1_style))
    story.append(Paragraph(
        "Day-to-day staff commands for sanctioning violators, purging messages, and managing channel states. "
        "Every command validates caller and bot role positions to guarantee hierarchy safety.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("6.1 Moderation & Utility Commands (16 Commands)", h2_style))
    mod_cmds = [
        [
            Paragraph("<b>Command Syntax</b>", th_style),
            Paragraph("<b>Required Permission</b>", th_style),
            Paragraph("<b>Detailed Functional Description</b>", th_style)
        ],
        [
            Paragraph("<code>?ban &lt;member|id&gt; [reason]</code>", td_code_style),
            Paragraph("Ban Members", td_style),
            Paragraph("Bans user, sends clean DM notice, checks hierarchy, logs Case ID.", td_style)
        ],
        [
            Paragraph("<code>?unban &lt;user_id&gt; [reason]</code>", td_code_style),
            Paragraph("Ban Members", td_style),
            Paragraph("Removes ban from Discord user ID and logs disciplinary case.", td_style)
        ],
        [
            Paragraph("<code>?kick &lt;member&gt; [reason]</code>", td_code_style),
            Paragraph("Kick Members", td_style),
            Paragraph("Kicks member from server, verifies hierarchy, logs Case ID.", td_style)
        ],
        [
            Paragraph("<code>?timeout &lt;member&gt; &lt;dur&gt; [r]</code>", td_code_style),
            Paragraph("Moderate Members", td_style),
            Paragraph("Times out member (e.g. 10m, 1h, 1d) with strict hierarchy checks.", td_style)
        ],
        [
            Paragraph("<code>?untimeout &lt;member&gt; [reason]</code>", td_code_style),
            Paragraph("Moderate Members", td_style),
            Paragraph("Removes active Discord timeout from member.", td_style)
        ],
        [
            Paragraph("<code>?warn &lt;member&gt; [reason]</code>", td_code_style),
            Paragraph("Moderate Members", td_style),
            Paragraph("Issues persistent formal warning to member ledger and logs Case ID.", td_style)
        ],
        [
            Paragraph("<code>?purge &lt;amount&gt; [@user]</code>", td_code_style),
            Paragraph("Manage Messages", td_style),
            Paragraph("Deletes up to 500 messages (auto-capped to 14 days to prevent API crashes).", td_style)
        ],
        [
            Paragraph("<code>?slowmode &lt;seconds&gt; [chan]</code>", td_code_style),
            Paragraph("Manage Channels", td_style),
            Paragraph("Configures channel message cooldown delay (0 to 21600 seconds).", td_style)
        ],
        [
            Paragraph("<code>?lock [channel] [reason]</code>", td_code_style),
            Paragraph("Manage Channels", td_style),
            Paragraph("Locks text channel by denying Send Messages for @everyone.", td_style)
        ],
        [
            Paragraph("<code>?unlock [channel]</code>", td_code_style),
            Paragraph("Manage Channels", td_style),
            Paragraph("Restores Send Messages permission for @everyone.", td_style)
        ],
        [
            Paragraph("<code>?hide [channel]</code>", td_code_style),
            Paragraph("Manage Channels", td_style),
            Paragraph("Hides text channel from standard members by denying View Channel.", td_style)
        ],
        [
            Paragraph("<code>?unhide [channel]</code>", td_code_style),
            Paragraph("Manage Channels", td_style),
            Paragraph("Restores View Channel permission for @everyone.", td_style)
        ],
        [
            Paragraph("<code>?role add &lt;member&gt; &lt;role&gt;</code>", td_code_style),
            Paragraph("Manage Roles", td_style),
            Paragraph("Assigns role to member with strict bot and caller hierarchy validation.", td_style)
        ],
        [
            Paragraph("<code>?role remove &lt;member&gt; &lt;role&gt;</code>", td_code_style),
            Paragraph("Manage Roles", td_style),
            Paragraph("Removes role from member with strict hierarchy validation.", td_style)
        ],
        [
            Paragraph("<code>?setnick &lt;member&gt; [nickname]</code>", td_code_style),
            Paragraph("Manage Nicknames", td_style),
            Paragraph("Changes or resets member's server display nickname.", td_style)
        ],
        [
            Paragraph("<code>?snipe [channel]</code>", td_code_style),
            Paragraph("Manage Messages", td_style),
            Paragraph("Reveals the most recently deleted message and author in the channel.", td_style)
        ]
    ]
    mod_table = Table(mod_cmds, colWidths=[160, 115, 265])
    mod_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(mod_table)
    story.append(Spacer(1, 8))

    mod_note = [
        [
            Paragraph(
                "<b>🛡️ Operational Guardrails: Hierarchy Safety & 14-Day Purge Rules</b><br/>"
                "• <b>Hierarchy Enforcement:</b> Shizu Security automatically verifies that the executing moderator's highest role is strictly above the target member, and that the bot's own top role is also above the target. Staff can never moderate server owners or superiors.<br/>"
                "• <b>14-Day Safe Purge Cap:</b> Discord's API rejects bulk deletion calls for messages older than 14 days with HTTP 400 Bad Request. Shizu's purge algorithm automatically filters out older messages and safely cleans recent content without crashing.",
                box_text_style
            )
        ]
    ]
    mod_note_table = Table(mod_note, colWidths=[540])
    mod_note_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
    ]))
    story.append(mod_note_table)

    # PAGE 7: DISASTER RECOVERY & HARDENING
    story.append(PageBreak())
    story.append(Paragraph("7. Disaster Recovery & Security Hardening", h1_style))
    story.append(Paragraph(
        "Technical breakdown of automated snapshot recovery, real-time channel recreation, and production security checklists.",
        body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("7.1 Disaster Recovery & Self-Healing Architecture", h2_style))
    dr_steps = [
        [
            Paragraph("<b>Operation Phase</b>", th_style),
            Paragraph("<b>Command / Trigger</b>", th_style),
            Paragraph("<b>Technical Implementation & Restoration Workflow</b>", th_style)
        ],
        [
            Paragraph("<b>Automatic Snapshot</b>", td_bold_style),
            Paragraph("Bot Launch / <code>?backup</code>", td_style),
            Paragraph(
                "Serializes all channels, categories, voice channels, roles, role colors, and "
                "every member/role permission overwrite into SQLite JSON storage.",
                td_style
            )
        ],
        [
            Paragraph("<b>Real-Time Self-Healing</b>", td_bold_style),
            Paragraph("Unauthorized Channel Deletion", td_style),
            Paragraph(
                "Shizu catches <code>on_guild_channel_delete</code>, bans the rogue administrator within 500ms, "
                "and immediately clones the channel with exact position, category, topic, NSFW flags, and <b>overwrites</b>.",
                td_style
            )
        ],
        [
            Paragraph("<b>Disaster Channel Restore</b>", td_bold_style),
            Paragraph("<code>?restore channels</code>", td_style),
            Paragraph(
                "Iterates the snapshot database, identifies any channels missing from Discord, creates them, "
                "re-parents under their saved categories, and restores exact role permission trees.",
                td_style
            )
        ],
        [
            Paragraph("<b>Disaster Role Restore</b>", td_bold_style),
            Paragraph("<code>?restore roles</code>", td_style),
            Paragraph(
                "Recreates all nuked roles from snapshot with their exact colors, hoist flags, and permissions.",
                td_style
            )
        ],
        [
            Paragraph("<b>Emergency Lockdown</b>", td_bold_style),
            Paragraph("<code>?lockdown</code> / <code>?unlockdown</code>", td_style),
            Paragraph(
                "Instantly freezes all text channels by denying <code>Send Messages</code> on @everyone. "
                "<code>?unlockdown</code> safely clears the override to restore normal chatting.",
                td_style
            )
        ]
    ]
    dr_table = Table(dr_steps, colWidths=[120, 120, 300])
    dr_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(dr_table)
    story.append(Spacer(1, 7))

    story.append(Paragraph("7.2 Production Hardening & Pre-Flight Checklist", h2_style))
    hardening_data = [
        [
            Paragraph("<b>Requirement</b>", th_style),
            Paragraph("<b>Target Configuration</b>", th_style),
            Paragraph("<b>Security & Operational Justification</b>", th_style)
        ],
        [
            Paragraph("<b>Role Hierarchy</b>", td_bold_style),
            Paragraph("Place Shizu Security role at the <b>highest position</b> in Server Settings > Roles.", td_style),
            Paragraph("Discord enforces strict hierarchy: bots cannot ban, kick, timeout, or edit roles for members with equal or higher roles.", td_style)
        ],
        [
            Paragraph("<b>Privileged Gateway Intents</b>", td_bold_style),
            Paragraph("Enable <b>Server Members Intent</b> and <b>Message Content Intent</b> in Discord Dev Portal.", td_style),
            Paragraph("Mandatory for inspecting message contents for AutoMod and monitoring member actions.", td_style)
        ],
        [
            Paragraph("<b>Environment Security</b>", td_bold_style),
            Paragraph("Store tokens and IDs in <code>.env</code> file:<br/><code>OWNER_IDS=1478730719571349545,1509545584317562970</code>", td_style),
            Paragraph("Prevents token leaks and credential compromise. Keeps bot purely standalone.", td_style)
        ],
        [
            Paragraph("<b>Dedicated Audit Channels</b>", td_bold_style),
            Paragraph("Create private staff logs and bind:<br/><code>?setlog antinuke #logs</code> | <code>?setlog automod #logs</code>", td_style),
            Paragraph("Ensures immediate real-time forensic logging of breach events and AutoMod actions.", td_style)
        ]
    ]
    hardening_table = Table(hardening_data, colWidths=[115, 175, 250])
    hardening_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(hardening_table)
    story.append(Spacer(1, 9))

    signoff_data = [
        [
            Paragraph(
                "<b>SHIZU SECURITY BOT v2.3.0 — ZERO-TRUST DEFENSE CORE</b><br/>"
                "Engineered & Maintained by <b>VIPER & PRASHU</b><br/>"
                "<font size=7.5 color='#64748B'>Zero-Dependency Autonomous Architecture | Anti-Nuke • AutoMod • Moderation</font>",
                ParagraphStyle('Signoff', parent=box_text_style, alignment=1)
            )
        ]
    ]
    signoff_table = Table(signoff_data, colWidths=[540])
    signoff_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('PADDING', (0,0), (-1,-1), 6.5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(signoff_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    build_pdf()
