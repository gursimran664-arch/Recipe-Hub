from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'recipe_hub_secret_key_for_flash_messages'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'recipe.db')

USER_PROFILE_DATA = {
    'name': 'Sarah',
    'rank': 'level 3 planner',
    'planned': 14,
    'new': 7,
    'email_status': 'Enabled',
    'prep_style': 'Under 30 Minutes, Whole-food Focused',
    'servings': '2 Portions',
    'primary_goal': 'Dynamic Recipe Variation',
    'tracked_goals': 'Low Sodium, Unprocessed Balanced Whole Foods',
    'excluded_ingredients': 'None Configured'
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Drop existing tables to establish clean data rules
    cursor.execute('DROP TABLE IF EXISTS ingredients')
    cursor.execute('DROP TABLE IF EXISTS recipes')
    cursor.execute('DROP TABLE IF EXISTS ingredient_pool')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            instructions TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient_name TEXT,
            importance TEXT, 
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredient_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')

    recipes_data = [
        {
            "name": "Lemon Herb Chicken",
            "main_ingredients": ["chicken breast"],
            "optional_ingredients": ["tomatoes", "lemon", "spinach", "garlic", "onion"],
            "steps": "Clean and dice the chicken breast into bite-sized pieces.|Mix minced garlic, chopped onion, fresh squeezed lemon juice, and green herbs in a bowl to create a marinade.|Toss the chicken in the marinade and let it sit for 15 minutes.|Heat a light splash of olive oil in a pan over medium heat.|Add the chicken pieces and cook until golden brown and cooked through (about 8-10 minutes).|Throw in fresh chopped tomatoes and spinach leaves during the last 2 minutes until everything cooks down cleanly.|Serve warm on a plate."
        },
        {
            "name": "Garlic Tomato Pasta",
            "main_ingredients": ["pasta"],
            "optional_ingredients": ["tomatoes", "garlic", "spinach"],
            "steps": "Fill a large pot with water, add a generous pinch of salt, and bring to a rolling boil.|Drop the healthy whole-grain pasta into the boiling water and cook for 8-10 minutes until al dente.|While pasta boils, finely mince your garlic cloves and dice the fresh tomatoes.|Heat a skillet with olive oil and sauté the minced garlic until fragrant and lightly golden.|Add the diced tomatoes to the skillet, cooking down until they form a light, textured sauce.|Drain your cooked pasta completely and toss it directly into the skillet with the sauce.|Add fresh spinach leaves, tossing everything together for 1 minute until wilted and warm."
        },
        {
            "name": "Spinach Tomato Omelette",
            "main_ingredients": ["eggs"],
            "optional_ingredients": ["spinach", "tomatoes", "garlic"],
            "steps": "Crack fresh eggs into a bowl, season with a pinch of salt and pepper, and whisk vigorously with a fork.|Finely chop garlic, tomatoes, and clean spinach leaves.|Heat a non-stick frying pan over medium heat and lightly sauté the garlic and chopped tomatoes.|Add the spinach leaves to the pan and cook for 1 minute until they soften and shrink.|Pour the whisked eggs evenly over the cooked vegetable base in the pan.|Let the eggs set on the bottom for 2 minutes, then gently fold the omelette in half using a spatula.|Cook for an additional minute until the inside is firm and fully set, then slide onto a plate."
        },
        {
            "name": "Garlic Lemon Salmon",
            "main_ingredients": ["salmon"],
            "optional_ingredients": ["lemon", "garlic"],
            "steps": "Pat salmon fillets dry with a paper towel.|Season both sides of the salmon evenly with salt, cracked black pepper, and a generous layer of minced garlic.|Heat a frying pan over medium-high heat with a touch of healthy cooking oil.|Place the salmon fillets skin-side down first into the hot pan and sear for 4-5 minutes.|Carefully flip the salmon over to cook the top side for another 3-4 minutes until flaky.|Squeeze the juice of a fresh lemon directly over the salmon while it is still sizzling in the pan.|Remove from heat and serve immediately."
        },
        {
            "name": "Mediterranean Chickpea Salad",
            "main_ingredients": ["chickpeas"],
            "optional_ingredients": ["tomatoes", "cucumber", "onion", "lemon"],
            "steps": "Open your can of chickpeas, pour them into a colander, and rinse thoroughly under cold water.|Chop tomatoes, crisp cucumber, and onion into uniform, bite-sized cubes.|Combine the rinsed chickpeas and all the chopped fresh vegetables into a large salad bowl.|Cut a lemon in half and squeeze its fresh juice entirely over the salad mix.|Drizzle with a light touch of olive oil, salt, and pepper.|Use large spoons to toss the ingredients completely until evenly dressed.|Let sit for 5 minutes before serving to allow the whole-food flavors to fully blend."
        },
        {
            "name": "Avocado Egg Toast",
            "main_ingredients": ["bread", "avocado"],
            "optional_ingredients": ["eggs"],
            "steps": "Place your slice of high-fiber, whole-grain bread into the toaster until golden and crunchy.|Slice open a fresh avocado, remove the pit, and scoop the green flesh out into a small bowl.|Use a fork to thoroughly mash the avocado with a small pinch of salt and pepper.|Spread the mashed avocado paste thickly and evenly across the warm, toasted bread surface.|Top with an egg cooked to your preference (poached or fried) if available.|Garnish with an extra crack of pepper and enjoy immediately."
        },
        {
            "name": "Apple Cinnamon Oatmeal",
            "main_ingredients": ["oats"],
            "optional_ingredients": ["apples", "milk", "honey"],
            "steps": "Pour milk or water into a clean saucepan and place it over medium heat until it reaches a gentle simmer.|Stir rolled oats into the warming liquid completely.|Wash and finely dice your fresh apples into small squares if using.|Add diced apples and a dash of ground cinnamon straight into the oatmeal pot.|Turn heat down to low and let it cook for 5-6 minutes, stirring continuously so it stays smooth.|Once oats are thick and creamy, pour them into a breakfast bowl.|Drizzle a spoonful of sweet honey across the top surface before eating."
        },
        {
            "name": "Banana Almond Protein Shake",
            "main_ingredients": ["milk", "banana"],
            "optional_ingredients": ["almonds", "honey"],
            "steps": "Peel a ripe banana and break it into 3 or 4 smaller chunks.|Place banana pieces directly into the base of a high-speed blender.|Measure out your fresh almonds and toss them into the blender jar if available.|Pour cold milk over the ingredients.|Add a delicate drizzle of natural honey to balance out the wholesome flavors.|Secure blender lid tightly and blend on high speed for approximately 45-60 seconds.|Pour into a tall glass and enjoy cold."
        },
        {
            "name": "Greek Yogurt Berry Bowl",
            "main_ingredients": ["yogurt"],
            "optional_ingredients": ["blueberries", "honey", "almonds"],
            "steps": "Spoon a generous portion of thick, unsweetened Greek yogurt into a clean breakfast bowl.|Smooth out the surface layer with the back of your spoon.|Rinse your fresh blueberries under cold water and scatter them across the top of the yogurt.|Take your almonds, crush them into small pieces on a cutting board, and sprinkle them around the bowl if using.|Finish the dish by adding a golden drizzle of sweet honey right across the top surface."
        }
    ]

    for r in recipes_data:
        try:
            cursor.execute("INSERT INTO recipes (name, instructions) VALUES (?, ?)", (r["name"], r["steps"]))
            recipe_id = cursor.lastrowid
            
            for ing in r["main_ingredients"]:
                cursor.execute("INSERT INTO ingredients (recipe_id, ingredient_name, importance) VALUES (?, ?, 'main')", (recipe_id, ing.lower()))
                
            for ing in r["optional_ingredients"]:
                cursor.execute("INSERT INTO ingredients (recipe_id, ingredient_name, importance) VALUES (?, ?, 'optional')", (recipe_id, ing.lower()))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    conn = get_db_connection()
    pool_rows = conn.execute('SELECT name FROM ingredient_pool').fetchall()
    conn.close()
    ingredients = [row['name'] for row in pool_rows]
    return render_template('home.html', ingredients=ingredients)

@app.route('/add_ingredient', methods=['POST'])
def add_ingredient():
    new_item = request.form.get('ingredient', '').strip().lower()
    if new_item:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO ingredient_pool (name) VALUES (?)', (new_item,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
    return redirect(url_for('home'))

@app.route('/remove_ingredient/<item>')
def remove_ingredient(item):
    conn = get_db_connection()
    conn.execute('DELETE FROM ingredient_pool WHERE name = ?', (item.lower(),))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/recipe')
def recipe():
    conn = get_db_connection()
    pool_rows = conn.execute('SELECT name FROM ingredient_pool').fetchall()
    user_ingredients = set(row['name'].lower() for row in pool_rows)
    
    all_recipes = conn.execute('SELECT id, name, instructions FROM recipes').fetchall()
    matched_recipes = []
    
    for r in all_recipes:
        ing_rows = conn.execute('SELECT ingredient_name, importance FROM ingredients WHERE recipe_id = ?', (r['id'],)).fetchall()
        
        main_ingredients = [row['ingredient_name'].lower() for row in ing_rows if row['importance'] == 'main']
        optional_ingredients = [row['ingredient_name'].lower() for row in ing_rows if row['importance'] == 'optional']
        
        # 1. Verify user has ALL main baseline ingredients
        has_all_mains = all(main_ing in user_ingredients for main_ing in main_ingredients)
        
        # 2. Count total matches (main + optional items)
        total_matches = sum(1 for ing in (main_ingredients + optional_ingredients) if ing in user_ingredients)
        
        # Smart Check: Must have all main items AND at least 2 total selected items
        if has_all_mains and total_matches >= 2:
            matched_recipes.append({
                'name': r['name'],
                'main_ingredients': main_ingredients,
                'optional_ingredients': optional_ingredients,
                'steps': r['instructions'].split('|')
            })
            
    conn.close()
    return render_template('recipe.html', recipes=matched_recipes, pool_empty=(len(user_ingredients) == 0), user_ingredients=user_ingredients)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    active_tab = request.args.get('tab', 'personal')
    if request.method == 'POST':
        if active_tab == 'personal':
            USER_PROFILE_DATA['name'] = request.form.get('name', USER_PROFILE_DATA['name'])
            USER_PROFILE_DATA['email_status'] = request.form.get('email_status', USER_PROFILE_DATA['email_status'])
        elif active_tab == 'preferences':
            USER_PROFILE_DATA['prep_style'] = request.form.get('prep_style', USER_PROFILE_DATA['prep_style'])
            USER_PROFILE_DATA['servings'] = request.form.get('servings', USER_PROFILE_DATA['servings'])
            USER_PROFILE_DATA['primary_goal'] = request.form.get('primary_goal', USER_PROFILE_DATA['primary_goal'])
        elif active_tab == 'dietary':
            USER_PROFILE_DATA['tracked_goals'] = request.form.get('tracked_goals', USER_PROFILE_DATA['tracked_goals'])
            USER_PROFILE_DATA['excluded_ingredients'] = request.form.get('excluded_ingredients', USER_PROFILE_DATA['excluded_ingredients'])
            
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile', tab=active_tab))
    return render_template('profile.html', user=USER_PROFILE_DATA, active_tab=active_tab)

@app.route('/suggestions')
def suggestions():
    categorized_alternatives = {
        'Vegetables': [{'name': 'Tomatoes'}, {'name': 'Spinach'}, {'name': 'Cucumber'}, {'name': 'Onion'}, {'name': 'Garlic'}, {'name': 'Avocado'}],
        'Proteins': [{'name': 'Chicken Breast'}, {'name': 'Salmon'}, {'name': 'Eggs'}, {'name': 'Chickpeas'}],
        'Dairy & Pantry': [{'name': 'Pasta'}, {'name': 'Yogurt'}, {'name': 'Oats'}, {'name': 'Milk'}, {'name': 'Honey'}, {'name': 'Almonds'}, {'name': 'Bread'}],
        'Fruits': [{'name': 'Lemon'}, {'name': 'Apples'}, {'name': 'Banana'}, {'name': 'Blueberries'}]
    }
    active_category = request.args.get('category', 'All')
    return render_template('suggestions.html', categories=categorized_alternatives, active_category=active_category)

@app.route('/use_alternative/<name>')
def use_alternative(name):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO ingredient_pool (name) VALUES (?)', (name.lower(),))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()
    return redirect(url_for('home'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    info = {'address': '2 Bunny Street, Wellington, New Zealand', 'phone': '+64 220 603202'}
    if request.method == 'POST':
        name = request.form.get('name')
        flash(f"Thank you, {name}! Your message has been sent successfully.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html', info=info)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)