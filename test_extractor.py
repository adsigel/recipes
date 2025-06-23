#!/usr/bin/env python3
"""
Test script for Instagram Recipe Extractor
This script demonstrates the functionality with sample data
"""

from recipe_extractor import InstagramRecipeExtractor
import json

def test_extractor():
    """Test the recipe extractor with sample data"""
    
    # Initialize the extractor
    extractor = InstagramRecipeExtractor()
    
    # Test URLs (these are examples - you'll need real Instagram URLs)
    test_urls = [
        "https://www.instagram.com/p/example1/",
        "https://www.instagram.com/reel/example2/",
        "https://www.instagram.com/tv/example3/"
    ]
    
    print("🍳 Instagram Recipe Extractor - Test Mode")
    print("=" * 50)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nTest {i}: {url}")
        print("-" * 30)
        
        # Test URL validation
        is_valid = extractor._is_valid_instagram_url(url)
        print(f"URL Valid: {is_valid}")
        
        if is_valid:
            # Test extraction (this will fail with fake URLs, but shows the process)
            try:
                result = extractor.extract_recipe_from_url(url)
                print(f"Extraction Result: {result.get('error', 'Success')}")
                
                if not result.get('error'):
                    print(f"Title: {result.get('title', 'N/A')}")
                    print(f"Ingredients: {len(result.get('ingredients', []))}")
                    print(f"Steps: {len(result.get('steps', []))}")
            except Exception as e:
                print(f"Extraction Error: {str(e)}")
        
        print()
    
    # Test text parsing with sample recipe text
    print("Testing Text Parsing with Sample Recipe:")
    print("-" * 40)
    
    sample_text = """
    How to Make Chocolate Chip Cookies
    
    Ingredients:
    • 2 cups all-purpose flour
    • 1/2 cup butter
    • 1 cup chocolate chips
    • 1/2 cup sugar
    • 2 eggs
    
    Instructions:
    1. Preheat oven to 350°F
    2. Mix flour and sugar in a bowl
    3. Add melted butter and eggs
    4. Stir in chocolate chips
    5. Bake for 12 minutes
    """
    
    recipe_data = extractor._parse_recipe_from_text(sample_text)
    
    print(f"Title: {recipe_data['title']}")
    print(f"Description: {recipe_data['description'][:100]}...")
    print(f"Ingredients ({len(recipe_data['ingredients'])}):")
    for ingredient in recipe_data['ingredients']:
        print(f"  • {ingredient}")
    
    print(f"\nSteps ({len(recipe_data['steps'])}):")
    for i, step in enumerate(recipe_data['steps'], 1):
        print(f"  {i}. {step}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_extractor() 