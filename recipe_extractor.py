import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import json
from typing import Dict, List, Optional, Tuple
import os
import traceback
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class InstagramRecipeExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.chrome_profile_path = os.path.join(os.getcwd(), 'chrome_profile')
        self.driver = None
        
    def setup_driver(self):
        """
        Set up Chrome driver with persistent profile for Instagram extraction.
        DO NOT disable images or JavaScript here—Instagram requires them.
        """
        print("🚀 Setting up Chrome driver...")
        print(f"ℹ️  Using dedicated Chrome profile at: {self.chrome_profile_path}")
        
        chrome_options = Options()
        chrome_options.add_argument(f'--user-data-dir={self.chrome_profile_path}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # DO NOT add --disable-images or JS-blocking flags here!
        print("▶️  Initializing Chrome driver...")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Chrome driver initialized successfully.")
    
    def check_instagram_login(self):
        """Check if already logged into Instagram."""
        print("🔐 Checking Instagram login status...")
        self.driver.get("https://www.instagram.com/")
        
        # Wait longer for the page to fully load and render
        time.sleep(5)
        
        # Try multiple indicators of being logged in
        login_indicators = [
            '[data-testid="user-avatar"]',  # User avatar in header
            '[data-testid="nav-profile"]',  # Profile navigation
            'a[href*="/accounts/activity/"]',  # Activity link
            'a[href*="/accounts/edit/"]',  # Edit profile link
            '[aria-label*="Profile"]',  # Profile aria label
            'img[alt*="profile picture"]',  # Profile picture
            'a[href*="/' + self.driver.get_cookie('sessionid')['value'] + '/"]' if self.driver.get_cookie('sessionid') else None  # Session-based profile link
        ]
        
        # Remove None values
        login_indicators = [indicator for indicator in login_indicators if indicator]
        
        for indicator in login_indicators:
            try:
                # Wait a bit for each element
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                )
                print("✅ Instagram session is active.")
                return True
            except TimeoutException:
                continue
        
        # Additional check: look for login form (if we see it, we're not logged in)
        try:
            login_form_indicators = [
                'input[name="username"]',
                'input[name="password"]',
                '[data-testid="login-button"]',
                'button[type="submit"]'
            ]
            
            for indicator in login_form_indicators:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, indicator)
                    print("❌ Not logged into Instagram. Please log in manually first.")
                    return False
                except NoSuchElementException:
                    continue
        except Exception:
            pass
        
        # If we can't find login indicators but also can't find login form, 
        # let's be more lenient and assume we might be logged in
        print("⚠️  Could not definitively determine login status. Proceeding anyway...")
        return True
    
    def extract_recipe_data(self, url, manual_login=False):
        """Extract recipe data from Instagram post."""
        print(f"🌐 Navigating to recipe URL: {url}")
        self.driver.get(url)
        
        # Wait for page to load
        print("⏳ Waiting for page content to load...")
        selectors_to_try = ['article', '[role="main"]']
        content_element = None
        
        for selector in selectors_to_try:
            try:
                print(f"   Trying to find content with selector: {selector}")
                content_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found content with selector: {selector}")
                break
            except TimeoutException:
                continue
        
        if not content_element:
            raise Exception("Could not find main content area")
        
        # Wait for dynamic content
        print("⏳ Waiting for dynamic content to render...")
        time.sleep(3)
        
        print("📄 Parsing Instagram content...")
        
        # Extract image
        image_url = ""
        try:
            # Try to get image from meta tags first
            meta_image = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
            image_url = meta_image.get_attribute('content')
            print("✅ Found image via meta tag.")
        except NoSuchElementException:
            try:
                # Fallback to actual image element
                img_element = self.driver.find_element(By.CSS_SELECTOR, 'img[src*="instagram"]')
                image_url = img_element.get_attribute('src')
                print("✅ Found image via img element.")
            except NoSuchElementException:
                print("⚠️  Could not find image.")
        
        # Extract text content
        print("🔍 Analyzing page structure to find main content...")
        text_content = ""
        
        try:
            # Try to find the main caption/description
            caption_selectors = [
                'article div[data-testid="post-caption"]',
                'article span[dir="auto"]',
                'article div[dir="auto"]',
                '[role="main"] span[dir="auto"]',
                '[role="main"] div[dir="auto"]'
            ]
            
            for selector in caption_selectors:
                try:
                    caption_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in caption_elements:
                        text = element.text.strip()
                        if text and len(text) > 50:  # Look for substantial text
                            text_content += text + "\n\n"
                except:
                    continue
            
            print(f"📝 Extracted text length: {len(text_content)} characters")
            
        except Exception as e:
            print(f"⚠️  Error extracting text: {e}")
        
        if not text_content.strip():
            raise Exception("Could not extract any text content from the post")
        
        print("🍳 Parsing recipe from the extracted text...")
        
        # Parse the text to extract recipe components
        recipe_data = self.parse_recipe_text(text_content)
        recipe_data['image_url'] = image_url
        recipe_data['raw_text'] = text_content
        
        print("✅ Content parsing complete.")
        return recipe_data
    
    def parse_recipe_text(self, text):
        """Parse recipe text to extract ingredients and instructions."""
        lines = text.split('\n')
        
        # Initialize recipe data
        recipe_data = {
            'title': '',
            'description': '',
            'ingredients': [],
            'steps': []
        }
        
        # Try to find title (usually first line or after emojis)
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove common prefixes
                title = re.sub(r'^[🍳👨‍🍳👩‍🍳📝📋📖🔪🥘🍽️]+', '', line).strip()
                if title and len(title) > 3:
                    recipe_data['title'] = title
                    break
        
        # If no title found, use first substantial line
        if not recipe_data['title']:
            for line in lines:
                line = line.strip()
                if line and len(line) > 10 and not line.startswith('#'):
                    recipe_data['title'] = line
                    break
        
        # Parse ingredients and instructions
        in_ingredients = False
        in_instructions = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect ingredients section
            if any(keyword in line.lower() for keyword in ['ingredients:', 'ingredient:', 'what you need:', 'you\'ll need:']):
                in_ingredients = True
                in_instructions = False
                continue
                
            # Detect instructions section
            if any(keyword in line.lower() for keyword in ['instructions:', 'directions:', 'method:', 'steps:', 'how to:', 'preparation:']):
                in_ingredients = False
                in_instructions = True
                continue
                
            # Add to appropriate section
            if in_ingredients and line and not line.startswith('#'):
                # Clean up ingredient line
                ingredient = re.sub(r'^[-•*]\s*', '', line)
                if ingredient and len(ingredient) > 2:
                    recipe_data['ingredients'].append(ingredient)
            elif in_instructions and line and not line.startswith('#'):
                # Clean up instruction line
                instruction = re.sub(r'^\d+[\.\)]\s*', '', line)
                if instruction and len(instruction) > 5:
                    recipe_data['steps'].append(instruction)
        
        # If we didn't find structured sections, try to parse by patterns
        if not recipe_data['ingredients'] and not recipe_data['steps']:
            self.parse_unstructured_text(text, recipe_data)
        
        return recipe_data
    
    def parse_unstructured_text(self, text, recipe_data):
        """Parse unstructured text to find ingredients and instructions."""
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Look for ingredient patterns
            if any(word in line.lower() for word in ['cup', 'tbsp', 'tsp', 'oz', 'lb', 'gram', 'kg', 'ml', 'l']):
                ingredient = re.sub(r'^[-•*]\s*', '', line)
                if ingredient and len(ingredient) > 3:
                    recipe_data['ingredients'].append(ingredient)
            # Look for instruction patterns
            elif any(word in line.lower() for word in ['heat', 'preheat', 'mix', 'stir', 'add', 'cook', 'bake', 'combine', 'whisk', 'fold']):
                instruction = re.sub(r'^\d+[\.\)]\s*', '', line)
                if instruction and len(instruction) > 10:
                    recipe_data['steps'].append(instruction)

    def run(self, url, manual_login=False):
        """Main method to extract recipe from Instagram URL."""
        try:
            self.setup_driver()
            
            if manual_login:
                print("🔧 Manual Login Mode")
                print("=" * 50)
                print("Chrome will open with Instagram. Please:")
                print("1. Log in to Instagram in the opened browser")
                print("2. Navigate to the recipe post if needed")
                print("3. Press Enter in this terminal when ready to continue")
                print("=" * 50)
                
                # Navigate to Instagram
                self.driver.get("https://www.instagram.com/")
                time.sleep(2)
                
                # Wait for user to log in manually
                input("Press Enter after you've logged in to Instagram...")
                print("✅ Continuing with extraction...")
                
                # Now navigate to the specific recipe URL
                self.driver.get(url)
                time.sleep(3)
                
                recipe_data = self.extract_recipe_data(url, manual_login=manual_login)
                return recipe_data
            else:
                # Normal flow - check login status first
                if not self.check_instagram_login():
                    raise Exception("Instagram login required. Please log in manually first.")
                
                recipe_data = self.extract_recipe_data(url)
                return recipe_data
        finally:
            if self.driver:
                print("🚪 Closing browser.")
                self.driver.quit()


class NYTimesRecipeExtractor:
    def __init__(self):
        self.chrome_profile_path = os.path.join(os.getcwd(), 'chrome_profile')
        self.driver = None

    def setup_driver(self):
        """
        Set up Chrome driver with persistent profile for NYTimes extraction.
        Here, we can disable images if needed for anti-bot, but NOT in Instagram extractor.
        """
        print("🚀 Setting up Chrome driver for NYTimes...")
        print(f"ℹ️  Using dedicated Chrome profile at: {self.chrome_profile_path}")
        
        chrome_options = Options()
        chrome_options.add_argument(f'--user-data-dir={self.chrome_profile_path}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Only for NYTimes
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2
        })
        print("▶️  Initializing Chrome driver...")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        self.driver.execute_script("Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'})")
        print("✅ Chrome driver initialized successfully.")

    def check_nytimes_login(self):
        """Check if already logged into NYTimes Cooking."""
        print("🔐 Checking NYTimes Cooking login status...")
        self.driver.get("https://cooking.nytimes.com/")
        time.sleep(3)
        
        # Check for bot detection first
        try:
            bot_detection_indicators = [
                "You have been blocked",
                "suspect that you're a robot",
                "bot detection",
                "automated access",
                "blocked from The New York Times"
            ]
            
            page_text = self.driver.page_source.lower()
            for indicator in bot_detection_indicators:
                if indicator.lower() in page_text:
                    print("🚫 Bot detection triggered! NYTimes has blocked automated access.")
                    print("💡 To fix this:")
                    print("   1. Open Chrome manually")
                    print("   2. Go to https://cooking.nytimes.com/")
                    print("   3. Complete any CAPTCHA or verification")
                    print("   4. Log in to your NYTimes account")
                    print("   5. Close Chrome and try the extraction again")
                    return False
        except Exception as e:
            print(f"⚠️  Error checking for bot detection: {e}")
        
        try:
            # Look for elements that indicate we're logged in
            # NYTimes might show user avatar, account menu, or "Sign Out" link
            login_indicators = [
                '[data-testid="user-menu"]',
                '.user-menu',
                '[data-testid="account-menu"]',
                '.account-menu',
                'a[href*="logout"]',
                'a[href*="signout"]',
                '.user-avatar',
                '[data-testid="user-avatar"]'
            ]
            
            for selector in login_indicators:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, selector)
                    print("✅ NYTimes Cooking session is active.")
                    return True
                except NoSuchElementException:
                    continue
            
            # Also check if we can access a recipe without being redirected to login
            self.driver.get("https://cooking.nytimes.com/recipes/1020000-classic-chocolate-chip-cookies")
            time.sleep(3)
            
            # Look for paywall or login prompts
            paywall_indicators = [
                '[data-testid="paywall"]',
                '.paywall',
                '[data-testid="login-prompt"]',
                '.login-prompt',
                'button[data-testid="login-button"]',
                '.login-button'
            ]
            
            for selector in paywall_indicators:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, selector)
                    print("❌ NYTimes Cooking login required - paywall detected.")
                    print("💡 Please log in to your NYTimes account manually in Chrome and try again.")
                    return False
                except NoSuchElementException:
                    continue
            
            # If we can see recipe content, we're probably logged in
            try:
                self.driver.find_element(By.CSS_SELECTOR, 'h1')
                print("✅ NYTimes Cooking session appears active (can access recipe content).")
                return True
            except NoSuchElementException:
                print("❌ Not logged into NYTimes Cooking. Please log in manually first.")
                print("💡 Open Chrome, go to https://cooking.nytimes.com/, and log in to your account.")
                return False
                
        except Exception as e:
            print(f"⚠️  Error checking login status: {e}")
            return False

    def extract_recipe_data(self, url):
        """Extract recipe data from NYTimes Cooking recipe."""
        print(f"🌐 Navigating to NYTimes recipe URL: {url}")
        self.driver.get(url)
        
        # Wait for page to load
        print("⏳ Waiting for page content to load...")
        time.sleep(5)  # Give more time for dynamic content
        
        # Try multiple selectors for the main content
        selectors_to_try = [
            '[data-testid="recipe-header"]',
            '.recipe-header',
            'main',
            '[role="main"]',
            'article'
        ]
        
        content_found = False
        for selector in selectors_to_try:
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found content with selector: {selector}")
                content_found = True
                break
            except TimeoutException:
                continue
        
        if not content_found:
            print("⚠️  Could not find main content, continuing anyway...")
        
        # Wait a bit more for dynamic content to fully load
        time.sleep(3)
        
        print("📄 Parsing NYTimes Cooking content...")
        
        # Extract title - try multiple selectors
        title = ""
        title_selectors = [
            'h1[data-testid="recipe-title"]',
            'h1.recipe-title',
            'h1',
            '[data-testid="title"]',
            '.title'
        ]
        
        for selector in title_selectors:
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                title = title_element.text.strip()
                if title:
                    print(f"✅ Found title: {title}")
                    break
            except NoSuchElementException:
                continue
        
        if not title:
            print("⚠️  Could not find title")
        
        # Extract image - try multiple selectors
        image_url = ""
        image_selectors = [
            '[data-testid="recipe-image"] img',
            '.recipe-image img',
            'img[src*="nytimes"]',
            'img[alt*="recipe"]',
            'img'
        ]
        
        for selector in image_selectors:
            try:
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for img in img_elements:
                    src = img.get_attribute('src')
                    if src and ('nytimes' in src or 'recipe' in src.lower()):
                        image_url = src
                        print("✅ Found recipe image")
                        break
                if image_url:
                    break
            except NoSuchElementException:
                continue
        
        if not image_url:
            print("⚠️  Could not find image")
        
        # Extract description
        description = ""
        desc_selectors = [
            '[data-testid="recipe-description"]',
            '.recipe-description',
            '[data-testid="description"]',
            '.description',
            'p[class*="description"]'
        ]
        
        for selector in desc_selectors:
            try:
                desc_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                description = desc_element.text.strip()
                if description:
                    print("✅ Found recipe description")
                    break
            except NoSuchElementException:
                continue
        
        if not description:
            print("⚠️  Could not find description")
        
        # Extract ingredients - NYTimes specific approach
        ingredients = []
        print("🔍 Looking for Ingredients section...")
        
        # First, try to find the Ingredients section by text
        try:
            # Look for the Ingredients heading
            ingredients_heading = None
            heading_selectors = [
                'h2:contains("Ingredients")',
                'h3:contains("Ingredients")',
                'h4:contains("Ingredients")',
                '[data-testid="ingredients-heading"]',
                '.ingredients-heading'
            ]
            
            # Also try to find by text content
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Ingredients')]")
            for element in all_elements:
                if element.tag_name in ['h2', 'h3', 'h4', 'h5'] and 'ingredients' in element.text.lower():
                    ingredients_heading = element
                    print(f"✅ Found Ingredients heading: {element.text}")
                    break
            
            if ingredients_heading:
                # Find the next sibling or parent that contains list items
                try:
                    # Try to find list items after the heading
                    parent = ingredients_heading.find_element(By.XPATH, "./..")
                    ingredient_elements = parent.find_elements(By.CSS_SELECTOR, 'li')
                    
                    if not ingredient_elements:
                        # Try to find list items in the same section
                        ingredient_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), 'Ingredients')]/following-sibling::*//li")
                    
                    for element in ingredient_elements:
                        ingredient = element.text.strip()
                        if ingredient and len(ingredient) > 2:
                            ingredients.append(ingredient)
                    
                    if ingredients:
                        print(f"✅ Found {len(ingredients)} ingredients")
                except Exception as e:
                    print(f"⚠️  Error extracting ingredients from heading: {e}")
            
        except Exception as e:
            print(f"⚠️  Error finding ingredients heading: {e}")
        
        # Fallback: try direct selectors for ingredients
        if not ingredients:
            ingredients_selectors = [
                '[data-testid="recipe-ingredients"] li',
                '.recipe-ingredients li',
                '[data-testid="ingredients"] li',
                '.ingredients li',
                'ul[class*="ingredient"] li',
                'li[class*="ingredient"]'
            ]
            
            for selector in ingredients_selectors:
                try:
                    ingredient_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if ingredient_elements:
                        for element in ingredient_elements:
                            ingredient = element.text.strip()
                            if ingredient and len(ingredient) > 2:
                                ingredients.append(ingredient)
                        if ingredients:
                            print(f"✅ Found {len(ingredients)} ingredients via fallback")
                            break
                except NoSuchElementException:
                    continue
        
        if not ingredients:
            print("⚠️  Could not find ingredients section")
        
        # Extract instructions - NYTimes specific approach
        steps = []
        print("🔍 Looking for Preparation section...")
        
        # First, try to find the Preparation section by text
        try:
            # Look for the Preparation heading
            preparation_heading = None
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Preparation')]")
            for element in all_elements:
                if element.tag_name in ['h2', 'h3', 'h4', 'h5'] and 'preparation' in element.text.lower():
                    preparation_heading = element
                    print(f"✅ Found Preparation heading: {element.text}")
                    break
            
            if preparation_heading:
                # Find the next sibling or parent that contains list items
                try:
                    # Try to find list items after the heading
                    parent = preparation_heading.find_element(By.XPATH, "./..")
                    step_elements = parent.find_elements(By.CSS_SELECTOR, 'li')
                    
                    if not step_elements:
                        # Try to find list items in the same section
                        step_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), 'Preparation')]/following-sibling::*//li")
                    
                    for element in step_elements:
                        step = element.text.strip()
                        if step and len(step) > 5:
                            steps.append(step)
                    
                    if steps:
                        print(f"✅ Found {len(steps)} steps")
                except Exception as e:
                    print(f"⚠️  Error extracting steps from heading: {e}")
            
        except Exception as e:
            print(f"⚠️  Error finding preparation heading: {e}")
        
        # Fallback: try direct selectors for instructions
        if not steps:
            instructions_selectors = [
                '[data-testid="recipe-instructions"] li',
                '.recipe-instructions li',
                '[data-testid="instructions"] li',
                '.instructions li',
                'ol[class*="instruction"] li',
                'li[class*="instruction"]',
                '[data-testid="recipe-steps"] li',
                '.recipe-steps li'
            ]
            
            for selector in instructions_selectors:
                try:
                    step_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if step_elements:
                        for element in step_elements:
                            step = element.text.strip()
                            if step and len(step) > 5:
                                steps.append(step)
                        if steps:
                            print(f"✅ Found {len(steps)} steps via fallback")
                            break
                except NoSuchElementException:
                    continue
        
        if not steps:
            print("⚠️  Could not find instructions section")
        
        # Extract raw text for manual parsing if needed
        raw_text = ""
        try:
            # Try to get the main content area
            content_selectors = [
                'main',
                'article',
                '[data-testid="recipe-content"]',
                '.recipe-content',
                'body'
            ]
            
            for selector in content_selectors:
                try:
                    content_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    raw_text = content_element.text
                    if raw_text and len(raw_text) > 100:
                        break
                except NoSuchElementException:
                    continue
        except Exception as e:
            print(f"⚠️  Error extracting raw text: {e}")
            raw_text = self.driver.find_element(By.TAG_NAME, 'body').text

        # If we failed to extract ingredients or steps, print the HTML for debugging
        if not ingredients or not steps:
            try:
                print("\n========== NYT MAIN HTML DEBUG ==========")
                main_html = ""
                try:
                    main_elem = self.driver.find_element(By.TAG_NAME, 'main')
                    main_html = main_elem.get_attribute('outerHTML')
                except Exception:
                    main_html = self.driver.find_element(By.TAG_NAME, 'body').get_attribute('outerHTML')
                print(main_html[:5000])  # Print first 5000 chars for brevity
                print("========== END NYT MAIN HTML DEBUG ==========")
            except Exception as e:
                print(f"⚠️  Could not print main HTML for debug: {e}")

        print("✅ NYTimes content parsing complete.")
        
        return {
            'title': title,
            'description': description,
            'image_url': image_url,
            'ingredients': ingredients,
            'steps': steps,
            'raw_text': raw_text
        }

    def run(self, url):
        """Main method to extract recipe from NYTimes URL."""
        try:
            self.setup_driver()
            
            if not self.check_nytimes_login():
                raise Exception("NYTimes Cooking login required. Please log in manually to Chrome and try again.")
            
            recipe_data = self.extract_recipe_data(url)
            return recipe_data
        finally:
            if self.driver:
                print("🚪 Closing browser.")
                self.driver.quit()


def get_recipe_extractor(url):
    """Get the appropriate recipe extractor based on URL."""
    if 'instagram.com' in url:
        return InstagramRecipeExtractor()
    elif 'cooking.nytimes.com' in url:
        return NYTimesRecipeExtractor()
    else:
        raise Exception(f"Unsupported URL: {url}")

def extract_recipe_data(url, manual_login=False):
    """Main function to extract recipe data from any supported URL."""
    if 'instagram.com' in url:
        print("📱 Using Instagram recipe extractor")
        extractor = InstagramRecipeExtractor()
        return extractor.run(url, manual_login=manual_login)
    elif 'cooking.nytimes.com' in url:
        print("📰 Using NYTimes Cooking recipe extractor")
        extractor = NYTimesRecipeExtractor()
        return extractor.run(url)
    else:
        raise Exception(f"Unsupported URL: {url}") 