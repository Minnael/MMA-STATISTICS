import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, Optional

class UFCFighterScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_fighter_data(self, fighter_url: str) -> Dict:
        try:
            response = self.session.get(fighter_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            name = self._extract_fighter_name(soup)
            image_url = self._extract_fighter_image(soup)
            stats = self._extract_specific_stats(soup)
            
            return {
                'name': name,
                'url': fighter_url,
                'image_url': image_url,
                **stats
            }
        except:
            return {}

    def _extract_fighter_name(self, soup: BeautifulSoup) -> str:
        name_selectors = ['h1.hero-profile__name', '.hero-profile__name', 'h1']
        for selector in name_selectors:
            name_element = soup.select_one(selector)
            if name_element:
                return name_element.get_text(strip=True)
        return "N/A"

    def _extract_fighter_image(self, soup: BeautifulSoup) -> str:
        """Extrai a URL da imagem do lutador"""
        image_selectors = [
            '.hero-profile__image img',
            '.hero-profile__image-wrap img',
            '.athlete-image img',
            '.hero-image img',
            'img[alt*="headshot"]',
            'img[src*="headshot"]'
        ]
        
        for selector in image_selectors:
            img_element = soup.select_one(selector)
            if img_element:
                src = img_element.get('src')
                if src:
                    # Se a URL for relativa, converte para absoluta
                    if src.startswith('//'):
                        return 'https:' + src
                    elif src.startswith('/'):
                        return 'https://www.ufc.com.br' + src
                    elif src.startswith('http'):
                        return src
        return None

    def _extract_specific_stats(self, soup: BeautifulSoup) -> Dict:
        stats = {
            'slpm': None, 'sapm': None, 'strike_acc': None, 'strike_def': None,
            'td_avg15': None, 'td_acc': None, 'td_def': None, 'sub_avg15': None,
            'kd_avg': None, 'aft_minutes': None
        }
        
        # Precisão de striking e takedown dos gráficos circulares
        charts = soup.find_all('svg', class_='e-chart-circle')
        for chart in charts:
            title = chart.find('title')
            if title:
                title_text = title.get_text().lower()
                percent_text = chart.find('text', class_='e-chart-circle__percent')
                if percent_text:
                    try:
                        percent_float = float(percent_text.get_text(strip=True).replace('%', '')) / 100.0
                        if 'striking' in title_text or 'golpes' in title_text:
                            stats['strike_acc'] = percent_float
                        elif 'quedas' in title_text or 'takedown' in title_text:
                            stats['td_acc'] = percent_float
                    except:
                        pass
        
        # Estatísticas dos grupos
        all_groups = soup.find_all('div', class_=re.compile(r'c-stat-compare__group'))
        for group in all_groups:
            number_elem = group.find('div', class_='c-stat-compare__number')
            label_elem = group.find('div', class_='c-stat-compare__label')
            if not number_elem or not label_elem:
                continue
                
            label = label_elem.get_text(strip=True).lower()
            value_text = number_elem.get_text(strip=True)
            
            percent_elem = number_elem.find('div', class_='c-stat-compare__percent')
            if percent_elem:
                percent_text = percent_elem.get_text(strip=True)
                value_text = value_text.replace(percent_text, '') + percent_text
            
            numeric_value = self._extract_numeric_value(value_text)
            
            if label == 'golpes sig. conectados':
                stats['slpm'] = numeric_value
            elif label == 'golpes sig. absorvidos':
                stats['sapm'] = numeric_value
            elif 'defesa de golpes sig' in label:
                stats['strike_def'] = numeric_value / 100.0 if numeric_value and '%' in value_text else numeric_value
            elif label == 'média de quedas':
                stats['td_avg15'] = numeric_value
            elif label == 'defesa de quedas':
                stats['td_def'] = numeric_value / 100.0 if numeric_value and '%' in value_text else numeric_value
            elif label == 'média de finalizações':
                stats['sub_avg15'] = numeric_value
            elif label == 'média de knockdowns':
                stats['kd_avg'] = numeric_value
            elif label == 'tempo médio de luta':
                stats['aft_minutes'] = self._convert_time_to_minutes(value_text)
        
        return stats

    def _extract_numeric_value(self, text: str) -> Optional[float]:
        try:
            numeric_text = re.sub(r'[^\d.,]', '', text.replace(',', '.'))
            return float(numeric_text) if numeric_text else None
        except:
            return None

    def _convert_time_to_minutes(self, time_text: str) -> Optional[float]:
        try:
            clean_time = re.sub(r'[^\d:]', '', time_text)
            if ':' in clean_time:
                parts = clean_time.split(':')
                if len(parts) == 2:
                    return int(parts[0]) + (int(parts[1]) / 60.0)
            return self._extract_numeric_value(time_text)
        except:
            return None

    def save_to_json(self, data: Dict, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scraper = UFCFighterScraper()
    fighter_url = 'https://www.ufc.com.br/athlete/dricus-du-plessis'
    fighter_data = scraper.get_fighter_data(fighter_url)
    
    if fighter_data:
        filename = f"{fighter_data.get('name', 'fighter').lower().replace(' ', '_')}_stats.json"
        scraper.save_to_json(fighter_data, filename)
