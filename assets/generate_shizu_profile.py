"""
Shizu Security - Zero-Trust Animated Bot Avatar & Banner Generator
Generates high-definition video-type animated GIFs and MP4s starring the Shizu mascot.
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import subprocess

SRC_MASCOT = r"c:\Users\xdvip\Videos\security bot\assets\shizu_mascot.webp"
FFMPEG = r"C:\Program Files\BlueStacks_msi5\ffmpeg.exe"
FONT_PATH = r"C:\Windows\Fonts\bahnschrift.ttf"
OUTPUT_DIR = r"c:\Users\xdvip\Videos\security bot\assets"

NUM_FRAMES = 36  # 36 frames at 25 fps = 1.44s smooth seamless loop
FPS = 25

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def draw_arc_segment(draw, center, radius, start_angle, end_angle, color, width=2):
    cx, cy = center
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.arc(bbox, start=start_angle, end=end_angle, fill=color, width=width)

def generate_avatar():
    """Generates 512x512 animated avatar with rotating HUD rings, radar sweep, and Shizu mascot."""
    print(f"[*] Rendering Animated Avatar ({NUM_FRAMES} frames)...")
    frames = []

    c_cyan = (0, 240, 255)
    c_purple = (180, 60, 255)
    c_green = (0, 255, 170)
    c_bg = (6, 8, 16)

    # Load mascot
    raw_dog = Image.open(SRC_MASCOT).convert('RGBA')
    raw_dog = raw_dog.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))
    raw_dog = ImageEnhance.Contrast(raw_dog).enhance(1.08)

    dog_base_dim = 360
    dog_resized = raw_dog.resize((dog_base_dim, dog_base_dim), Image.Resampling.LANCZOS)

    # Circular mask for mascot
    circle_mask = Image.new('L', (dog_base_dim, dog_base_dim), 0)
    draw_c = ImageDraw.Draw(circle_mask)
    draw_c.ellipse((4, 4, dog_base_dim - 4, dog_base_dim - 4), fill=255)
    circle_mask = circle_mask.filter(ImageFilter.GaussianBlur(1))

    for f in range(NUM_FRAMES):
        t = f / NUM_FRAMES  # 0.0 to 1.0
        angle = t * 2 * math.pi

        # 512x512 canvas
        img = Image.new('RGBA', (512, 512), c_bg + (255,))
        draw = ImageDraw.Draw(img)

        # 1. Background hexagonal tech grid
        center = (256, 256)
        for r in range(40, 250, 45):
            alpha = int(25 + 15 * math.sin(angle + r))
            draw.circle(center, r, outline=(0, 180, 255, alpha), width=1)

        # 2. Outer Rotating Reticle Ring (Clockwise)
        outer_deg = t * 360
        for i in range(12):
            deg = outer_deg + i * 30
            rad = math.radians(deg)
            p1 = (256 + 242 * math.cos(rad), 256 + 242 * math.sin(rad))
            p2 = (256 + 234 * math.cos(rad), 256 + 234 * math.sin(rad))
            draw.line([p1, p2], fill=c_cyan + (180,), width=2)

        # Outer segmented brackets
        draw_arc_segment(draw, center, 238, outer_deg, outer_deg + 60, c_cyan + (220,), width=3)
        draw_arc_segment(draw, center, 238, outer_deg + 120, outer_deg + 180, c_purple + (220,), width=3)
        draw_arc_segment(draw, center, 238, outer_deg + 240, outer_deg + 300, c_cyan + (220,), width=3)

        # 3. Inner Counter-Rotating Reticle Ring (Counter-Clockwise)
        inner_deg = -t * 360
        draw_arc_segment(draw, center, 206, inner_deg, inner_deg + 45, c_purple + (200,), width=2)
        draw_arc_segment(draw, center, 206, inner_deg + 90, inner_deg + 135, c_green + (200,), width=2)
        draw_arc_segment(draw, center, 206, inner_deg + 180, inner_deg + 225, c_purple + (200,), width=2)
        draw_arc_segment(draw, center, 206, inner_deg + 270, inner_deg + 315, c_green + (200,), width=2)

        # 4. Mascot with subtle breathing float
        float_y = int(4 * math.sin(angle))
        zoom_dim = int(dog_base_dim + 4 * math.sin(angle))
        mascot_frame = dog_resized.resize((zoom_dim, zoom_dim), Image.Resampling.BILINEAR)
        mask_frame = circle_mask.resize((zoom_dim, zoom_dim), Image.Resampling.BILINEAR)

        # Glow halo behind mascot
        halo_r = 185 + int(6 * math.sin(angle))
        draw.ellipse([256 - halo_r, 256 - halo_r, 256 + halo_r, 256 + halo_r], fill=(0, 100, 160, 40))

        dog_pos = (256 - zoom_dim // 2, 256 - zoom_dim // 2 + float_y)
        img.paste(mascot_frame, dog_pos, mask_frame)

        # 5. Sweeping 360 Radar / Laser Scan line
        scan_angle = t * 2 * math.pi
        scan_x = 256 + 200 * math.cos(scan_angle)
        scan_y = 256 + 200 * math.sin(scan_angle)
        draw.line([(256, 256), (scan_x, scan_y)], fill=c_cyan + (160,), width=2)

        # 6. Status badge at bottom
        badge_box = [156, 468, 356, 498]
        draw.rounded_rectangle(badge_box, radius=6, fill=(10, 16, 32, 230), outline=c_cyan + (180,), width=1)
        font_sm = get_font(12)
        draw.text((195, 474), "ZERO-TRUST ACTIVE", fill=(255, 255, 255, 240), font=font_sm)

        # Pulsing green status LED
        led_alpha = int(180 + 75 * math.sin(angle * 2))
        draw.ellipse([176, 479, 186, 489], fill=c_green + (led_alpha,))

        frames.append(img.convert('RGB'))

    # Save GIF
    gif_path = os.path.join(OUTPUT_DIR, "shizu_avatar_animated.gif")
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=True
    )
    print(f"[OK] Saved {gif_path} ({os.path.getsize(gif_path) / 1024:.1f} KB)")

def generate_banner():
    """Generates 960x384 animated banner (5:2 Discord ratio) with 3D rolling grid, mascot crest, and metallic gleam."""
    print(f"[*] Rendering Animated Banner ({NUM_FRAMES} frames)...")
    frames = []

    c_cyan = (0, 240, 255)
    c_purple = (180, 60, 255)
    c_bg = (5, 7, 14)

    raw_dog = Image.open(SRC_MASCOT).convert('RGBA')
    raw_dog = raw_dog.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))
    crest_dim = 240
    dog_crest = raw_dog.resize((crest_dim, crest_dim), Image.Resampling.LANCZOS)

    crest_mask = Image.new('L', (crest_dim, crest_dim), 0)
    draw_cm = ImageDraw.Draw(crest_mask)
    draw_cm.ellipse((4, 4, crest_dim - 4, crest_dim - 4), fill=255)

    font_title = get_font(46)
    font_sub = get_font(18)

    for f in range(NUM_FRAMES):
        t = f / NUM_FRAMES
        angle = t * 2 * math.pi

        img = Image.new('RGBA', (960, 384), c_bg + (255,))
        draw = ImageDraw.Draw(img)

        # 1. 3D Perspective Rolling Cyber Grid Floor
        vanishing_y = 120
        grid_offset = (t * 40) % 40
        # Horizontal lines with exponential perspective spacing
        for i in range(12):
            y = int(vanishing_y + (i * 22 + grid_offset) ** 1.15)
            if y < 384:
                alpha = int(min(180, (y - vanishing_y) * 0.8))
                draw.line([(0, y), (960, y)], fill=(0, 160, 230, alpha), width=1)

        # Perspective vertical rays
        for x in range(-200, 1160, 70):
            p_top = (480 + (x - 480) * 0.15, vanishing_y)
            p_bot = (x, 384)
            draw.line([p_top, p_bot], fill=(0, 120, 200, 45), width=1)

        # 2. Left Side: Mascot Shield Hologram Crest
        crest_center = (180, 192)
        float_y = int(3 * math.sin(angle))
        cx, cy = crest_center

        # Rotating outer halo
        halo_deg = t * 360
        draw_arc_segment(draw, (cx, cy + float_y), 135, halo_deg, halo_deg + 90, c_cyan + (210,), width=3)
        draw_arc_segment(draw, (cx, cy + float_y), 135, halo_deg + 180, halo_deg + 270, c_purple + (210,), width=3)

        # Paste Mascot in Crest
        crest_pos = (cx - crest_dim // 2, cy - crest_dim // 2 + float_y)
        img.paste(dog_crest, crest_pos, crest_mask)

        # Orbiting satellite blip
        sat_rad = math.radians(halo_deg * 2)
        sat_x = cx + 135 * math.cos(sat_rad)
        sat_y = cy + float_y + 135 * math.sin(sat_rad)
        draw.ellipse([sat_x - 5, sat_y - 5, sat_x + 5, sat_y + 5], fill=(0, 255, 200, 240))

        # 3. Right Side: Typography & Specular Gleam
        # Text "SHIZU SECURITY"
        text_x, text_y = 360, 130
        draw.text((text_x, text_y), "SHIZU SECURITY", fill=(255, 255, 255, 240), font=font_title)

        # Specular light gleam bar sweeping across text
        gleam_x = text_x + int(t * 540)
        draw.line([(gleam_x, text_y - 5), (gleam_x - 30, text_y + 55)], fill=(255, 255, 255, 180), width=4)
        draw.line([(gleam_x + 10, text_y - 5), (gleam_x - 20, text_y + 55)], fill=c_cyan + (120,), width=2)

        # Subtitle
        draw.text((text_x, text_y + 65), "ZERO-TRUST DISCORD DEFENSE • v2.3 CORE", fill=c_cyan + (230,), font=font_sub)

        # 4. Animated Equalizer Waveform Bars (Bottom Right)
        eq_x = 360
        for b in range(24):
            bar_h = max(4, int(18 + 14 * math.sin(angle * 3 + b * 0.45) + 6 * math.cos(angle * 2 + b)))
            bar_y = 290 - bar_h
            bx = eq_x + b * 16
            draw.rounded_rectangle([bx, bar_y, bx + 10, 290], radius=2, fill=c_purple + (190,))

        # Status Pill
        draw.rounded_rectangle([750, 18, 935, 48], radius=6, fill=(10, 16, 32, 220), outline=c_cyan + (150,), width=1)
        draw.text((780, 24), "SYSTEM SECURED", fill=(255, 255, 255, 230), font=get_font(12))
        draw.ellipse([764, 28, 774, 38], fill=(0, 255, 170, 220))

        frames.append(img.convert('RGB'))

    # Save Banner GIF
    gif_path = os.path.join(OUTPUT_DIR, "shizu_banner_animated.gif")
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=True
    )
    print(f"[OK] Saved {gif_path} ({os.path.getsize(gif_path) / 1024:.1f} KB)")

if __name__ == "__main__":
    generate_avatar()
    generate_banner()
    print("\n[SUCCESS] Generated brand new animated avatar and banner for Shizu Security!")
