import os
import sqlite3
import requests
import re
# Function to remove HTML tags from text
def strip_html(text):
 return re.sub(r'<[^>]+>', '', text or '')
from flask import Flask, render_template, request, redirect, url_for, flash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Spoonacular API key for fetching online recipes
API_KEY = os.environ.get("SPOONACULAR_API_KEY", "6eddc57bd0094927881a44dfc5d62f28")

# Function to look up recipes online using a list of ingredients
def call_api(ingredients):
    
    
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "ingredients": ingredients,
        "number": 5,
        "apiKey": API_KEY,
    }
    response = requests.get(url, params=params, timeout=10)
    return response.json()
   
# Function to get full preparation steps for a specific recipe
def get_recipe_details(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": API_KEY}
    response = requests.get(url, params=params, timeout=10)
    return response.json()

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'recipe_hub_secret_key_for_flash_messages'

# Define database file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE  = os.path.join(BASE_DIR, 'recipe.db')

# Default user profile data stored in memory
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
    'excluded_ingredients': 'None Configured',
}

# ── Database ───────────────────────────────────────────────────────────────────

# Create database tables on startup if they don't exist
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Table for ingredients available in the kitchen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredient_pool (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')

    # Table to cache recipe details from the API
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT,
            image               TEXT,
            used_ingredients    TEXT,
            missed_ingredients  TEXT,
            instructions        TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Helper function to open a database connection
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ── Routes ─────────────────────────────────────────────────────────────────────

# Home route: Displays ingredients currently in the user's pantry pool
@app.route('/')
def home():
    conn = get_db_connection()
    pool_rows   = conn.execute('SELECT name FROM ingredient_pool').fetchall()
    conn.close()
    ingredients = [row['name'] for row in pool_rows]
    return render_template('home.html', ingredients=ingredients)

# Add route: Adds a new item to the kitchen ingredient pool
@app.route('/add_ingredient', methods=['POST'])
def add_ingredient():
    new_item = request.form.get('ingredient', '').strip().lower()
    if new_item:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO ingredient_pool (name) VALUES (?)', (new_item,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Skips if item already exists
        finally:
            conn.close()
    return redirect(url_for('home'))

# Remove route: Deletes an ingredient from the kitchen pool
@app.route('/remove_ingredient/<item>')
def remove_ingredient(item):
    conn = get_db_connection()
    conn.execute('DELETE FROM ingredient_pool WHERE name = ?', (item.lower(),))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

# Recipe route: Fetches online recipes matching available ingredients and shows them
@app.route('/recipe')
def recipe():
    conn = get_db_connection()

    pool_rows        = conn.execute('SELECT name FROM ingredient_pool').fetchall()
    user_ingredients = [row['name'].lower() for row in pool_rows]

    # Stop if the user's pantry pool is empty
    if not user_ingredients:
        conn.close()
        return render_template('recipe.html', recipes=[], pool_empty=True)

    ingredients_str = ",".join(user_ingredients)

# Filtering out unwanted instruction phrases from ingredients
    bad_phrases = [
        "squeeze", "add ", "stir ", "cover ",
        "mix ", "simmer ", "heat", "water", "pepper if",
    ]

    api_recipes = call_api(ingredients_str)

    if not isinstance(api_recipes, list):
        print("API error response:", api_recipes)  
        api_recipes = []

# Clean and filter API data, fetch details, and store results into the database
    for r in api_recipes:
        used_list   = []
        missed_list = []

        for i in r['usedIngredients']:
            name = i['name'].lower()
            if not any(p in name for p in bad_phrases):
                used_list.append(i['name'])

        
        for i in r['missedIngredients']:
            name = i['name'].lower()
            if not any(p in name for p in bad_phrases):
                missed_list.append(i['name'])

        used   = ", ".join(used_list)
        missed = ", ".join(missed_list)

        details      = get_recipe_details(r['id'])
        
        
        instructions = strip_html(details.get('instructions', 'No preparation steps available.'))

        existing = conn.execute(
            "SELECT id FROM recipes WHERE name = ?", (r['title'],)
        ).fetchone()

        if not existing:
            conn.execute(
                "INSERT INTO recipes (name, image, used_ingredients, missed_ingredients, instructions)"
                " VALUES (?, ?, ?, ?, ?)",
                (r['title'], r['image'], used, missed, instructions),
            )

    conn.commit()

    # Query the local database to load and render matching recipes
    placeholders = " OR ".join(["used_ingredients LIKE ?" for _ in user_ingredients])
    params = [f"%{ing}%" for ing in user_ingredients]

    all_recipes = conn.execute(
        f"SELECT * FROM recipes WHERE {placeholders}", params
    ).fetchall()
    conn.close()

    return render_template('recipe.html', recipes=all_recipes, pool_empty=False)

# Profile route: Handles multi-tab settings form data saving
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    active_tab = request.args.get('tab', 'personal')
    if request.method == 'POST':
        if active_tab == 'personal':
            USER_PROFILE_DATA['name']         = request.form.get('name',         USER_PROFILE_DATA['name'])
            USER_PROFILE_DATA['email_status'] = request.form.get('email_status', USER_PROFILE_DATA['email_status'])
        elif active_tab == 'preferences':
            USER_PROFILE_DATA['prep_style']   = request.form.get('prep_style',   USER_PROFILE_DATA['prep_style'])
            USER_PROFILE_DATA['servings']     = request.form.get('servings',     USER_PROFILE_DATA['servings'])
            USER_PROFILE_DATA['primary_goal'] = request.form.get('primary_goal', USER_PROFILE_DATA['primary_goal'])
        elif active_tab == 'dietary':
            USER_PROFILE_DATA['tracked_goals']        = request.form.get('tracked_goals',        USER_PROFILE_DATA['tracked_goals'])
            USER_PROFILE_DATA['excluded_ingredients'] = request.form.get('excluded_ingredients', USER_PROFILE_DATA['excluded_ingredients'])

        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile', tab=active_tab))

    return render_template('profile.html', user=USER_PROFILE_DATA, active_tab=active_tab)

# Suggestions route: Shows organized healthy item substitution options
@app.route('/suggestions')
def suggestions():
    categorized_alternatives = {
        'Vegetables':   [{'name': 'Tomatoes'}, {'name': 'Spinach'}, {'name': 'Cucumber'},
                         {'name': 'Onion'}, {'name': 'Garlic'}, {'name': 'Avocado'}],
        'Proteins':     [{'name': 'Chicken Breast'}, {'name': 'Salmon'},
                         {'name': 'Eggs'}, {'name': 'Chickpeas'}],
        'Dairy & Pantry': [{'name': 'Pasta'}, {'name': 'Yogurt'}, {'name': 'Oats'},
                           {'name': 'Milk'}, {'name': 'Honey'}, {'name': 'Almonds'}, {'name': 'Bread'}],
        'Fruits':       [{'name': 'Lemon'}, {'name': 'Apples'}, {'name': 'Banana'}, {'name': 'Blueberries'}],
    }
    active_category = request.args.get('category', 'All')
    return render_template('suggestions.html', categories=categorized_alternatives, active_category=active_category)

# Shortcut route: Instantly transfers an alternative ingredient to the pantry pool
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

# Contact route: Displays contact info and forwards feedback messages via email
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    info = {'address': '2 Bunny Street, Wellington, New Zealand', 'phone': '+64 220 603202'}
    if request.method == 'POST':
        sender_name = request.form.get('name')
        sender_email = request.form.get('email')
        sender_message = request.form.get('message')
 
        MY_EMAIL = "recipehub00@gmail.com"
        MY_PASSWORD = "cmzcgzpewaalohiz"
 
        msg = MIMEMultipart()
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL  
        msg['Subject'] = f"RecipeHub: New Message from {sender_name}"
 
        email_body = f"""
        You have received a new contact form submission:
       
        --------------------------------------------------
        Name:  {sender_name}
        Email: {sender_email}
        --------------------------------------------------
       
        Message:
        {sender_message}
        """
        msg.attach(MIMEText(email_body, 'plain'))
 
        try:
            # Send message via Google SMTP mail servers
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(MY_EMAIL, MY_PASSWORD)
            server.sendmail(MY_EMAIL, MY_EMAIL, msg.as_string())
            server.quit()
           
            # This will trigger ONLY if sending succeeds
            flash(f"Thank you, {sender_name}! Your message has been sent successfully.", "success")
        except Exception as e:
            # Crucial debugging: check your terminal window to read this error if delivery still fails
            print("\n!!! MAIL DELIVERY FAILED !!!")
            print(f"SMTP Error Log: {e}\n")
           
            # This triggers if something goes wrong (bad password, network blocking port 587, etc.)
            flash("Oops! The message could not send. Check your terminal output for details.", "danger")
       # flash(f"Thank you, {sender_name}! Your message has been sent successfully.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html', info=info)

# Execution block: Launches database verification and spins up the local testing server
if __name__ == '__main__':
    init_db()
    app.run(debug=True)