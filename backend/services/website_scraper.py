"""
Website Scraper Service - Import products from company websites
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse


class WebsiteScraper:
    """Scrape product information from company websites"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def scrape_products(self, url: str, company_name: str) -> Dict:
        """
        Scrape products from a website URL
        Returns: {
            'success': bool,
            'products': List[Dict],
            'error': Optional[str]
        }
        """
        try:
            # Fetch website content
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different scraping strategies based on common patterns
            products = []
            
            # Strategy 1: Look for common product listing patterns
            product_elements = self._find_product_elements(soup)
            
            for element in product_elements:
                product_data = self._extract_product_info(element, url)
                if product_data:
                    products.append(product_data)
            
            # If no products found, try alternative strategies
            if not products:
                products = self._extract_products_from_tables(soup)
            
            if not products:
                products = self._extract_products_from_lists(soup)
            
            return {
                'success': True,
                'products': products[:100],  # Limit to 100 products
                'total_found': len(products),
                'error': None
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'products': [],
                'total_found': 0,
                'error': f'Failed to fetch website: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'products': [],
                'total_found': 0,
                'error': f'Scraping error: {str(e)}'
            }
    
    def _find_product_elements(self, soup):
        """Find product elements using common CSS selectors"""
        selectors = [
            '.product-item',
            '.product-card',
            '.product',
            '[class*="product"]',
            '.item',
            '[data-product]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if len(elements) > 3:  # Need at least a few products
                return elements
        
        return []
    
    def _extract_product_info(self, element, base_url: str) -> Optional[Dict]:
        """Extract product information from a single element"""
        try:
            # Extract product name
            name_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a', 'span'])
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name or len(name) < 3:
                return None
            
            # Extract description
            desc_elem = element.find(['p', 'div', 'span'], class_=re.compile(r'desc|detail|info', re.I))
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Extract category (guess from text)
            category = self._guess_category(name, description)
            
            return {
                'name': name[:200],
                'description': description[:500] if description else f"Product from website",
                'category': category,
                'sub_category': None,
                'target_crops': None,
                'target_problems': None,
                'dosage': None,
                'usage_instructions': None,
                'safety_precautions': None,
                'is_active': True
            }
            
        except Exception:
            return None
    
    def _extract_products_from_tables(self, soup) -> List[Dict]:
        """Extract products from HTML tables"""
        products = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True)
                    if name and len(name) > 3:
                        products.append({
                            'name': name[:200],
                            'description': cells[1].get_text(strip=True)[:500] if len(cells) > 1 else "",
                            'category': self._guess_category(name, ""),
                            'is_active': True
                        })
        
        return products
    
    def _extract_products_from_lists(self, soup) -> List[Dict]:
        """Extract products from lists (ul/ol)"""
        products = []
        lists = soup.find_all(['ul', 'ol'])
        
        for list_elem in lists:
            items = list_elem.find_all('li')
            if len(items) > 5:  # Likely a product list
                for item in items:
                    text = item.get_text(strip=True)
                    if text and len(text) > 3:
                        products.append({
                            'name': text[:200],
                            'description': f"Product extracted from website",
                            'category': self._guess_category(text, ""),
                            'is_active': True
                        })
        
        return products
    
    def _guess_category(self, name: str, description: str) -> str:
        """Guess product category from name/description"""
        text = f"{name} {description}".lower()
        
        if any(word in text for word in ['seed', 'बीज', 'variety', 'hybrid']):
            return 'seed'
        elif any(word in text for word in ['pesticide', 'insecticide', 'fungicide', 'herbicide', 'कीटनाशक']):
            return 'pesticide'
        elif any(word in text for word in ['fertilizer', 'खाद', 'nutrient', 'manure']):
            return 'fertilizer'
        elif any(word in text for word in ['equipment', 'tool', 'machine', 'यंत्र']):
            return 'equipment'
        else:
            return 'other'


# Singleton instance
scraper = WebsiteScraper()
