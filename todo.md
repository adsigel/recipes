# Recipe App Future Enhancements

This file tracks the to-do list for turning the recipe extractor proof of concept into a full-featured application.

## Core Features
- [X] **Database Integration:** Replace `saved_recipes.json` with a robust database (e.g., PostgreSQL, SQLite) for storing recipes.
- [X] **Manual Recipe Entry:** Add a dedicated form to allow users to add new recipes manually, including uploading a photo.
- [ ] **Photo Capture & Upload:** Add camera support for mobile devices to capture recipe photos directly, with options to take a new photo or upload from gallery. Include image compression and resizing for optimal storage.
- [X] **Recipe Search & Filtering:** Implement a search bar to filter recipes by keywords in the title, ingredients, or instructions.
- [X] **Tagging System:** Add the ability to create custom tags for recipes (e.g., "quick-eats", "dinner-party", "baking") and filter by them.

## Nutrition & Data Model
- [X] **Update Recipe Data Model:** Extend the recipe data model to store nutrition information (calories, protein, fat, carbs) and serving count.
- [ ] **Nutrition-Based Filtering:** Allow users to filter or sort recipes based on nutrition information (e.g., "high-protein", "low-carb").
- [ ] **Automatic Nutrition Calculation:** Add a manual "Calculate Nutrition" button that estimates calories and macros from ingredient list using nutrition databases (USDA, etc.). This should be triggered manually rather than automatically to avoid errors.

## Recipe Tracking & Usage
- [X] **Cook Count Tracking:** Add fields to track how many times each recipe has been made, including a counter and the date it was last cooked.
- [X] **"Mark as Cooked" Button:** Add a simple button on recipe detail pages to increment the cook count and update the last cooked date.
- [ ] **Recipe History:** Display a list of when each recipe was last made, sorted by most recent or most frequently cooked.
- [ ] **Cooking Statistics:** Show cooking statistics like "Most Cooked Recipes", "Recently Made", and "Never Made" categories.

## Serving Size Calculator
- [ ] **Dynamic Recipe Scaling:** Add the ability to scale recipe ingredients based on desired serving size (e.g., double, halve, or custom multiplier).
- [ ] **Smart Ingredient Parsing:** Parse ingredient quantities and units to enable accurate scaling (e.g., "2 cups flour" → "4 cups flour" when doubling).
- [ ] **Unit Conversion:** Handle common unit conversions when scaling (e.g., "1/2 cup" → "1/4 cup" when halving, "1 tbsp" → "2 tbsp" when doubling).
- [ ] **Serving Size Input:** Add a simple input field or dropdown to select scaling factor (0.5x, 1x, 1.5x, 2x, 3x, custom).
- [ ] **Real-time Updates:** Update ingredient quantities in real-time as the user adjusts the serving size.
- [ ] **Preserve Original Recipe:** Always show the original recipe alongside the scaled version, or provide a toggle to switch between views.
- [ ] **Fraction Handling:** Properly handle fractions and mixed numbers (e.g., "1 1/2 cups" → "3 cups" when doubling).
- [ ] **Non-scalable Ingredients:** Allow marking certain ingredients as non-scalable (e.g., salt, pepper, cooking spray) that don't need to be adjusted.

## User Experience (UX)
- [X] **UI Reorganization:** Prioritize browsing saved recipes on the main page, moving the "Add Recipe" functionality to a secondary, dedicated section.
- [X] **Submenu for Adding Recipes:** Create a clear submenu or choice for adding recipes, either manually or via Instagram extraction.
- [X] **"Cooking Mode" Display:** Create a special view for recipes that uses a large, easy-to-read font, keeps the device's screen awake, and displays ingredients and instructions clearly for use while cooking.

## Extensibility
- [ ] **Expanded Importer:** Add the ability to import recipes from other sources besides Instagram, such as popular cooking blogs or other recipe websites.

## Data & Machine Learning
- [X] **Store Raw Extracted Text:** Save the original, raw text from the Instagram extractor in the database alongside the cleaned, user-edited version. This will create a dataset for future ML model training to improve automated parsing.

## Meal Planning
- [ ] **Select multiple meals:** User can select as many recipes as they want via checkbox. Keep a running tally of the number of meals selected and the average nutritional info for each meal.
- [ ] **Scheduling:** Assign recipes to different meals and days of the week. Maybe the app can suggest schedule optimizations based on grocery freshness. Figure out a way to account for leftovers--maybe based on editable serving count for the meal plan.
- [ ] **Grocery prep:** Once a meal plan is confirmed, assemble a full shopping list based on all the selected meals. Allow the user to indicate what they already have in the house versus need to buy.
- [ ] **Update Reminders app:** Explore creating shopping list items on a specified list in the Reminders app.

# TODO: Transition to Cloud-Based Extraction (Fly.io)

## Goal
Move Selenium-based recipe extraction (Instagram, NYTimes) to a cloud service for mobile and remote access.

## Steps
- [ ] Dockerize the Flask app and all dependencies (Selenium, Chrome/Chromedriver, etc.)
- [ ] Test the Docker image locally to ensure extraction works with persistent Chrome profile
- [ ] Set up a Fly.io account and install the Fly CLI
- [ ] Deploy the Dockerized app to Fly.io (use persistent volumes for Chrome profile if needed)
- [ ] Configure environment variables/secrets for any credentials
- [ ] Expose the Flask API endpoint securely (consider authentication or IP allowlist)
- [ ] Test extraction from a remote/mobile device
- [ ] Update the app frontend to point to the new cloud endpoint
- [ ] Document the cloud setup and login flow for Instagram/NYTimes

## Considerations
- Chrome profile persistence for login sessions
- Fly.io free tier resource limits
- Security: restrict who can access the extractor API
- Ongoing maintenance: updating Chrome/Chromedriver versions 