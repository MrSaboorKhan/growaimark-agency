import random


class KeywordResearch:
    def __init__(self, seed_keyword):
        self.seed = seed_keyword

    def get_suggestions(self):
        # Mock data - Replace with actual API later
        keywords = [
            f"{self.seed} services",
            f"best {self.seed}",
            f"{self.seed} agency",
            f"{self.seed} tools",
            f"{self.seed} expert",
            f"{self.seed} consultant",
            f"affordable {self.seed}",
            f"professional {self.seed}"
        ]

        results = []
        for kw in keywords:
            results.append({
                'keyword': kw,
                'volume': random.randint(100, 5000),
                'competition': random.choice(['Low', 'Medium', 'High']),
                'cpc': round(random.uniform(0.5, 5.0), 2)
            })

        return sorted(results, key=lambda x: x['volume'], reverse=True)[:10]