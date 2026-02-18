HEAVY_INDUSTRY_KEYWORDS = {
    "aluminium": 2.0,
    "acier": 2.0,
    "ciment": 2.0,
    "mines": 2.0,
    "industri": 1.5,
    "énergie": 1.2,
    "tarif": 1.7,
    "régie": 1.7,
    "carbone": 1.4,
    "efficacité": 1.8,
    "subvention": 1.5,
    "hydrogène": 1.5,
}


CATEGORY_RULES = {
    "réglementation": ["régie", "réglement", "conformité", "loi", "décret"],
    "tarifs": ["tarif", "prix", "facture", "coût", "indexation"],
    "subventions": ["subvention", "programme", "aide", "financement"],
    "technologies": ["ia", "smart", "hydrogène", "électrification", "batterie"],
}


def compute_impact_score(text: str) -> float:
    low = text.lower()
    score = 0.0
    for k, weight in HEAVY_INDUSTRY_KEYWORDS.items():
        if k in low:
            score += weight
    return round(score, 2)


def classify_category(text: str) -> str:
    low = text.lower()
    for category, keys in CATEGORY_RULES.items():
        if any(k in low for k in keys):
            return category
    return "general"


def confidence_from_score(score: float) -> str:
    if score >= 3.5:
        return "Élevé"
    if score >= 1.5:
        return "Moyen"
    return "Faible"
