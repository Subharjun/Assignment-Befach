"""Deterministic keyword → category / brand hints.

Small LLMs (qwen2.5:3b) often forget to set `category` when the user gives a
short follow-up like "yeah iPhone I want". This module is a cheap, exact-match
safety net that runs alongside the LLM's intent extraction.
"""
from __future__ import annotations

import re

# Keyword → canonical category. Lowercased; matched as whole words.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Mobiles": [
        "iphone", "phone", "phones", "smartphone", "mobile", "mobiles",
        "samsung galaxy", "galaxy s", "galaxy a", "galaxy m", "galaxy f",
        "oneplus", "pixel", "redmi", "poco", "vivo", "oppo", "realme", "motorola", "nothing phone",
    ],
    "Laptops": [
        "laptop", "laptops", "macbook", "notebook", "thinkpad", "ultrabook",
        "rog strix", "predator", "alienware", "ideapad", "vivobook", "zenbook",
        "surface laptop", "gaming laptop", "creator laptop",
    ],
    "Audio": [
        "headphone", "headphones", "earbud", "earbuds", "earphone", "earphones",
        "airpods", "neckband", "anc", "noise cancelling", "noise-cancelling",
        "wireless headphones", "speaker", "soundbar",
    ],
    "Monitors": [
        "monitor", "monitors", "display", "screen", "ultrawide", "144hz", "240hz",
    ],
    "Accessories": [
        "mouse", "keyboard", "mechanical keyboard", "webcam", "cooling pad",
        "usb hub", "usb-c hub", "laptop stand", "power bank", "charger",
    ],
    "Footwear": [
        "shoes", "shoe", "sneakers", "sneaker", "running shoes", "trainers",
        "boots", "hiking shoes", "tennis shoes",
    ],
    "Clothing": [
        "jeans", "t-shirt", "tshirt", "t shirt", "shirt", "hoodie",
        "sweatshirt", "chinos", "trousers", "track pants",
    ],
    "Beauty": [
        "serum", "moisturiser", "moisturizer", "sunscreen", "face wash",
        "lipstick", "mascara", "hair oil", "niacinamide", "skincare",
    ],
    "Books": [
        "book", "books", "novel", "paperback", "hardcover",
    ],
    "Kitchen": [
        "air fryer", "airfryer", "mixer grinder", "induction", "pressure cooker",
        "kettle", "microwave", "toaster", "coffee maker", "food processor",
    ],
    "Furniture": [
        "sofa", "bed", "mattress", "desk", "chair", "wardrobe", "bookshelf",
        "dining table", "recliner",
    ],
    "Eyewear": [
        "spectacles", "spectacle", "eyewear", "eyeglasses", "eyeglass",
        "glasses", "sunglasses", "sunglass", "shades", "frames",
        "aviator", "wayfarer", "ray-ban", "ray ban", "blue light glasses",
        "reading glasses",
    ],
}

# Brand → category (exact brand mention pins category even without product type word).
BRAND_TO_CATEGORY: dict[str, str] = {
    # Mobiles
    "iphone": "Mobiles", "samsung": "Mobiles", "oneplus": "Mobiles",
    "xiaomi": "Mobiles", "realme": "Mobiles", "vivo": "Mobiles", "oppo": "Mobiles",
    "google pixel": "Mobiles", "nothing": "Mobiles", "motorola": "Mobiles", "redmi": "Mobiles", "poco": "Mobiles",
    # Laptops (some overlap with Mobiles for Samsung/Apple — handled via keyword precedence)
    "macbook": "Laptops", "thinkpad": "Laptops", "rog": "Laptops",
    "predator": "Laptops", "alienware": "Laptops", "surface": "Laptops",
    # Audio
    "bose": "Audio", "sennheiser": "Audio", "airpods": "Audio", "jbl": "Audio",
    "boat": "Audio", "marshall": "Audio",
    # Footwear
    "nike": "Footwear", "adidas": "Footwear", "puma": "Footwear", "asics": "Footwear",
    "skechers": "Footwear", "reebok": "Footwear", "new balance": "Footwear",
    # Clothing
    "levis": "Clothing", "levi's": "Clothing", "uniqlo": "Clothing", "zara": "Clothing", "h&m": "Clothing",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


# Keyword → canonical brand (as stored in product `brand` field).
BRAND_ALIASES: dict[str, str] = {
    "iphone": "Apple",
    "apple": "Apple",
    "macbook": "Apple",
    "airpods": "Apple",
    "samsung": "Samsung",
    "galaxy": "Samsung",
    "oneplus": "OnePlus",
    "xiaomi": "Xiaomi",
    "redmi": "Xiaomi",
    "poco": "Xiaomi",
    "realme": "Realme",
    "vivo": "Vivo",
    "oppo": "Oppo",
    "google pixel": "Google",
    "pixel": "Google",
    "nothing": "Nothing",
    "motorola": "Motorola",
    "moto ": "Motorola",
    "bose": "Bose",
    "sony": "Sony",
    "sennheiser": "Sennheiser",
    "jbl": "JBL",
    "marshall": "Marshall",
    "boat": "boAt",
    "nike": "Nike",
    "adidas": "Adidas",
    "puma": "Puma",
    "asics": "Asics",
    "reebok": "Reebok",
    "skechers": "Skechers",
    "new balance": "New Balance",
    "levis": "Levi's",
    "levi's": "Levi's",
    "uniqlo": "Uniqlo",
    "zara": "Zara",
    "lenovo": "Lenovo",
    "thinkpad": "Lenovo",
    "legion": "Lenovo",
    "asus": "ASUS",
    "rog": "ASUS",
    "zenbook": "ASUS",
    "vivobook": "ASUS",
    "dell": "Dell",
    "alienware": "Dell",
    "hp ": "HP",
    "pavilion": "HP",
    "spectre": "HP",
    "omen": "HP",
    "acer": "Acer",
    "predator": "Acer",
    "msi": "MSI",
    "microsoft surface": "Microsoft",
    "surface laptop": "Microsoft",
    "lg ": "LG",
    # Eyewear
    "ray-ban": "Ray-Ban",
    "ray ban": "Ray-Ban",
    "oakley": "Oakley",
    "vincent chase": "Vincent Chase",
    "lenskart": "Lenskart",
    "john jacobs": "John Jacobs",
    "carrera": "Carrera",
    "tom ford": "Tom Ford",
    "persol": "Persol",
    "vogue eyewear": "Vogue Eyewear",
}


def hint_brand(*texts: str) -> str | None:
    """Detect an explicit brand mention. Multi-word aliases match first."""
    for text in texts:
        if not text:
            continue
        norm = _normalize(text)
        for kw in sorted(BRAND_ALIASES.keys(), key=len, reverse=True):
            if " " in kw and kw in norm:
                return BRAND_ALIASES[kw]
        for kw, brand in BRAND_ALIASES.items():
            if " " in kw:
                continue
            if re.search(rf"\b{re.escape(kw)}\b", norm):
                return brand
    return None


def hint_category(*texts: str) -> str | None:
    """Look across the given strings (most-recent first wins on ties) and
    return the first category we're confident about. Word-boundary match.
    """
    for text in texts:
        if not text:
            continue
        norm = _normalize(text)
        # 1) Multi-word product-type keywords (longest first).
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in sorted(keywords, key=len, reverse=True):
                if " " in kw and kw in norm:
                    return cat
        # 2) Single-word product-type keywords (\b match).
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if " " in kw:
                    continue
                if re.search(rf"\b{re.escape(kw)}\b", norm):
                    return cat
        # 3) Brand mention.
        for brand, cat in BRAND_TO_CATEGORY.items():
            if re.search(rf"\b{re.escape(brand)}\b", norm):
                return cat
    return None
