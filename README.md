# Recipe Hub 🍳🥗
> **Course:** 203 Investigative Studio 1  
> **Assessment:** Team Prototype and Report 
> **Development Team:** Gursimran Singh (270689019)  & Parth (270487311) (50% / 50% Collaborative Contribution Split)

---

## 📌 Project Concept & Goals
**Recipe Hub** is a healthy cooking web app built to solve a simple problem: most recipe platforms focus only on food pictures and social sharing,
rather than helping people manage the ingredients they actually have in their kitchen. 

This prototype helps users manage their day-to-day cooking by tracking pantry ingredients,
instantly matching items to find the best recipes, and suggesting healthy food alternatives.

---

## 🚀 Core Platform Features
* **Pantry Ingredient Pool:** A live dashboard page where users can add and remove ingredients currently available in their kitchen.
* **Automatic Recipe Matcher:** A backend matching system that compares your kitchen ingredients with saved recipes and shows you exactly what you can cook.
* **Healthy Food Suggestions:** A page split into clear food groups (Vegetables, Proteins, Dairy & Pantry, Fruits) that shows alternative ingredients you can use.
* **Interactive Profile & Goals:** A clean user settings page where you can edit personal info, update daily meal targets, and check off dietary options like Low Sodium.
* **Contact & Support Portal:** A clean contact form page displaying local operational address and help phone numbers to handle user messages.

---

## 🛠️ Folder Layout & Architecture
* **Server Code:** Python 3.x
* **Web Framework:** Flask
* **Database Engine:** SQLite3
* **Layout Templates:** HTML5, CSS3, and Jinja2 Templates

```text
recipe_hub/
│
├── app.py                 # Main Python server code and website routes
├── recipe.db              # SQLite database file where all recipe data is saved
│
├── templates/             # HTML layout pages
│   ├── base.html          # Main website template with common header and footer sections
│   ├── home.html          # Pantry page to add and remove your current ingredients
│   ├── recipe.html        # Matching recipes page sorted by ingredients you own
│   ├── suggestions.html   # Food alternatives grid broken down by categories
│   ├── profile.html       # Profile settings page with working entry forms
│   └── contact.html       # Contact page showing support info and a message form
│
└── static/
    └── style.css          # Main styling sheet used to look clean and neat
