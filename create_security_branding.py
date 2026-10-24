import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

BRAIN_DIR = r"C:\Users\xdvip\.gemini\antigravity\brain\48563075-5ecf-4705-82fe-f0e55fa34e36"
AVATAR_SRC = os.path.join(BRAIN_DIR, "shizu_security_avatar_1792736265984.jpg")
BANNER_SRC = os.path.join(BRAIN_DIR, "shizu_security_banner_1792736288444.jpg")

ASSETS_DIR = r"c:\Users\xdvip\Videos\security bot\assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

AVATAR_OUT_STATIC = os.path.join(ASSETS_DIR, "shizu_avatar_security.png")
BANNER_OUT_STATIC = os.path.join(ASSETS_DIR, "shizu_banner_security.png")
AVATAR_OUT_GIF = os.path.join(ASSETS_DIR, "shizu_avatar_animated.gif")
BANNER_OUT_GIF = os.path.join(ASSETS_DIR, "shizu_banner_animated.gif")

# Also save copies directly in brain artifact directory for display
AVATAR_ARTIFACT_PNG = os.path.join(BRAIN_DIR, "shizu_avatar_security.png")
BANNER_ARTIFACT_PNG = os.path.join(BRAIN_DIR, "shizu_banner_security.png")
AVATAR_ARTIFACT_GIF = os.path.join(BRAIN_DIR, "shizu_avatar_animated.gif")
BANNER_ARTIFACT_GIF = os.path.join(BRAIN_DIR, "shizu_banner_animated.gif")

def process_static_assets():
    print("[1/3] Processing static security assets...")
    # Avatar (1024x1024)
    im_av = Image.open(AVATAR_SRC).convert("RGBA")
    im_av.save(AVATAR_OUT_STATIC, "PNG")
    im_av.save(AVATAR_ARTIFACT_PNG, "PNG")
    print(f"  [OK] Saved Avatar Static: {AVATAR_OUT_STATIC}")

    # Banner (Crop to 5:2 ratio: 1280x512)
    im_bn = Image.open(BANNER_SRC).convert("RGBA")
    w, h = im_bn.size
    target_ratio = 5.0 / 2.0
    crop_h = int(w / target_ratio)
    if crop_h > h:
        crop_h = h
        crop_w = int(h * target_ratio)
        left = (w - crop_w) // 2
        top = 0
        right = left + crop_w
        bottom = h
    else:
        left = 0
        top = (h - crop_h) // 2
        right = w
        bottom = top + crop_h

    im_bn_cropped = im_bn.crop((left, top, right, bottom)).resize((1280, 512), Image.Resampling.LANCZOS)
    im_bn_cropped.save(BANNER_OUT_STATIC, "PNG")
    im_bn_cropped.save(BANNER_ARTIFACT_PNG, "PNG")
    print(f"  [OK] Saved Banner Static (5:2 ratio): {BANNER_OUT_STATIC}")

def generate_animated_avatar(num_frames=36, size=512):
    print(f"[2/3] Generating Animated Security Avatar ({num_frames} frames @ {size}x{size})...")
    base = Image.open(AVATAR_SRC).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    cx, cy = size // 2, size // 2
    r_outer = int(size * 0.46)
    r_inner = int(size * 0.41)

    frames = []
    for f in range(num_frames):
        progress = f / num_frames
        angle_rad = progress * 2 * math.pi
        angle_deg = progress * 360.0

        frame = base.copy()
        overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 1. Outer Cyan Rotating Reticle (Clockwise)
        for i in range(12):
            tick_ang = angle_rad + (i * math.pi / 6)
            x1 = cx + math.cos(tick_ang) * (r_outer - 6)
            y1 = cy + math.sin(tick_ang) * (r_outer - 6)
            x2 = cx + math.cos(tick_ang) * (r_outer + 4)
            y2 = cy + math.sin(tick_ang) * (r_outer + 4)
            draw.line([(x1, y1), (x2, y2)], fill=(6, 182, 212, 190), width=2)

        # Outer Reticle Arcs
        draw.arc([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
                 start=int(angle_deg), end=int(angle_deg + 60), fill=(6, 182, 212, 220), width=3)
        draw.arc([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
                 start=int(angle_deg + 120), end=int(angle_deg + 180), fill=(6, 182, 212, 220), width=3)
        draw.arc([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
                 start=int(angle_deg + 240), end=int(angle_deg + 300), fill=(6, 182, 212, 220), width=3)

        # 2. Inner Red/Crimson Counter-Rotating Reticle (Counter-Clockwise)
        ccw_deg = -angle_deg * 1.5
        draw.arc([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner],
                 start=int(ccw_deg), end=int(ccw_deg + 45), fill=(239, 68, 68, 200), width=2)
        draw.arc([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner],
                 start=int(ccw_deg + 180), end=int(ccw_deg + 225), fill=(239, 68, 68, 200), width=2)

        # 3. 360-Degree Sweeping Radar Laser Beam
        radar_len = int(size * 0.44)
        rx = cx + math.cos(angle_rad) * radar_len
        ry = cy + math.sin(angle_rad) * radar_len
        draw.line([(cx, cy), (rx, ry)], fill=(34, 211, 238, 140), width=2)

        # 4. Central Optic Core Pulse (Breathing cyan/red energy)
        pulse = 0.5 + 0.5 * math.sin(progress * 2 * math.pi)
        pulse_r = int(14 + 6 * pulse)
        draw.ellipse([cx - pulse_r, cy - pulse_r, cx + pulse_r, cy + pulse_r],
                     outline=(239, 68, 68, int(150 + 100 * pulse)), width=2)

        # 5. Status Pill at bottom: [DEFENSE ACTIVE]
        pill_w, pill_h = 170, 24
        px1 = cx - pill_w // 2
        py1 = size - 40
        px2 = cx + pill_w // 2
        py2 = py1 + pill_h
        draw.rounded_rectangle([px1, py1, px2, py2], radius=12, fill=(15, 23, 42, 220), outline=(6, 182, 212, 180), width=1)
        # Pulsing neon green LED dot
        led_alpha = int(180 + 75 * math.sin(progress * 4 * math.pi))
        draw.ellipse([px1 + 8, py1 + 6, px1 + 18, py1 + 16], fill=(34, 197, 94, led_alpha))

        # Composite frame
        composed = Image.alpha_composite(frame, overlay).convert("RGB")
        # Quantize with clean adaptive palette
        paletted = composed.quantize(colors=128, method=Image.Resampling.LANCZOS)
        frames.append(paletted)

    # Save animated GIF
    frames[0].save(
        AVATAR_OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=40,  # 25 FPS
        loop=0,
        optimize=True
    )
    frames[0].save(
        AVATAR_ARTIFACT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=40,
        loop=0,
        optimize=True
    )
    print(f"  [OK] Saved Animated Avatar GIF: {AVATAR_OUT_GIF} ({os.path.getsize(AVATAR_OUT_GIF)/1024:.1f} KB)")

def generate_animated_banner(num_frames=36, width=960, height=384):
    print(f"[3/3] Generating Animated Security Banner ({num_frames} frames @ {width}x{height})...")
    # Base banner cropped to 5:2 and resized
    im_bn = Image.open(BANNER_SRC).convert("RGBA")
    w, h = im_bn.size
    crop_h = int(w * (height / width))
    top = (h - crop_h) // 2
    base = im_bn.crop((0, top, w, top + crop_h)).resize((width, height), Image.Resampling.LANCZOS)

    frames = []
    for f in range(num_frames):
        progress = f / num_frames
        frame = base.copy()
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 1. Scanning Laser Beam moving left to right
        laser_x = int(progress * width)
        draw.line([(laser_x, 0), (laser_x, height)], fill=(6, 182, 212, 160), width=3)
        # Laser glow edges
        draw.line([(laser_x - 2, 0), (laser_x - 2, height)], fill=(6, 182, 212, 60), width=2)
        draw.line([(laser_x + 2, 0), (laser_x + 2, height)], fill=(6, 182, 212, 60), width=2)

        # 2. Corner Tactical Brackets
        bracket_len = 28
        for (bx, by, dx, dy) in [(20, 20, 1, 1), (width - 20, 20, -1, 1), (20, height - 20, 1, -1), (width - 20, height - 20, -1, -1)]:
            draw.line([(bx, by), (bx + dx * bracket_len, by)], fill=(239, 68, 68, 200), width=2)
            draw.line([(bx, by), (bx, by + dy * bracket_len)], fill=(239, 68, 68, 200), width=2)

        # 3. Specular Light Shimmer across top and bottom cyber bars
        shimmer_x = int(((progress * 1.5) % 1.0) * width)
        draw.line([(shimmer_x - 40, 10), (shimmer_x + 40, 10)], fill=(255, 255, 255, 180), width=2)
        draw.line([(shimmer_x - 40, height - 10), (shimmer_x + 40, height - 10)], fill=(6, 182, 212, 180), width=2)

        composed = Image.alpha_composite(frame, overlay).convert("RGB")
        paletted = composed.quantize(colors=128, method=Image.Resampling.LANCZOS)
        frames.append(paletted)

    frames[0].save(
        BANNER_OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=40,
        loop=0,
        optimize=True
    )
    frames[0].save(
        BANNER_ARTIFACT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=40,
        loop=0,
        optimize=True
    )
    print(f"  [OK] Saved Animated Banner GIF: {BANNER_OUT_GIF} ({os.path.getsize(BANNER_OUT_GIF)/1024:.1f} KB)")

if __name__ == "__main__":
    process_static_assets()
    generate_animated_avatar()
    generate_animated_banner()
    print("\n[ALL BRANDING ASSETS SUCCESSFULLY GENERATED!]")
