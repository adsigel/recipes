from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from recipe_extractor import extract_recipe_data
import json
import os
from datetime import datetime, timezone

app = Flask(__name__)
# --- Database Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
# Prevent browser caching during development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

db = SQLAlchemy(app)

# --- Recipe Database Model ---
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.String(300), nullable=True)
    # Store ingredients and steps as JSON strings in a text field
    ingredients = db.Column(db.Text, nullable=False)
    steps = db.Column(db.Text, nullable=False)
    # --- New Nutrition and Serving Fields ---
    servings = db.Column(db.String(50), nullable=True)
    calories = db.Column(db.String(50), nullable=True)
    protein = db.Column(db.String(50), nullable=True)
    fat = db.Column(db.String(50), nullable=True)
    carbs = db.Column(db.String(50), nullable=True)
    # --- Raw Extracted Text ---
    raw_text = db.Column(db.Text, nullable=True)
    # --- Recipe Usage Tracking ---
    cook_count = db.Column(db.Integer, default=0)
    last_cooked_date = db.Column(db.DateTime, nullable=True)
    # --- Timestamps ---
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Association table for the many-to-many relationship between Recipe and Tag
    recipe_tags = db.Table('recipe_tags',
        db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'), primary_key=True),
        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
    )

    tags = db.relationship('Tag', secondary=recipe_tags, lazy='subquery',
        backref=db.backref('recipes', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'image_url': self.image_url,
            'description': self.description,
            'ingredients': json.loads(self.ingredients),
            'steps': json.loads(self.steps),
            'servings': self.servings,
            'calories': self.calories,
            'protein': self.protein,
            'fat': self.fat,
            'carbs': self.carbs,
            'raw_text': self.raw_text,
            'cook_count': self.cook_count,
            'last_cooked_date': self.last_cooked_date.isoformat() if self.last_cooked_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': [tag.name for tag in self.tags]
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is missing from the request'}), 400
    
    url = data['url']
    manual_login = data.get('manual_login', False)  # Default to False
    
    try:
        # Use the factory function to get the appropriate extractor
        recipe_data = extract_recipe_data(url, manual_login=manual_login)
        return jsonify(recipe_data)
    except Exception as e:
        print(f"Error extracting recipe: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/save', methods=['POST'])
def save_recipe():
    try:
        data = request.get_json().get('recipe', {})
        
        if not all(k in data for k in ['title', 'ingredients', 'steps']):
             return jsonify({'error': 'Missing recipe data.'}), 400

        new_recipe = Recipe(
            title=data['title'],
            image_url=data.get('image_url', ''),
            description=data.get('description', ''),
            # Convert Python lists to JSON strings for storage
            ingredients=json.dumps(data['ingredients']),
            steps=json.dumps(data['steps']),
            # --- Save New Nutrition Data ---
            servings=data.get('servings'),
            calories=data.get('calories'),
            protein=data.get('protein'),
            fat=data.get('fat'),
            carbs=data.get('carbs'),
            # --- Raw Extracted Text ---
            raw_text=data.get('raw_text', '')
        )
        
        db.session.add(new_recipe)

        # Handle Tags for new recipe
        if 'tags' in data:
            for tag_name in data['tags']:
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    new_recipe.tags.append(tag)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Recipe saved successfully!', 'recipe_id': new_recipe.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/recipes')
def get_recipes():
    search_term = request.args.get('search', '')
    sort_order = request.args.get('sort', 'newest')
    tag_filter = request.args.get('tag', '')

    query = Recipe.query

    if tag_filter:
        query = query.join(Recipe.tags).filter(Tag.name == tag_filter)

    if search_term:
        query = query.filter(or_(
            Recipe.title.ilike(f'%{search_term}%'),
            Recipe.ingredients.ilike(f'%{search_term}%')
        ))

    if sort_order == 'oldest':
        query = query.order_by(Recipe.created_at.asc())
    elif sort_order == 'title_asc':
        query = query.order_by(Recipe.title.asc())
    elif sort_order == 'title_desc':
        query = query.order_by(Recipe.title.desc())
    elif sort_order == 'most_cooked':
        query = query.order_by(Recipe.cook_count.desc())
    elif sort_order == 'least_cooked':
        query = query.order_by(Recipe.cook_count.asc())
    elif sort_order == 'recently_cooked':
        query = query.order_by(Recipe.last_cooked_date.desc().nullslast())
    else: # Default to 'newest'
        query = query.order_by(Recipe.created_at.desc())
        
    recipes = query.all()
    
    recipes_data = [{
        'id': r.id,
        'title': r.title,
        'image_url': r.image_url,
        'description': r.description,
        'ingredients': json.loads(r.ingredients),
        'steps': json.loads(r.steps),
        'servings': r.servings,
        'calories': r.calories,
        'protein': r.protein,
        'fat': r.fat,
        'carbs': r.carbs,
        'raw_text': r.raw_text,
        'cook_count': r.cook_count,
        'last_cooked_date': r.last_cooked_date.strftime('%Y-%m-%d %H:%M:%S') if r.last_cooked_date else None,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': r.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'tags': [tag.name for tag in r.tags]
    } for r in recipes]
    
    return jsonify(recipes=recipes_data)

@app.route('/tags')
def get_tags():
    tags = Tag.query.all()
    return jsonify(tags=[tag.name for tag in tags])

@app.route('/recipe/<int:recipe_id>')
def get_recipe(recipe_id):
    """Display a single recipe."""
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('recipe.html', recipe=recipe.to_dict())

@app.route('/update_recipe/<int:recipe_id>', methods=['POST'])
def update_recipe(recipe_id):
    """Update an existing recipe."""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        data = request.get_json().get('recipe', {})
        
        if not all(k in data for k in ['title', 'ingredients', 'steps']):
            return jsonify({'error': 'Missing recipe data.'}), 400

        # Update basic recipe fields
        recipe.title = data['title']
        recipe.image_url = data.get('image_url', '')
        recipe.description = data.get('description', '')
        recipe.ingredients = json.dumps(data['ingredients'])
        recipe.steps = json.dumps(data['steps'])
        recipe.servings = data.get('servings')
        recipe.calories = data.get('calories')
        recipe.protein = data.get('protein')
        recipe.fat = data.get('fat')
        recipe.carbs = data.get('carbs')
        recipe.raw_text = data.get('raw_text', '')
        
        # Clear existing tags and add new ones
        recipe.tags.clear()
        if 'tags' in data:
            for tag_name in data['tags']:
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    recipe.tags.append(tag)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Recipe updated successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/mark_cooked/<int:recipe_id>', methods=['POST'])
def mark_cooked(recipe_id):
    """Mark a recipe as cooked - increment cook count and update last cooked date."""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        
        # Increment cook count
        recipe.cook_count += 1
        
        # Update last cooked date
        recipe.last_cooked_date = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Recipe marked as cooked! (Cooked {recipe.cook_count} times)',
            'cook_count': recipe.cook_count,
            'last_cooked_date': recipe.last_cooked_date.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reset_cook_count/<int:recipe_id>', methods=['POST'])
def reset_cook_count(recipe_id):
    """Reset cook count and last cooked date for a recipe."""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        
        # Reset cook count and last cooked date
        recipe.cook_count = 0
        recipe.last_cooked_date = None
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Cook count and history reset successfully!',
            'cook_count': 0,
            'last_cooked_date': None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# --- Tag Database Model ---
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 