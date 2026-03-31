import requests
from bs4 import BeautifulSoup
import json


class SEOAnalyzer:
    def __init__(self, url):
        self.url = url
        self.results = {}

    def analyze(self):
        try:
            # Add https if not present
            if not self.url.startswith('http'):
                self.url = 'https://' + self.url

            response = requests.get(self.url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # SEO Analysis
            title = soup.find('title')
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            h1_tags = soup.find_all('h1')
            images = soup.find_all('img')

            # Calculate score
            score = 100
            issues = []

            if not title:
                score -= 20
                issues.append("Missing title tag")

            if not meta_desc:
                score -= 15
                issues.append("Missing meta description")

            if len(h1_tags) == 0:
                score -= 10
                issues.append("No H1 tag found")
            elif len(h1_tags) > 1:
                score -= 5
                issues.append("Multiple H1 tags found")

            # Images without alt
            images_without_alt = [img for img in images if not img.get('alt')]
            if images_without_alt:
                score -= len(images_without_alt) * 2
                issues.append(f"{len(images_without_alt)} images missing alt text")

            return {
                'success': True,
                'url': self.url,
                'score': max(0, score),
                'title': title.text if title else "No title",
                'meta_description': meta_desc['content'][:150] if meta_desc else "No description",
                'h1_count': len(h1_tags),
                'word_count': len(soup.get_text().split()),
                'issues': issues[:5],
                'recommendations': [
                    "Add title tag" if not title else None,
                    "Add meta description" if not meta_desc else None,
                    "Add H1 tag" if len(h1_tags) == 0 else None,
                    "Add alt text to images" if images_without_alt else None
                ]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }