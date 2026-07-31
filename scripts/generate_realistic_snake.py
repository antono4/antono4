#!/usr/bin/env python3
"""
Realistic 3D Snake Animation Generator
- Green contribution grid
- 3D realistic snake with shadows and highlights
"""
import requests
from datetime import datetime, timedelta
import math

USERNAME = "antono4"
OUTPUT_FILE = "../output/snake.gif"

# GitHub exact contribution colors (dark mode)
CONTRIB_COLORS = {
    0: "#161b22",      # No contribution
    1: "#0e4429",      # Level 1 (darkest green)
    2: "#006d32",      # Level 2 (dark green)
    3: "#26a641",      # Level 3 (medium green)
    4: "#39d353",      # Level 4 (bright green)
}

def get_contributions(username):
    url = f"https://github-contributions-api.jogruber.de/v4/{username}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def create_snake_path():
    path = []
    for week in range(53):
        if week % 2 == 0:
            for day in range(7):
                path.append((week, day))
        else:
            for day in range(6, -1, -1):
                path.append((week, day))
    return path

def hex_to_rgba(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)

def draw_3d_ellipse(draw, cx, cy, rx, ry, color, shadow_offset=2):
    """Draw a 3D-looking ellipse with gradient effect"""
    # Shadow
    shadow_color = (max(0, color[0]//3), max(0, color[1]//3), max(0, color[2]//3), 180)
    draw.ellipse([cx-rx+shadow_offset, cy-ry+shadow_offset, cx+rx+shadow_offset, cy+ry+shadow_offset], fill=shadow_color)
    # Main ellipse
    draw.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=color)
    # Highlight
    highlight_color = (min(255, color[0]+60), min(255, color[1]+60), min(255, color[2]+60), 200)
    draw.ellipse([cx-rx//2, cy-ry//2, cx-rx//4, cy-ry//4], fill=highlight_color)

def generate_frames(contributions, num_frames=60, cell_size=11, gap=3):
    from PIL import Image, ImageDraw
    
    width = 53 * (cell_size + gap) + 30
    height = 7 * (cell_size + gap) + 80
    
    frames = []
    path = create_snake_path()
    
    contrib_by_date = {}
    for day in contributions.get('contributions', []):
        contrib_by_date[day['date']] = day['count']
    
    start_date = datetime.strptime(contributions['contributions'][0]['date'], '%Y-%m-%d')
    
    for frame_idx in range(num_frames):
        frame = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        
        # Draw contribution grid - exact GitHub style (no extra effects)
        for week in range(53):
            for day in range(7):
                current_date = start_date + timedelta(weeks=week, days=day)
                date_str = current_date.strftime('%Y-%m-%d')
                count = contrib_by_date.get(date_str, 0)
                # GitHub level calculation: 1-3=1, 4-6=2, 7-9=3, 10+=4
                level = min(4, (count + 2) // 3) if count > 0 else 0
                x = week * (cell_size + gap) + 15
                y = day * (cell_size + gap) + 40
                color = hex_to_rgba(CONTRIB_COLORS.get(level, CONTRIB_COLORS[0]))
                
                # Simple rounded square like GitHub
                draw.rounded_rectangle([x, y, x + cell_size, y + cell_size], radius=2, fill=color)
        
        # Calculate snake position
        snake_progress = int((frame_idx / num_frames) * len(path))
        body_length = min(snake_progress, 100)
        
        # Draw snake body with 3D effect
        for i in range(body_length):
            idx = snake_progress - i - 1
            if 0 <= idx < len(path):
                week, day = path[idx]
                cx = week * (cell_size + gap) + 15 + cell_size // 2
                cy = day * (cell_size + gap) + 40 + cell_size // 2
                
                # Thickness varies - thicker in middle
                center_ratio = abs(i - body_length/2) / (body_length/2) if body_length > 0 else 1
                thickness = max(3, int((cell_size // 2) * (1 - center_ratio * 0.4)))
                
                # Snake body color gradient - natural snake colors
                if i < 25:
                    # Near head - bright
                    r, g, b = 210, 180, 140  # Tan/beige
                elif i < 50:
                    t = (i - 25) / 25
                    r, g, b = int(210 + (180-210)*t), int(180 + (140-180)*t), int(140 + (100-140)*t)
                elif i < 75:
                    t = (i - 50) / 25
                    r, g, b = int(180 + (120-180)*t), int(140 + (80-140)*t), int(100 + (60-100)*t)
                else:
                    t = (i - 75) / 25
                    r, g, b = int(120 + (80-120)*t), int(80 + (50-80)*t), int(60 + (40-60)*t)
                
                alpha = max(80, 255 - (i - 60) * 4) if i > 60 else 255
                body_color = (r, g, b, alpha)
                
                # 3D body segment
                shadow = (max(0, r//3), max(0, g//3), max(0, b//3), alpha)
                draw.ellipse([cx-thickness+2, cy-thickness+3, cx+thickness+2, cy+thickness+3], fill=shadow)
                draw.ellipse([cx-thickness, cy-thickness, cx+thickness, cy+thickness], fill=body_color)
                
                # Scale pattern / shine
                if i % 4 == 0 and i < 70:
                    shine = (min(255, r+50), min(255, g+50), min(255, b+50), 150)
                    draw.ellipse([cx-thickness//2+1, cy-thickness//2+1, cx+thickness//4, cy+thickness//4], fill=shine)
                
                # Body pattern stripes
                if i % 8 < 4 and i < 80:
                    stripe_alpha = 40
                    stripe_color = (r//2, g//2, b//2, stripe_alpha)
                    draw.ellipse([cx-thickness//2, cy-thickness//2, cx+thickness//2, cy+thickness//2], fill=stripe_color)
        
        # Draw 3D Snake Head
        if 0 < snake_progress <= len(path):
            week, day = path[snake_progress - 1]
            hx = week * (cell_size + gap) + 15 + cell_size // 2
            hy = day * (cell_size + gap) + 40 + cell_size // 2
            hs = cell_size // 2 + 4
            
            # Deep shadow for 3D effect
            draw.ellipse([hx-hs+3, hy-hs+5, hx+hs+3, hy+hs+5], fill=(20, 15, 10, 220))
            # Medium shadow
            draw.ellipse([hx-hs+2, hy-hs+4, hx+hs+2, hy+hs+4], fill=(60, 45, 30, 200))
            
            # Head base - tan color
            head_base = (210, 180, 140, 255)
            draw.ellipse([hx-hs, hy-hs, hx+hs, hy+hs], fill=head_base)
            
            # Head pattern (scales)
            draw.ellipse([hx-hs//2, hy-hs//2, hx+hs//2, hy+hs//2], fill=(190, 160, 120, 255))
            
            # Scale details around head
            for angle in range(0, 360, 60):
                sx = hx + int(math.cos(math.radians(angle)) * hs * 0.6)
                sy = hy + int(math.sin(math.radians(angle)) * hs * 0.6)
                draw.ellipse([sx-2, sy-2, sx+2, sy+2], fill=(170, 140, 100, 200))
            
            # Eyes with 3D depth
            eye_positions = [(hx - 6, hy - 4), (hx + 4, hy - 4)]
            for ex, ey in eye_positions:
                # Eye socket (deep shadow)
                draw.ellipse([ex-4, ey-6, ex+2, ey-1], fill=(30, 20, 10, 255))
                # Eye white/outer
                draw.ellipse([ex-3, ey-5, ex+1, ey-2], fill=(220, 200, 150, 255))
                # Iris
                draw.ellipse([ex-2, ey-4, ex, ey-2], fill=(139, 90, 43, 255))
                # Vertical pupil
                draw.ellipse([ex-1, ey-4, ex, ey-3], fill=(0, 0, 0, 255))
                # Eye shine
                draw.point([ex-1, ey-4], fill=(255, 255, 255, 200))
            
            # Nostrils
            draw.ellipse([hx-3, hy+2, hx-1, hy+4], fill=(80, 60, 40, 255))
            draw.ellipse([hx+1, hy+2, hx+3, hy+4], fill=(80, 60, 40, 255))
            
            # Forked tongue with animation
            tongue_frame = frame_idx % 20
            if tongue_frame < 14:
                tongue_len = min(12, tongue_frame)
                # Tongue base (red)
                draw.line([hx, hy+hs, hx, hy+hs+tongue_len], fill=(220, 50, 50), width=2)
                # Forked tongue
                if tongue_len > 5:
                    draw.line([hx, hy+hs+tongue_len, hx-4, hy+hs+tongue_len+5], fill=(220, 50, 50), width=1)
                    draw.line([hx, hy+hs+tongue_len, hx+4, hy+hs+tongue_len+5], fill=(220, 50, 50), width=1)
        
        frames.append(frame)
    
    return frames

def main():
    print("Fetching contributions...")
    contributions = get_contributions(USERNAME)
    if not contributions:
        print("Failed!")
        return
    
    print("Generating 60 frames with 3D snake...")
    frames = generate_frames(contributions, num_frames=60)
    
    print("Saving...")
    frames[0].save(OUTPUT_FILE, save_all=True, append_images=frames[1:], duration=70, loop=0, optimize=True)
    print("Done!")

if __name__ == "__main__":
    main()
