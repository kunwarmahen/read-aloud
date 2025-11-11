from PIL import Image, ImageDraw, ImageFont

def create_icon(size):
    # Create a gradient background
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient-like circles
    for i in range(5):
        color_val = int(102 + (118 - 102) * i / 5)
        circle_size = int(size * (0.9 - i * 0.15))
        pos = (size - circle_size) // 2
        draw.ellipse([pos, pos, pos + circle_size, pos + circle_size], 
                     fill=(color_val, 126, 234))
    
    # Draw speaker icon
    center_x, center_y = size // 2, size // 2
    speaker_width = size // 3
    
    # Speaker cone
    points = [
        (center_x - speaker_width//2, center_y - speaker_width//4),
        (center_x - speaker_width//4, center_y - speaker_width//4),
        (center_x - speaker_width//4, center_y + speaker_width//4),
        (center_x - speaker_width//2, center_y + speaker_width//4),
    ]
    draw.polygon(points, fill='white')
    
    # Speaker rectangle
    draw.rectangle([
        center_x - speaker_width//4, 
        center_y - speaker_width//6,
        center_x, 
        center_y + speaker_width//6
    ], fill='white')
    
    # Sound waves
    wave_offset = speaker_width // 6
    for i in range(1, 3):
        arc_size = wave_offset * i * 2
        draw.arc([
            center_x - wave_offset, 
            center_y - arc_size//2,
            center_x + arc_size, 
            center_y + arc_size//2
        ], 300, 60, fill='white', width=max(2, size//32))
    
    return img

# Create all icon sizes
for size in [16, 48, 128]:
    icon = create_icon(size)
    icon.save(f'icon{size}.png')
    print(f'Created icon{size}.png')

