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


def generate_clock_diagram(output_path: str, hour: int = None, minute: int = None, show_hands: bool = False, size: int = 300):
    """
    Generates a crisp, high-resolution analog clock face diagram.
    If show_hands is False, creates a blank clock dial with numbers 1 to 12, hour/minute ticks,
    and a center pivot dot, perfect for 'Draw hands to show the correct times' questions.
    If show_hands is True, draws the hour and minute hands pointing to the specified time.
    """
    import numpy as np

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(3.2, 3.2), dpi=300)
    circle = plt.Circle((0, 0), 1.0, color='#1e293b', fill=False, linewidth=2.4)
    ax.add_patch(circle)

    # Hour numbers & major ticks
    for i in range(1, 13):
        angle = np.pi / 2 - (2 * np.pi / 12) * i
        x_tick_outer = np.cos(angle)
        y_tick_outer = np.sin(angle)
        x_tick_inner = 0.90 * np.cos(angle)
        y_tick_inner = 0.90 * np.sin(angle)
        ax.plot([x_tick_inner, x_tick_outer], [y_tick_inner, y_tick_outer], color='#1e293b', linewidth=2.0)
        
        x_num = 0.76 * np.cos(angle)
        y_num = 0.76 * np.sin(angle)
        ax.text(x_num, y_num, str(i), fontsize=12, fontweight='bold', ha='center', va='center', color='#0f172a', fontname='Arial')

    # Minor minute ticks
    for i in range(60):
        if i % 5 != 0:
            angle = np.pi / 2 - (2 * np.pi / 60) * i
            ax.plot([0.95 * np.cos(angle), np.cos(angle)], [0.95 * np.sin(angle), np.sin(angle)], color='#64748b', linewidth=1.0)

    # Draw hands if requested
    if show_hands and hour is not None:
        m = minute if minute is not None else 0
        h_angle = np.pi / 2 - (2 * np.pi / 12) * ((hour % 12) + m / 60.0)
        m_angle = np.pi / 2 - (2 * np.pi / 60) * m
        # Hour hand (shorter, thicker)
        ax.plot([0, 0.50 * np.cos(h_angle)], [0, 0.50 * np.sin(h_angle)], color='#0f172a', linewidth=3.5, solid_capstyle='round', zorder=4)
        # Minute hand (longer, medium)
        ax.plot([0, 0.75 * np.cos(m_angle)], [0, 0.75 * np.sin(m_angle)], color='#0f172a', linewidth=2.2, solid_capstyle='round', zorder=4)

    # Center pivot point
    ax.scatter(0, 0, color='#1e293b', s=35, zorder=5)

    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()
    return output_path


def generate_geometric_shape(output_path: str, shape_type: str):
    """
    Generates clean, textbook-quality 2D and 3D geometric shape diagrams
    (cylinder, pyramid, circle, sphere, cone, cube).
    """
    import numpy as np
    from matplotlib.patches import Ellipse, Circle, Arc

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    shape = shape_type.lower().replace('shape_', '').strip()

    if shape == 'cylinder':
        fig, ax = plt.subplots(figsize=(2.6, 1.6), dpi=300)
        ax.plot([0.3, 1.8], [0.8, 0.8], color='#1e293b', linewidth=2.4)
        ax.plot([0.3, 1.8], [-0.8, -0.8], color='#1e293b', linewidth=2.4)
        arc_left = Arc((0.3, 0), 0.5, 1.6, angle=0, theta1=90, theta2=270, color='#1e293b', linewidth=2.4)
        arc_left_back = Arc((0.3, 0), 0.5, 1.6, angle=0, theta1=270, theta2=90, color='#94a3b8', linewidth=1.5, linestyle='--')
        ax.add_patch(arc_left)
        ax.add_patch(arc_left_back)
        ellipse_right = Ellipse((1.8, 0), 0.5, 1.6, fill=False, color='#1e293b', linewidth=2.4)
        ax.add_patch(ellipse_right)
        ax.set_xlim(-0.1, 2.2)
        ax.set_ylim(-1.0, 1.0)

    elif shape == 'pyramid':
        fig, ax = plt.subplots(figsize=(2.2, 1.8), dpi=300)
        apex = (1.0, 1.6)
        fl, fr = (0.2, 0.2), (1.5, 0.2)
        br, bl = (1.8, 0.6), (0.5, 0.6)
        # Dashed hidden edges
        ax.plot([bl[0], br[0]], [bl[1], br[1]], color='#94a3b8', linewidth=1.5, linestyle='--')
        ax.plot([bl[0], fl[0]], [bl[1], fl[1]], color='#94a3b8', linewidth=1.5, linestyle='--')
        ax.plot([bl[0], apex[0]], [bl[1], apex[1]], color='#94a3b8', linewidth=1.5, linestyle='--')
        # Solid front edges
        ax.plot([fl[0], fr[0]], [fl[1], fr[1]], color='#1e293b', linewidth=2.4)
        ax.plot([fr[0], br[0]], [fr[1], br[1]], color='#1e293b', linewidth=2.4)
        ax.plot([fl[0], apex[0]], [fl[1], apex[1]], color='#1e293b', linewidth=2.4)
        ax.plot([fr[0], apex[0]], [fr[1], apex[1]], color='#1e293b', linewidth=2.4)
        ax.plot([br[0], apex[0]], [br[1], apex[1]], color='#1e293b', linewidth=2.4)
        ax.set_xlim(0.0, 2.0)
        ax.set_ylim(0.0, 1.8)

    elif shape == 'sphere':
        fig, ax = plt.subplots(figsize=(1.8, 1.8), dpi=300)
        circle = Circle((0, 0), 0.9, fill=False, color='#1e293b', linewidth=2.4)
        ax.add_patch(circle)
        eq_front = Arc((0, 0), 1.8, 0.5, angle=0, theta1=180, theta2=360, color='#1e293b', linewidth=1.8)
        eq_back = Arc((0, 0), 1.8, 0.5, angle=0, theta1=0, theta2=180, color='#94a3b8', linewidth=1.2, linestyle='--')
        ax.add_patch(eq_front)
        ax.add_patch(eq_back)
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)

    elif shape == 'cone':
        fig, ax = plt.subplots(figsize=(1.8, 2.0), dpi=300)
        apex_cone = (1.0, 1.8)
        ax.plot([0.2, apex_cone[0]], [0.3, apex_cone[1]], color='#1e293b', linewidth=2.4)
        ax.plot([1.8, apex_cone[0]], [0.3, apex_cone[1]], color='#1e293b', linewidth=2.4)
        cone_base_front = Arc((1.0, 0.3), 1.6, 0.5, angle=0, theta1=180, theta2=360, color='#1e293b', linewidth=2.4)
        cone_base_back = Arc((1.0, 0.3), 1.6, 0.5, angle=0, theta1=0, theta2=180, color='#94a3b8', linewidth=1.5, linestyle='--')
        ax.add_patch(cone_base_front)
        ax.add_patch(cone_base_back)
        ax.set_xlim(0.0, 2.0)
        ax.set_ylim(0.0, 2.0)

    elif shape == 'cube' or shape == 'cuboid':
        fig, ax = plt.subplots(figsize=(1.8, 1.8), dpi=300)
        ax.plot([0.2, 1.2, 1.2, 0.2, 0.2], [0.2, 0.2, 1.2, 1.2, 0.2], color='#1e293b', linewidth=2.4)
        ax.plot([0.2, 0.6], [1.2, 1.6], color='#1e293b', linewidth=2.4)
        ax.plot([1.2, 1.6], [1.2, 1.6], color='#1e293b', linewidth=2.4)
        ax.plot([1.2, 1.6], [0.2, 0.6], color='#1e293b', linewidth=2.4)
        ax.plot([0.6, 1.6], [1.6, 1.6], color='#1e293b', linewidth=2.4)
        ax.plot([1.6, 1.6], [0.6, 1.6], color='#1e293b', linewidth=2.4)
        ax.plot([0.2, 0.6], [0.2, 0.6], color='#94a3b8', linewidth=1.5, linestyle='--')
        ax.plot([0.6, 1.6], [0.6, 0.6], color='#94a3b8', linewidth=1.5, linestyle='--')
        ax.plot([0.6, 0.6], [0.6, 1.6], color='#94a3b8', linewidth=1.5, linestyle='--')
        ax.set_xlim(0.0, 1.8)
        ax.set_ylim(0.0, 1.8)

    else:  # 'circle' or default 2D circle
        fig, ax = plt.subplots(figsize=(1.8, 1.8), dpi=300)
        circle = Circle((0, 0), 0.9, fill=False, color='#1e293b', linewidth=2.4)
        ax.add_patch(circle)
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)

    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()
    return output_path


