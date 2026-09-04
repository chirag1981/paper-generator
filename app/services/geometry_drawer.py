import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

def generate_zigzag_diagram(output_path: str, vertices=None):
    """Generates a high-res zigzag polyline diagram with labeled vertices."""
    if not vertices:
        vertices = [
            ('L', 1.0, 1.0, -0.25),
            ('M', 2.0, 2.2, 0.2),
            ('P', 3.0, 1.2, -0.25),
            ('Q', 4.0, 2.4, 0.2),
            ('R', 5.0, 1.2, -0.25)
        ]
    
    fig, ax = plt.subplots(figsize=(6, 2.4), dpi=300)
    x_vals = [v[1] for v in vertices]
    y_vals = [v[2] for v in vertices]
    
    ax.plot(x_vals, y_vals, color='#1e293b', linewidth=2.5, zorder=2)
    for name, x, y, oy in vertices:
        ax.scatter(x, y, color='#0284c7', s=70, zorder=3)
        ax.text(x, y + oy, name, fontsize=13, fontweight='bold', ha='center', va='center', color='#0f172a')
        
    ax.set_xlim(min(x_vals) - 0.5, max(x_vals) + 0.5)
    ax.set_ylim(min(y_vals) - 0.6, max(y_vals) + 0.6)
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', transparent=False, facecolor='white')
    plt.close()
    return output_path

def generate_lines_rays_diagram(output_path: str):
    """Generates a geometry diagram with intersecting lines and rays (G-A-C-E, Ray AB, Line DF)."""
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=300)
    # Horizontal line GE
    ax.annotate('', xy=(6.5, 2), xytext=(0.5, 2),
                arrowprops=dict(arrowstyle='<->', color='#1e293b', lw=2.2))

    # Vertical ray from A to B
    ax.annotate('', xy=(2.5, 4.2), xytext=(2.5, 2),
                arrowprops=dict(arrowstyle='->', color='#1e293b', lw=2.2))

    # Transversal line through C: from F to D
    ax.annotate('', xy=(5.2, 4.2), xytext=(4.0, 0.8),
                arrowprops=dict(arrowstyle='<->', color='#1e293b', lw=2.2))

    geom_points = {
        'G': (1.5, 2.0, -0.3, 0),
        'A': (2.5, 2.0, -0.3, 0.15),
        'C': (4.5, 2.0, -0.3, 0.15),
        'E': (5.8, 2.0, -0.3, 0),
        'B': (2.5, 4.0, 0.1, 0.25),
        'D': (5.1, 3.9, 0.1, 0.25),
        'F': (4.1, 1.0, 0.1, 0.25)
    }

    for name, (x, y, oy, ox) in geom_points.items():
        ax.scatter(x, y, color='#0284c7', s=60, zorder=4)
        ax.text(x + ox, y + oy, name, fontsize=13, fontweight='bold', ha='center', va='center', color='#0f172a')

    ax.set_xlim(0, 7)
    ax.set_ylim(0.4, 4.6)
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', transparent=False, facecolor='white')
    plt.close()
    return output_path

def generate_girl_icon(output_dir: str):
    """Generates full and half girl icons for pictographs."""
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, 'girl_full.png')
    half_path = os.path.join(output_dir, 'girl_half.png')

    if not (os.path.exists(full_path) and os.path.exists(half_path)):
        def create_icon(half=False):
            img = Image.new('RGBA', (80, 80), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            # Head
            draw.ellipse([25, 8, 55, 38], fill='#f59e0b', outline='#1e293b', width=2)
            # Hair buns
            draw.ellipse([16, 14, 28, 26], fill='#b45309', outline='#1e293b', width=2)
            draw.ellipse([52, 14, 64, 26], fill='#b45309', outline='#1e293b', width=2)
            # Eyes & Smile
            draw.ellipse([32, 20, 36, 24], fill='#1e293b')
            draw.ellipse([44, 20, 48, 24], fill='#1e293b')
            draw.arc([35, 24, 45, 32], start=0, end=180, fill='#1e293b', width=2)
            # Dress
            draw.polygon([(40, 38), (18, 68), (62, 68)], fill='#ec4899', outline='#1e293b', width=2)
            # Arms
            draw.line([(30, 46), (14, 56)], fill='#1e293b', width=2)
            draw.line([(50, 46), (66, 56)], fill='#1e293b', width=2)
            # Legs
            draw.line([(32, 68), (32, 78)], fill='#1e293b', width=2)
            draw.line([(48, 68), (48, 78)], fill='#1e293b', width=2)
            
            if half:
                img = img.crop((0, 0, 40, 80))
            return img

        create_icon(False).save(full_path)
        create_icon(True).save(half_path)

    return full_path, half_path

def generate_pictograph_chart(output_path: str, classes_data=None, key_value=4):
    """Generates a complete pixel-perfect pictograph chart image."""
    if not classes_data:
        classes_data = [
            ('Class 1', 6, 0),
            ('Class 2', 4, 1),
            ('Class 3', 5, 0),
            ('Class 4', 3, 1),
            ('Class 5', 2, 1),
            ('Class 6', 4, 0),
            ('Class 7', 3, 0),
            ('Class 8', 1, 1),
        ]
        
    out_dir = os.path.dirname(output_path) or '.'
    full_icon_path, half_icon_path = generate_girl_icon(out_dir)
    
    full_icon = Image.open(full_icon_path).resize((48, 48), Image.Resampling.LANCZOS)
    half_icon = Image.open(half_icon_path).resize((24, 48), Image.Resampling.LANCZOS)

    w, h = 900, 620
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([20, 20, w-20, h-20], radius=8, outline='#1e293b', width=2, fill='#ffffff')
    draw.rectangle([22, 22, w-22, 80], fill='#f1f5f9')
    draw.line([20, 80, w-20, 80], fill='#1e293b', width=2)
    draw.line([180, 20, 180, h-20], fill='#cbd5e1', width=2)

    try:
        font_header = ImageFont.truetype('arialbd.ttf', 20)
        font_key = ImageFont.truetype('arialbd.ttf', 16)
        font_body = ImageFont.truetype('arialbd.ttf', 18)
    except:
        font_header = ImageFont.load_default()
        font_key = font_header
        font_body = font_header

    draw.text((100, 40), 'Class', font=font_header, fill='#0f172a', anchor='mm')
    draw.text((360, 40), 'Number of Girl Students', font=font_header, fill='#0f172a', anchor='mm')
    draw.text((580, 40), 'Key:  ', font=font_key, fill='#334155', anchor='mm')
    img.paste(full_icon.resize((26, 26)), (615, 27), full_icon.resize((26, 26)))
    draw.text((690, 40), f'= {key_value} Girls,', font=font_key, fill='#334155', anchor='mm')
    img.paste(half_icon.resize((13, 26)), (745, 27), half_icon.resize((13, 26)))
    draw.text((810, 40), f'= {key_value//2} Girls', font=font_key, fill='#334155', anchor='mm')

    row_h = (h - 20 - 80) / max(len(classes_data), 1)

    for i, (cls, fulls, halfs) in enumerate(classes_data):
        y_top = 80 + i * row_h
        y_mid = y_top + row_h / 2
        if i % 2 == 1:
            draw.rectangle([22, y_top, w-22, y_top + row_h], fill='#f8fafc')
        if i > 0:
            draw.line([20, y_top, w-20, y_top], fill='#e2e8f0', width=1)
        
        draw.text((100, y_mid), cls, font=font_body, fill='#334155', anchor='mm')
        
        x_start = 220
        for f in range(fulls):
            img.paste(full_icon, (int(x_start + f * 60), int(y_mid - 24)), full_icon)
        if halfs > 0:
            img.paste(half_icon, (int(x_start + fulls * 60), int(y_mid - 24)), half_icon)

    img.save(output_path, dpi=(300, 300))
    return output_path
