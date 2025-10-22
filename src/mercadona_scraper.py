import requests
import pandas as pd
import time
import random
import os
from pathlib import Path
from typing import Set, List, Dict, Any
import json

class MercadonaScraper:
    def __init__(self):
        self.base_url = "https://tienda.mercadona.es/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Track fetched IDs
        self.fetched_category_ids: Set[int] = set()
        self.fetched_product_ids: Set[str] = set()
        
        # Storage
        self.products_data: List[Dict[str, Any]] = []
        
        # Create image directory
        Path("./img").mkdir(exist_ok=True)
        
    def polite_delay(self):
        """Random delay between 0.5 and 1.5 seconds"""
        time.sleep(random.uniform(0.5, 1.5))
    
    def safe_request(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """Make API request with error handling and retries"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"  ⚠️  Error fetching {url}: {e}")
                if attempt < max_retries - 1:
                    print(f"  Retrying ({attempt + 2}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"  ❌ Failed after {max_retries} attempts")
                    return {}
        return {}
    
    def extract_all_category_ids(self, data: Dict[str, Any]) -> Set[int]:
        """Recursively extract all category IDs from nested structure"""
        category_ids = set()
        
        if isinstance(data, dict):
            if 'id' in data:
                category_ids.add(data['id'])
            if 'categories' in data:
                for cat in data['categories']:
                    category_ids.update(self.extract_all_category_ids(cat))
        elif isinstance(data, list):
            for item in data:
                category_ids.update(self.extract_all_category_ids(item))
        
        return category_ids
    
    def fetch_all_categories(self) -> Set[int]:
        """Fetch all category IDs from the categories endpoint"""
        print("📂 Fetching all categories...")
        url = f"{self.base_url}/categories/"
        data = self.safe_request(url)
        
        if not data or 'results' not in data:
            print("❌ Failed to fetch categories")
            return set()
        
        all_ids = self.extract_all_category_ids(data['results'])
        print(f"✅ Found {len(all_ids)} unique categories")
        return all_ids
    
    def fetch_products_from_category(self, category_id: int) -> Set[str]:
        """Fetch all product IDs from a category"""
        if category_id in self.fetched_category_ids:
            return set()
        
        url = f"{self.base_url}/categories/{category_id}/"
        data = self.safe_request(url)
        self.polite_delay()
        
        self.fetched_category_ids.add(category_id)
        
        if not data:
            return set()
        
        product_ids = set()
        if 'categories' in data:
            for cat in data['categories']:
                if 'products' in cat:
                    for product in cat['products']:
                        if 'id' in product:
                            product_ids.add(str(product['id']))
        
        return product_ids
    
    def flatten_categories(self, categories: List[Dict]) -> Dict[str, Any]:
        """Flatten nested categories structure"""
        flattened = {}
        
        for cat in categories:
            level = cat.get('level', 0)
            flattened[f'level_{level}_cat_id'] = cat.get('id')
            flattened[f'level_{level}_cat_name'] = cat.get('name')
            flattened[f'level_{level}_cat_order'] = cat.get('order')
            
            if 'categories' in cat:
                nested = self.flatten_categories(cat['categories'])
                flattened.update(nested)
        
        return flattened
    
    def flatten_photos(self, photos: List[Dict]) -> Dict[str, Any]:
        """Flatten photos structure"""
        flattened = {}
        for i, photo in enumerate(photos):
            flattened[f'img_{i}_url'] = photo.get('zoom')
            flattened[f'img_{i}_perspective'] = photo.get('perspective')
        return flattened
    
    def download_image(self, url: str, filepath: str) -> bool:
        """Download image from URL"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"  ⚠️  Failed to download image {url}: {e}")
            return False
    
    def fetch_product_details(self, product_id: str) -> bool:
        """Fetch and process product details"""
        if product_id in self.fetched_product_ids:
            return False
        
        url = f"{self.base_url}/products/{product_id}/"
        data = self.safe_request(url)
        self.polite_delay()
        
        self.fetched_product_ids.add(product_id)
        
        if not data:
            return False
        
        # Flatten the product data
        flattened = {
            'id': data.get('id'),
            'ean': data.get('ean'),
            'status': data.get('status'),
            'is_bulk': data.get('is_bulk'),
            'packaging': data.get('packaging'),
            'published': data.get('published'),
            'share_url': data.get('share_url'),
            'display_name': data.get('display_name'),
            'is_variable_weight': data.get('is_variable_weight'),
        }
        
        # Flatten details
        if 'details' in data and data['details']:
            for key, value in data['details'].items():
                flattened[f'details_{key}'] = value
        
        # Flatten price_instructions
        if 'price_instructions' in data and data['price_instructions']:
            for key, value in data['price_instructions'].items():
                flattened[f'price_{key}'] = value
        
        # Flatten nutrition_information
        if 'nutrition_information' in data and data['nutrition_information']:
            for key, value in data['nutrition_information'].items():
                flattened[key] = value
        
        # Flatten categories
        if 'categories' in data and data['categories']:
            cat_flattened = self.flatten_categories(data['categories'])
            flattened.update(cat_flattened)
        
        # Flatten photos and download images
        if 'photos' in data and data['photos']:
            photo_flattened = self.flatten_photos(data['photos'])
            flattened.update(photo_flattened)
            
            # Download images
            for i, photo in enumerate(data['photos']):
                if 'zoom' in photo:
                    img_path = f"./img/{product_id}_img_{i}.jpg"
                    self.download_image(photo['zoom'], img_path)
        
        self.products_data.append(flattened)
        return True
    
    def save_progress(self):
        """Save current progress to CSV"""
        if self.products_data:
            df = pd.DataFrame(self.products_data)
            df.to_csv('mercadona_progress.csv', index=False)
            print(f"💾 Progress saved: {len(self.products_data)} products")
    
    def scrape_all(self):
        """Main scraping workflow"""
        print("🚀 Starting Mercadona scraper...\n")
        
        # Step 1: Get all categories
        all_category_ids = self.fetch_all_categories()
        if not all_category_ids:
            print("❌ No categories found. Exiting.")
            return
        
        print(f"\n🔍 Processing {len(all_category_ids)} categories...\n")
        
        # Step 2: Get all product IDs from categories
        all_product_ids = set()
        for i, cat_id in enumerate(all_category_ids, 1):
            print(f"[{i}/{len(all_category_ids)}] Category {cat_id}...", end=" ")
            product_ids = self.fetch_products_from_category(cat_id)
            all_product_ids.update(product_ids)
            print(f"Found {len(product_ids)} products")
            
            # Save progress every 10 categories
            if i % 10 == 0:
                self.save_progress()
        
        print(f"\n✅ Found {len(all_product_ids)} unique products\n")
        print(f"🛒 Fetching product details...\n")
        
        # Step 3: Fetch all product details
        for i, product_id in enumerate(all_product_ids, 1):
            print(f"[{i}/{len(all_product_ids)}] Product {product_id}...", end=" ")
            if self.fetch_product_details(product_id):
                print("✅")
            else:
                print("⏭️  (skipped)")
            
            # Save progress every 50 products
            if i % 50 == 0:
                self.save_progress()
        
        # Final save
        print("\n💾 Creating final DataFrame and saving...\n")
        mercadona = pd.DataFrame(self.products_data)
        mercadona.to_csv('mercadona.csv', index=False)
        
        print(f"✅ Complete! Scraped {len(mercadona)} products")
        print(f"📁 Data saved to: mercadona.csv")
        print(f"🖼️  Images saved to: ./img/")
        
        return mercadona


# Run the scraper
if __name__ == "__main__":
    scraper = MercadonaScraper()
    df = scraper.scrape_all()
