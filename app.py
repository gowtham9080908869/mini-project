from flask import Flask, render_template, request, jsonify, session, send_from_directory
import pandas as pd
import numpy as np
import joblib
import random
import string
import os
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from gtts import gTTS

# ============================================================================
# COMPOSITE CAPTCHA CLASS (Merged from composite_captcha.py)
# ============================================================================

class CompositeCaptcha:
    def __init__(self, static_folder='static'):
        self.static_folder = static_folder
        self.assets_dir = os.path.join(static_folder, 'assets')
        self.bg_dir = os.path.join(self.assets_dir, 'backgrounds')
        self.obj_dir = os.path.join(self.assets_dir, 'objects')
        
        # Ensure directories exist
        os.makedirs(self.bg_dir, exist_ok=True)
        os.makedirs(self.obj_dir, exist_ok=True)
        
        self.backgrounds = [f for f in os.listdir(self.bg_dir) if f.endswith('.png')]
        self.objects = {
            'cars': 'car.png',
            'traffic_lights': 'traffic_light.png',
            'crosswalks': 'crosswalk.png'
        }
        # Dimensions for standardizing
        self.size = (300, 300)

    def glom_path(self, *args):
        return os.path.join(*args)

    def create_composite_image(self, target_category, is_target_present=True, num_distractors=2):
        """
        Creates a composite image.
        Returns:
            filename: str,
            target_box: tuple (x1, y1, x2, y2) or None if not present/applicable
        """
        # Reload backgrounds in case they were just generated
        self.backgrounds = [f for f in os.listdir(self.bg_dir) if f.endswith('.png')]
        
        # 1. Select Background
        if not self.backgrounds:
            # Fallback if no backgrounds
            bg = Image.new('RGBA', self.size, (200, 200, 200))
        else:
            bg_name = random.choice(self.backgrounds)
            bg_path = self.glom_path(self.bg_dir, bg_name)
            try:
                bg = Image.open(bg_path).convert('RGBA')
            except:
                bg = Image.new('RGBA', self.size, (200, 200, 200))
            
        bg = bg.resize(self.size)

        target_box = None
        
        # 2. Place Target (if valid)
        if is_target_present and target_category in self.objects:
            obj_name = self.objects[target_category]
            obj_path = self.glom_path(self.obj_dir, obj_name)
            
            try:
                obj = Image.open(obj_path).convert('RGBA')
                # Resize object to reasonable size (e.g., 20-30% of bg)
                obj_w, obj_h = obj.size
                scale = random.uniform(0.3, 0.5)
                new_size = (int(obj_w * scale), int(obj_h * scale))
                obj = obj.resize(new_size)
                
                # Random position
                max_x = self.size[0] - new_size[0]
                max_y = self.size[1] - new_size[1]
                x = random.randint(0, max(0, max_x))
                y = random.randint(0, max(0, max_y))
                
                # Paste
                bg.paste(obj, (x, y), obj)
                target_box = (x, y, x + new_size[0], y + new_size[1])
                
            except Exception as e:
                print(f"Error placing target: {e}")

        # 3. Place Distractors (optional, other categories)
        distractor_cats = [c for c in self.objects.keys() if c != target_category]
        if distractor_cats:
            for _ in range(num_distractors):
                d_cat = random.choice(distractor_cats)
                d_name = self.objects[d_cat]
                try:
                    d_obj = Image.open(self.glom_path(self.obj_dir, d_name)).convert('RGBA')
                    # Resize
                    d_w, d_h = d_obj.size
                    scale = random.uniform(0.2, 0.4)
                    new_size = (int(d_w * scale), int(d_h * scale))
                    d_obj = d_obj.resize(new_size)
                    
                    x = random.randint(0, self.size[0] - new_size[0])
                    y = random.randint(0, self.size[1] - new_size[1])
                    
                    # Simple paste (no overlap check for speed, can be improved)
                    bg.paste(d_obj, (x, y), d_obj)
                except:
                    pass

        # 4. Save
        output_dir = self.glom_path(self.static_folder, 'generated_captchas')
        os.makedirs(output_dir, exist_ok=True)
        filename = f"comp_{int(time.time()*1000)}_{random.randint(0,1000)}.png"
        bg.save(os.path.join(output_dir, filename))
        
        return f"generated_captchas/{filename}", target_box

# ============================================================================
# ASSET GENERATION (Merged from create_placeholders.py)
# ============================================================================

def create_street_bg():
    img = Image.new('RGB', (800, 600), (100, 100, 100)) # Gray road
    draw = ImageDraw.Draw(img)
    # Sky
    draw.rectangle([0, 0, 800, 200], fill=(135, 206, 235))
    # Road lines
    draw.line([0, 400, 800, 400], fill=(255, 255, 255), width=5)
    draw.line([0, 500, 800, 500], fill=(255, 255, 255), width=5)
    img.save('static/assets/backgrounds/street.png')

def create_nature_bg():
    img = Image.new('RGB', (800, 600), (34, 139, 34)) # Forest Green
    draw = ImageDraw.Draw(img)
    # Sky
    draw.rectangle([0, 0, 800, 200], fill=(135, 206, 235))
    # Sun
    draw.ellipse([700, 50, 780, 130], fill=(255, 255, 0))
    img.save('static/assets/backgrounds/nature.png')

def create_car():
    img = Image.new('RGBA', (200, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Car body
    draw.rectangle([20, 40, 180, 90], fill=(255, 0, 0))
    # Car top
    draw.polygon([(40, 40), (60, 10), (140, 10), (160, 40)], fill=(200, 0, 0))
    # Wheels
    draw.ellipse([30, 70, 70, 110], fill=(0, 0, 0))
    draw.ellipse([130, 70, 170, 110], fill=(0, 0, 0))
    img.save('static/assets/objects/car.png')

def create_traffic_light():
    img = Image.new('RGBA', (60, 150), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Housing
    draw.rectangle([10, 10, 50, 140], fill=(50, 50, 50))
    # Lights
    draw.ellipse([20, 20, 40, 40], fill=(255, 0, 0))
    draw.ellipse([20, 60, 40, 80], fill=(255, 165, 0))
    draw.ellipse([20, 100, 40, 120], fill=(0, 255, 0))
    img.save('static/assets/objects/traffic_light.png')

def create_crosswalk():
    img = Image.new('RGBA', (300, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Stripes
    for i in range(0, 300, 40):
        draw.rectangle([i, 10, i+20, 90], fill=(255, 255, 255))
    img.save('static/assets/objects/crosswalk.png')

def check_and_create_assets():
    """Ensure all required assets exist"""
    # Create directories
    os.makedirs('static/assets/backgrounds', exist_ok=True)
    os.makedirs('static/assets/objects', exist_ok=True)
    
    # Create assets if they don't exist
    if not os.path.exists('static/assets/backgrounds/street.png'): create_street_bg()
    if not os.path.exists('static/assets/backgrounds/nature.png'): create_nature_bg()
    if not os.path.exists('static/assets/objects/car.png'): create_car()
    if not os.path.exists('static/assets/objects/traffic_light.png'): create_traffic_light()
    if not os.path.exists('static/assets/objects/crosswalk.png'): create_crosswalk()

# ============================================================================
# MAIN APPLICATION
# ============================================================================

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production-2026'  # Change this in production!

# Load your trained AI brain (if available)
try:
    model = joblib.load('captcha_guard.pkl')
except:
    model = None # Handle missing model gracefully

# Initialize Composite Captcha Generator
composite_gen = CompositeCaptcha()

# Ensure static directories exist
os.makedirs('static/audio', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/challenge_images', exist_ok=True)
os.makedirs('static/generated_captchas', exist_ok=True)

# Generate assets on startup
check_and_create_assets()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_random_text(length=6):
    """Generate random alphanumeric text for CAPTCHA"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_captcha_image(text):
    """Create a distorted image with the given text"""
    width, height = 300, 100
    bg_color = (5, 5, 5)
    text_color = (0, 242, 255)
    
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    # Draw text
    text_width = draw.textlength(text, font=font) if hasattr(draw, 'textlength') else len(text) * 30
    position = ((width - text_width) / 2, 20)
    draw.text(position, text, fill=text_color, font=font)
    
    # Add noise lines
    for _ in range(5):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([start, end], fill=(0, 242, 255, 100), width=2)
    
    # Add noise dots
    for _ in range(100):
        xy = (random.randint(0, width), random.randint(0, height))
        draw.point(xy, fill=(0, 200, 255))
    
    image = image.filter(ImageFilter.GaussianBlur(radius=1))
    
    filename = f'captcha_{int(time.time()*1000)}.png'
    filepath = os.path.join('static/images', filename)
    image.save(filepath)
    
    return filename

def create_voice_captcha(text):
    """Create audio file with spoken text"""
    spoken_text = ' '.join(list(text))
    filename = f'voice_{int(time.time()*1000)}.mp3'
    filepath = os.path.join('static/audio', filename)
    
    tts = gTTS(text=spoken_text, lang='en', slow=True)
    tts.save(filepath)
    
    return filename

def generate_challenge_images():
    """Generate 9 images for image CAPTCHA using CompositeCaptcha"""
    # 1. Select a target category
    target_category = random.choice(['cars', 'traffic_lights', 'crosswalks'])
    
    images = []
    correct_indices = []
    
    # 2. Generate 9 images
    for i in range(9):
        # Determine if this image should contain the target
        is_target = False
        if len(correct_indices) < 3:
             is_target = True
        elif len(correct_indices) < 5 and random.random() > 0.5:
             is_target = True
        
        # Balance
        if i >= 6 and len(correct_indices) < 3:
            is_target = True
            
        # Max limit
        if len(correct_indices) >= 5:
            is_target = False

        if is_target:
            correct_indices.append(i)
            img_path, _ = composite_gen.create_composite_image(target_category, is_target_present=True)
        else:
            # Distractor
            distractors = [c for c in ['cars', 'traffic_lights', 'crosswalks'] if c != target_category]
            dist_cat = random.choice(distractors)
            img_path, _ = composite_gen.create_composite_image(dist_cat, is_target_present=True)
            
        images.append(f'/static/{img_path}')
        
    return images, correct_indices, target_category

def generate_part_selection_challenge():
    """Generate a single image with a specific target for Part Selection"""
    target_category = random.choice(['cars', 'traffic_lights', 'crosswalks'])
    
    # Generate single image with target
    img_path, target_box = composite_gen.create_composite_image(target_category, is_target_present=True, num_distractors=4)
    
    return f'/static/{img_path}', target_box, target_category

def cleanup_old_files(directory, max_age_hours=1):
    """Remove files older than specified hours"""
    now = datetime.now()
    if not os.path.exists(directory):
        return
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if now - file_time > timedelta(hours=max_age_hours):
                try:
                    os.remove(filepath)
                except:
                    pass

def init_session():
    """Initialize or reset verification session"""
    session['stage'] = 'text'
    session['text_attempts'] = 2
    session['image_attempts'] = 2
    session['part_attempts'] = 2
    session['voice_attempts'] = 2
    session['captcha_time'] = time.time()

def progress_to_next_stage():
    """Move to the next verification stage"""
    current = session.get('stage', 'text')
    
    if current == 'text':
        session['stage'] = 'image'
    elif current == 'image':
        session['stage'] = 'part'
    elif current == 'part':
        session['stage'] = 'voice'
    elif current == 'voice':
        session['stage'] = 'denied'
    
    return session['stage']

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    if 'stage' not in session:
        init_session()
    return render_template('index.html')

@app.route('/start_verification', methods=['GET'])
def start_verification():
    init_session()
    return jsonify({
        'success': True,
        'stage': session['stage'],
        'text_attempts': session['text_attempts'],
        'image_attempts': session['image_attempts'],
        'part_attempts': session['part_attempts'],
        'voice_attempts': session['voice_attempts']
    })

@app.route('/get_current_challenge', methods=['GET'])
def get_current_challenge():
    stage = session.get('stage', 'text')
    
    if stage == 'denied':
        return jsonify({'stage': 'denied', 'message': '🚫 ACCESS DENIED'})
    
    cleanup_old_files('static/images')
    cleanup_old_files('static/audio')
    cleanup_old_files('static/generated_captchas')
    
    if stage == 'text':
        text = generate_random_text(6)
        image_file = create_captcha_image(text)
        session['captcha_text'] = text
        session['captcha_time'] = time.time()
        
        return jsonify({
            'stage': 'text',
            'stage_number': 1,
            'attempts_left': session['text_attempts'],
            'image': f'/static/images/{image_file}'
        })
    
    elif stage == 'image':
        images, correct_indices, category = generate_challenge_images()
        session['image_correct'] = correct_indices
        session['captcha_time'] = time.time()
        
        return jsonify({
            'stage': 'image',
            'stage_number': 2,
            'attempts_left': session['image_attempts'],
            'images': images,
            'challenge': category.replace('_', ' ').title()
        })

    elif stage == 'part':
        image_url, target_box, category = generate_part_selection_challenge()
        session['part_target_box'] = target_box
        session['part_category'] = category
        session['captcha_time'] = time.time()
        
        return jsonify({
            'stage': 'part',
            'stage_number': 3,
            'attempts_left': session.get('part_attempts', 2),
            'image': image_url,
            'challenge': category.replace('_', ' ').title(),
            'instruction': f'Click on the {category.replace("_", " ")} in the image'
        })
    
    elif stage == 'voice':
        text = generate_random_text(6)
        audio_file = create_voice_captcha(text)
        session['captcha_voice'] = text
        session['captcha_time'] = time.time()
        
        return jsonify({
            'stage': 'voice',
            'stage_number': 4,
            'attempts_left': session['voice_attempts'],
            'audio': f'/static/audio/{audio_file}'
        })

@app.route('/verify_captcha', methods=['POST'])
def verify_captcha():
    stage = session.get('stage', 'text')
    
    if stage == 'denied':
        return jsonify({'success': False, 'stage': 'denied', 'message': '🚫 ACCESS DENIED - All attempts exhausted'})
    
    # Check expiration
    if 'captcha_time' in session:
        if time.time() - session['captcha_time'] > 300:
            return jsonify({'success': False, 'message': '⏱️ CAPTCHA EXPIRED - Generating new challenge', 'expired': True})
    
    is_correct = False
    
    if stage == 'text':
        user_answer = request.json.get('answer', '').upper().strip()
        correct_answer = session.get('captcha_text', '')
        is_correct = (user_answer == correct_answer)
        attempts_key = 'text_attempts'
        
    elif stage == 'image':
        user_selected = request.json.get('selected', [])
        correct_indices = session.get('image_correct', [])
        is_correct = set(user_selected) == set(correct_indices)
        attempts_key = 'image_attempts'

    elif stage == 'part':
        click_x = request.json.get('x', -1)
        click_y = request.json.get('y', -1)
        target_box = session.get('part_target_box', None)
        
        if target_box:
            x1, y1, x2, y2 = target_box
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                is_correct = True
            else:
                is_correct = False
        else:
            is_correct = True
        attempts_key = 'part_attempts'
        
    elif stage == 'voice':
        user_answer = request.json.get('answer', '').upper().strip()
        correct_answer = session.get('captcha_voice', '')
        is_correct = (user_answer == correct_answer)
        attempts_key = 'voice_attempts'
    
    if is_correct:
        session.clear()
        return jsonify({'success': True, 'message': '✅ VERIFICATION SUCCESSFUL - Access Granted', 'access_granted': True})
    else:
        session[attempts_key] -= 1
        attempts_left = session[attempts_key]
        
        if attempts_left > 0:
            return jsonify({
                'success': False,
                'message': f'❌ INCORRECT - {attempts_left} attempt{"s" if attempts_left > 1 else ""} remaining',
                'attempts_left': attempts_left,
                'stage': stage,
                'reload_challenge': True
            })
        else:
            next_stage = progress_to_next_stage()
            if next_stage == 'denied':
                return jsonify({'success': False, 'message': '🚫 ACCESS DENIED - All verification attempts exhausted', 'stage': 'denied', 'access_denied': True})
            else:
                stage_names = {'image': 'Image Selection', 'part': 'Part Selection', 'voice': 'Audio Verification'}
                return jsonify({
                    'success': False,
                    'message': f'⚠️ Moving to next stage: {stage_names.get(next_stage, next_stage)}',
                    'stage': next_stage,
                    'progress_stage': True
                })

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)