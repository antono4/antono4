#!/usr/bin/env python3
"""Realistic Snake Animation Generator"""
import requests
from datetime import datetime, timedelta

USERNAME = "antono4"
OUTPUT_FILE = "../output/snake.gif"

# Green theme colors for snake
COLORS = {
    0: "#0d1117", 1: "#22c55e", 2: "#16a34a", 3: "#15803d", 4: "#f64f59", 5: "#064e85",
}

def get_contributions(username):
    url = f"https://github-contributions-api.jogruber.de/v4/{username}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def create_realistic_snake_path():
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

def generate_frames(contributions, num_frames=50, cell_size=15, gap=2):
    from PIL import Image, ImageDraw
    
    width = 53 * (cell_size + gap) + 40
    height = 7 * (cell_size + gap) + 80
    
    frames = []
    path = create_realistic_snake_path()
    
    contrib_by_date = {}
    for day in contributions.get('contributions', []):
        contrib_by_date[day['date']] = day['count']
    
    start_date = datetime.strptime(contributions['contributions'][0]['date'], '%Y-%m-%d')
    
    for frame_idx in range(num_frames):
        frame = Image.new('RGBA', (width, height), (13, 17, 23, 255))
        draw = ImageDraw.Draw(frame)
        
        # Draw contribution grid
        for week in range(53):
            for day in range(7):
                current_date = start_date + timedelta(weeks=week, days=day)
                date_str = current_date.strftime('%Y-%m-%d')
                count = contrib_by_date.get(date_str, 0)
                level = min(5, count // 4) if count > 0 else 0
                x = week * (cell_size + gap) + 20
                y = day * (cell_size + gap) + 40
                color = COLORS.get(level, COLORS[0])
                draw.rounded_rectangle([x, y, x + cell_size - 1, y + cell_size - 1], radius=3, fill=hex_to_rgba(color))
        
        # Snake animation
        snake_progress = int((frame_idx / num_frames) * len(path))
        body_length = min(snake_progress, 90)
        
        for i in range(body_length):
            idx = snake_progress - i - 1
            if 0 <= idx < len(path):
                week, day = path[idx]
                x = week * (cell_size + gap) + 20 + cell_size // 2
                y = day * (cell_size + gap) + 40 + cell_size // 2
                thickness_ratio = 1.0 - (abs(i - body_length/2) / body_length) * 0.5
                size = max(3, int((cell_size // 2 - 1) * thickness_ratio))
                
                # Gradient body color - Green shades
                if i < 20:
                    # Bright green near head
                    r, g, b = 34, 197, 94
                elif i < 40:
                    # Transition to dark green
                    t = (i - 20) / 20
                    r, g, b = int(34 + (21-34)*t), int(197 + (128-197)*t), int(94 + (71-94)*t)
                elif i < 60:
                    # Dark green to forest green
                    t = (i - 40) / 20
                    r, g, b = int(21 + (18-21)*t), int(128 + (99-128)*t), int(71 + (54-71)*t)
                else:
                    # Tail fading
                    t = (i - 60) / 30
                    r, g, b = int(18 + (10-18)*t), int(99 + (60-99)*t), int(54 + (40-54)*t)
                
                alpha = max(100, 255 - (i - 50) * 3) if i > 50 else 255
                draw.ellipse([x-size, y-size, x+size, y+size], fill=(r, g, b, alpha))
                if i < 50:
                    draw.ellipse([x-size+2, y-size+2, x-size+max(1,size//2), y-size+max(1,size//2)], fill=(255,255,255,60))
        
        # Realistic snake head
        if 0 < snake_progress <= len(path):
            week, day = path[snake_progress - 1]
            hx = week * (cell_size + gap) + 20 + cell_size // 2
            hy = day * (cell_size + gap) + 40 + cell_size // 2
            hs = cell_size // 2 + 4
            
            # Shadow
            draw.ellipse([hx-hs+2, hy-hs+4, hx+hs+2, hy+hs+4], fill=(0, 80, 40, 200))
            # Head - Green
            draw.ellipse([hx-hs, hy-hs, hx+hs, hy+hs], fill=(34, 197, 94, 255))
            draw.ellipse([hx-hs//2, hy-hs//2, hx+hs//2, hy+hs//2], fill=(21, 160, 70, 255))
            
            # Eyes with vertical pupils
            for ex in [hx-5, hx+3]:
                draw.ellipse([ex-2, hy-6, ex+1, hy-2], fill=(0, 50, 80))  # Socket
                draw.ellipse([ex-1, hy-5, ex, hy-3], fill=(20, 20, 20))  # Pupil
                draw.ellipse([ex-1, hy-5, ex, hy-4], fill=(255,255,255,150))  # Shine
            
            # Forked tongue
            tongue_out = frame_idx % 15 < 10
            if tongue_out:
                tl = frame_idx % 15
                draw.line([hx, hy+hs, hx, hy+hs+tl], fill=(220, 50, 50), width=2)
                if tl > 4:
                    draw.line([hx, hy+hs+tl, hx-3, hy+hs+tl+4], fill=(220, 50, 50), width=1)
                    draw.line([hx, hy+hs+tl, hx+3, hy+hs+tl+4], fill=(220, 50, 50), width=1)
        
        frames.append(frame)
    
    return frames

def main():
    print("Fetching contributions...")
    contributions = get_contributions(USERNAME)
    if not contributions:
        print("Failed!")
        return
    
    print("Generating frames...")
    frames = generate_frames(contributions, num_frames=50)
    
    print("Saving...")
    frames[0].save(OUTPUT_FILE, save_all=True, append_images=frames[1:], duration=80, loop=0)
    print("Done!")

if __name__ == "__main__":
    main()
