"""Procedurally generate ~2000 realistic-looking products across categories.

Importable: `from scripts.generate_products import generate_products`
"""
from __future__ import annotations

import random
from typing import Iterable

random.seed(42)


# Curated free-to-use Unsplash photo IDs per category.
IMAGES: dict[str, list[str]] = {
    "Laptops": [
        "1593642632559-0c6d3fc62b89",
        "1603302576837-37561b2e2302",
        "1611186871348-b1ce696e52c9",
        "1496181133206-80ce9b88a853",
        "1517336714731-489689fd1ca8",
        "1531297484001-80022131f5a1",
    ],
    "Mobiles": [
        "1592286927505-1def25115558",
        "1610945265064-0e34e5519bbf",
        "1511707171634-5f897ff02aa9",
        "1601784551446-20c9e07cdbdb",
        "1556656793-08538906a9f8",
    ],
    "Audio": [
        "1583394838336-acd977736f90",
        "1545127398-14699f92334b",
        "1505740420928-5e560c06d30e",
        "1484704849700-f032a568e944",
        "1546435770-a3e426bf472b",
    ],
    "Monitors": [
        "1527443224154-c4a3942d3acf",
        "1547119957-637f8679db1e",
        "1593640408182-31c70c8268f5",
    ],
    "Accessories": [
        "1527814050087-3793815479db",
        "1593305841991-05c297ba4575",
        "1587829741301-dc798b83add3",
        "1572569511254-d8f925fe2cbb",
    ],
    "Footwear": [
        "1542291026-7eec264c27ff",
        "1606107557195-0e29a4b5b4aa",
        "1600185365926-3a2ce3cdb9eb",
        "1539185441755-769473a23570",
    ],
    "Clothing": [
        "1542272604-787c3835535d",
        "1521572163474-6864f9cf17ab",
        "1551488831-00ddcb6c6bd3",
        "1620799140408-edc6dcb6d633",
        "1503342217505-b0a15ec3261c",
    ],
    "Beauty": [
        "1556228720-195a672e8a03",
        "1571781926291-c477ebfd024b",
        "1522335789203-aabd1fc54bc9",
        "1596462502278-27bfdc403348",
    ],
    "Books": [
        "1544716278-ca5e3f4abd8c",
        "1512820790803-83ca734da794",
        "1495446815901-a7297e633e8d",
    ],
    "Kitchen": [
        "1574781330855-d0db8cc6a79c",
        "1556909114-f6e7ad7d3136",
        "1585515320310-259814833e62",
    ],
    "Furniture": [
        "1505693416388-ac5ce068fe85",
        "1555041469-a586c61ea9bc",
        "1581539250439-c96689b516dd",
    ],
    "Eyewear": [
        "1574258495973-f010dfbb5371",
        "1572635196237-14b3f281503f",
        "1577803645773-f96470509666",
        "1511499767150-a48a237f0083",
        "1473496169904-658ba7c44d8a",
        "1591076482161-42ce6da69f67",
    ],
}


# Subcategory-specific image overrides. When a subcategory key is present
# here, we use one of these URLs instead of the broad category pool. This
# prevents e.g. a Phone Cover from showing a wireless-mouse photo.
#
# For subcategories where I don't have well-verified Unsplash IDs, fall back
# to placehold.co with a clean label so the product is at least clearly
# identified (a scaffold concession — real images would come from Cloudinary).
def _placeholder(label: str, bg: str = "f5f5f7", fg: str = "1f2937") -> str:
    safe = label.replace(" ", "+").replace("/", "+")
    return f"https://placehold.co/600x600/{bg}/{fg}.png?text={safe}&font=lato"


SUBCATEGORY_IMAGES: dict[str, list[str]] = {
    # Phone-protection & charging accessories
    "Phone Case": [_placeholder("Phone+Case")],
    "Phone Cover": [_placeholder("Phone+Cover")],
    "Screen Protector": [_placeholder("Screen+Protector")],
    "Tempered Glass": [_placeholder("Tempered+Glass")],
    "Fast Charger 65W": [_placeholder("Fast+Charger+65W")],
    "Type-C Cable": [_placeholder("USB-C+Cable")],
    "Wireless Charger 15W": [_placeholder("Wireless+Charger")],
    "Car Phone Mount": [_placeholder("Car+Phone+Mount")],
    "AirTag Holder": [_placeholder("AirTag+Holder")],
    "Power Bank 10000mAh": [_placeholder("Power+Bank+10000mAh")],
    "Power Bank 20000mAh": [_placeholder("Power+Bank+20000mAh")],
    "Phone Stand": [_placeholder("Phone+Stand")],
    # Peripherals (these subcategories have decent Unsplash photos in the pool,
    # but the rest of Accessories share them — pin them here so they only go to
    # the right subcategory).
    "Wireless Mouse": ["https://images.unsplash.com/photo-1527814050087-3793815479db?w=800"],
    "Gaming Mouse": ["https://images.unsplash.com/photo-1527814050087-3793815479db?w=800"],
    "Mechanical Keyboard": ["https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800"],
    "USB-C Hub": [_placeholder("USB-C+Hub")],
    "Laptop Stand": [_placeholder("Laptop+Stand")],
    "Cooling Pad": ["https://images.unsplash.com/photo-1593305841991-05c297ba4575?w=800"],
    "Webcam 1080p": [_placeholder("1080p+Webcam")],
    "Webcam 4K": [_placeholder("4K+Webcam")],
}


def _img(cat: str, subcategory: str | None = None) -> str:
    if subcategory and subcategory in SUBCATEGORY_IMAGES:
        return random.choice(SUBCATEGORY_IMAGES[subcategory])
    return f"https://images.unsplash.com/photo-{random.choice(IMAGES[cat])}?w=800"


def _slug(*parts: str) -> str:
    s = "-".join(parts).lower()
    out = []
    for c in s:
        if c.isalnum():
            out.append(c)
        elif c in (" ", "-", "_", "/"):
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


# ------------------------------------------------------------------ catalog
LAPTOP_SERIES_BY_BRAND: dict[str, list[str]] = {
    "Acer": ["Predator Helios", "Aspire", "Swift", "Nitro V", "Spin"],
    "ASUS": ["ROG Strix", "ROG Zephyrus", "TUF Gaming", "Vivobook", "Zenbook"],
    "Dell": ["Inspiron", "XPS", "Latitude", "Vostro", "Alienware m16"],
    "HP": ["Pavilion", "Spectre x360", "Envy", "Omen", "EliteBook"],
    "Lenovo": ["ThinkPad", "IdeaPad Slim", "Legion", "Yoga", "ThinkBook"],
    "MSI": ["Stealth", "Katana", "Sword", "Modern", "Prestige"],
    "Apple": ["MacBook Air 13", "MacBook Air 15", "MacBook Pro 14", "MacBook Pro 16"],
    "Samsung": ["Galaxy Book", "Galaxy Book Pro", "Galaxy Book Ultra"],
    "LG": ["Gram", "Gram Pro", "Gram Style"],
    "Microsoft": ["Surface Laptop", "Surface Laptop Studio", "Surface Pro"],
}
LAPTOP_BRANDS = list(LAPTOP_SERIES_BY_BRAND.keys())
LAPTOP_SPECS = [
    ("i5", 16, 512, "RTX 3050"), ("i7", 16, 512, "RTX 4050"), ("i7", 32, 1024, "RTX 4060"),
    ("i9", 32, 1024, "RTX 4070"), ("i9", 64, 2048, "RTX 4080"), ("Ryzen 5", 16, 512, "RX 6600M"),
    ("Ryzen 7", 16, 1024, "RX 7600M"), ("Ryzen 9", 32, 2048, "RX 7700M"),
    ("Apple M3", 16, 512, "integrated"), ("Apple M3 Pro", 18, 1024, "integrated"),
]
LAPTOP_USE = ["Gaming", "Creator", "Business", "Student", "Ultrabook"]

MOBILE_SERIES_BY_BRAND: dict[str, list[str]] = {
    "Apple": ["iPhone 15", "iPhone 15 Pro", "iPhone 14", "iPhone 14 Pro", "iPhone SE"],
    "Samsung": ["Galaxy S24", "Galaxy S24 Ultra", "Galaxy A55", "Galaxy M55", "Galaxy F55"],
    "OnePlus": ["12R", "12", "Nord 4", "Nord CE 4", "Open"],
    "Xiaomi": ["14", "14 Pro", "Redmi Note 13", "Redmi 13C", "Poco F6"],
    "Realme": ["12 Pro+", "GT Neo 6", "Narzo 70", "12x", "P1 Pro"],
    "Vivo": ["V30", "X100", "Y200", "V40", "T3 Ultra"],
    "Oppo": ["Find X8", "Reno 12 Pro", "A78", "F27", "K12"],
    "Google": ["Pixel 8", "Pixel 8 Pro", "Pixel 7a", "Pixel Fold"],
    "Nothing": ["Phone (2)", "Phone (2a)", "Phone (3a)", "CMF Phone 1"],
    "Motorola": ["Edge 50 Pro", "Edge 50 Fusion", "Razr 50", "G84", "G34"],
}
MOBILE_BRANDS = list(MOBILE_SERIES_BY_BRAND.keys())
MOBILE_STORAGE = ["128GB", "256GB", "512GB", "1TB"]
MOBILE_COLORS = ["Midnight", "Silver", "Graphite", "Phantom Black", "Sky Blue", "Forest Green", "Coral"]

AUDIO_BRANDS = ["Sony", "Bose", "Sennheiser", "JBL", "Apple", "Samsung", "Marshall", "boAt", "Nothing", "Bang & Olufsen"]
AUDIO_TYPES = ["Wireless Headphones", "Earbuds", "Neckband", "Over-Ear Headphones", "True Wireless Earbuds", "Sports Earbuds"]

MONITOR_BRANDS = ["LG", "Samsung", "Dell", "ASUS", "Acer", "BenQ", "MSI", "Gigabyte"]
MONITOR_SPECS = [("24\"", "FHD", "75Hz"), ("27\"", "QHD", "144Hz"), ("32\"", "4K", "144Hz"), ("34\"", "UWQHD", "165Hz"), ("27\"", "QHD", "240Hz"), ("32\"", "4K", "60Hz")]

ACCESS_TYPES = [
    "Wireless Mouse", "Gaming Mouse", "Mechanical Keyboard", "USB-C Hub",
    "Laptop Stand", "Cooling Pad", "Webcam 1080p", "Webcam 4K",
    "Phone Stand", "Power Bank 20000mAh", "Power Bank 10000mAh",
    "Phone Case", "Phone Cover", "Screen Protector", "Tempered Glass",
    "Fast Charger 65W", "Type-C Cable", "Wireless Charger 15W",
    "Car Phone Mount", "AirTag Holder",
]
ACCESS_BRANDS = ["Logitech", "Razer", "HyperX", "Anker", "Belkin", "Cooler Master", "SteelSeries", "Corsair", "Mi", "Portronics", "Spigen", "OtterBox", "Caseology"]

FOOTWEAR_BRANDS = ["Nike", "Adidas", "Puma", "Reebok", "Asics", "New Balance", "Skechers", "Under Armour", "Bata", "Woodland"]
FOOTWEAR_TYPES = ["Running Shoes", "Training Shoes", "Casual Sneakers", "Trail Running Shoes", "Tennis Shoes", "Basketball Shoes", "Walking Shoes", "Hiking Boots"]
FOOTWEAR_COLORS = ["Black", "White", "Navy", "Grey", "Red", "Olive", "Tan"]
FOOTWEAR_AUDIENCE = ["Men", "Women", "Unisex"]

CLOTHING_BRANDS = ["Levi's", "H&M", "Uniqlo", "Zara", "U.S. Polo Assn.", "Tommy Hilfiger", "Allen Solly", "Peter England", "Roadster", "Mufti"]
CLOTHING_TYPES = ["Slim Fit Jeans", "Straight Fit Jeans", "Crew Neck T-Shirt", "Polo T-Shirt", "Casual Shirt", "Formal Shirt", "Hoodie", "Sweatshirt", "Chinos", "Track Pants"]

BEAUTY_BRANDS = ["Minimalist", "The Ordinary", "Cetaphil", "L'Oréal", "Lakmé", "Maybelline", "Nivea", "Plum", "Mamaearth", "Forest Essentials"]
BEAUTY_TYPES = ["Niacinamide Serum", "Vitamin C Serum", "Hyaluronic Acid", "Sunscreen SPF 50", "Moisturiser", "Face Wash", "Body Lotion", "Lipstick", "Mascara", "Hair Oil"]

BOOKS_CATALOG: list[tuple[str, str]] = [
    ("The Psychology of Money", "Morgan Housel"),
    ("Atomic Habits", "James Clear"),
    ("Deep Work", "Cal Newport"),
    ("Sapiens", "Yuval Noah Harari"),
    ("Educated", "Tara Westover"),
    ("Thinking, Fast and Slow", "Daniel Kahneman"),
    ("Zero to One", "Peter Thiel"),
    ("Shoe Dog", "Phil Knight"),
    ("The Lean Startup", "Eric Ries"),
    ("Hooked", "Nir Eyal"),
    ("Range", "David Epstein"),
    ("The Almanack of Naval Ravikant", "Eric Jorgenson"),
    ("Build", "Tony Fadell"),
    ("Make Time", "Jake Knapp"),
    ("Show Your Work", "Austin Kleon"),
    ("Hyperfocus", "Chris Bailey"),
    ("Drive", "Daniel Pink"),
    ("Grit", "Angela Duckworth"),
    ("Mindset", "Carol Dweck"),
    ("Influence", "Robert Cialdini"),
]

KITCHEN_BRANDS = ["Philips", "Prestige", "Bajaj", "Havells", "Pigeon", "Wonderchef", "Borosil", "Morphy Richards", "InstantPot", "Cello"]
KITCHEN_TYPES = ["Air Fryer", "Mixer Grinder", "Induction Cooktop", "Pressure Cooker", "Electric Kettle", "Microwave Oven", "Toaster", "Coffee Maker", "Food Processor", "Sandwich Maker"]

FURNITURE_BRANDS = ["IKEA", "Urban Ladder", "Pepperfry", "HomeTown", "Wakefit", "Wooden Street", "Godrej Interio", "Nilkamal", "Sleepyhead", "The Sleep Company"]
FURNITURE_TYPES = ["Queen Bed Frame", "King Size Bed", "Study Desk", "Office Chair", "3-Seater Sofa", "Recliner", "Wardrobe", "Bookshelf", "Dining Table", "Mattress (Queen)"]

EYEWEAR_BRANDS = ["Ray-Ban", "Oakley", "Vincent Chase", "Lenskart", "John Jacobs", "Carrera", "Tom Ford", "Persol", "Vogue Eyewear", "Fossil"]
EYEWEAR_KIND = ["Eyeglasses", "Sunglasses", "Reading Glasses", "Blue-Light Glasses", "Aviator Sunglasses", "Wayfarer Sunglasses"]
EYEWEAR_SHAPE = ["Square", "Round", "Aviator", "Rectangle", "Cat-eye", "Wayfarer", "Oversized"]
EYEWEAR_MATERIAL = ["Metal", "Acetate", "Plastic", "Titanium", "TR90"]
EYEWEAR_COLOR = ["Black", "Tortoise", "Gold", "Silver", "Gunmetal", "Brown", "Crystal", "Matte Black"]


def _laptops(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(LAPTOP_BRANDS)
        series = random.choice(LAPTOP_SERIES_BY_BRAND[brand])
        # Apple silicon only ships in MacBooks; everything else uses Intel/AMD/Snapdragon.
        if brand == "Apple":
            specs = [s for s in LAPTOP_SPECS if "Apple" in s[0]]
        else:
            specs = [s for s in LAPTOP_SPECS if "Apple" not in s[0]]
        cpu, ram, storage, gpu = random.choice(specs)
        use = random.choice(LAPTOP_USE)
        # Don't append a year/size if the series already ends in a digit.
        suffix = "" if series and series[-1].isdigit() else " " + random.choice(["2024", "2023"])
        base = {
            "Gaming": 95000, "Creator": 110000, "Business": 75000, "Student": 55000, "Ultrabook": 85000,
        }[use]
        price = base + random.randint(-15000, 80000)
        title = f"{brand} {series}{suffix} — {use} Edition ({cpu}, {ram}GB, {storage}GB)"
        desc = f"{ram}GB RAM, {storage}GB SSD, {cpu} CPU, {gpu} graphics. Tuned for {use.lower()} workloads."
        yield {
            "category": "Laptops",
            "subcategory": use,
            "brand": brand,
            "title": title,
            "description": desc,
            "price": float(price),
            "rating": round(random.uniform(3.6, 4.8), 1),
            "rating_count": random.randint(40, 5000),
            "tags": [use.lower(), cpu.lower(), gpu.lower(), "laptop", brand.lower()],
            "attributes": {"cpu": cpu, "gpu": gpu, "ram_gb": ram, "storage_gb": storage},
            "stock": random.randint(0, 80),
        }


def _mobiles(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(MOBILE_BRANDS)
        series = random.choice(MOBILE_SERIES_BY_BRAND[brand])
        storage = random.choice(MOBILE_STORAGE)
        color = random.choice(MOBILE_COLORS)
        base_by_brand = {"Apple": 80000, "Samsung": 60000, "OnePlus": 45000, "Google": 60000, "Nothing": 35000}.get(brand, 25000)
        storage_mult = {"128GB": 1.0, "256GB": 1.12, "512GB": 1.3, "1TB": 1.55}[storage]
        price = int(base_by_brand * storage_mult + random.randint(-8000, 20000))
        title = f"{brand} {series} ({storage}, {color})"
        desc = f"{storage} storage, {color} finish. Premium display, fast-charge battery, dual-SIM 5G."
        yield {
            "category": "Mobiles",
            "subcategory": "Smartphone",
            "brand": brand,
            "title": title,
            "description": desc,
            "price": float(max(price, 8999)),
            "rating": round(random.uniform(3.8, 4.7), 1),
            "rating_count": random.randint(80, 12000),
            "tags": ["smartphone", brand.lower(), storage.lower(), color.lower(), "5g"],
            "attributes": {"storage": storage, "color": color},
            "stock": random.randint(0, 150),
        }


def _audio(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(AUDIO_BRANDS)
        kind = random.choice(AUDIO_TYPES)
        anc = random.choice([True, False, False])
        title = f"{brand} {kind}{' with ANC' if anc else ''}"
        base = {"Wireless Headphones": 12000, "Earbuds": 4000, "Neckband": 2500, "Over-Ear Headphones": 15000, "True Wireless Earbuds": 6000, "Sports Earbuds": 3000}[kind]
        price = int(base + random.randint(-1500, 18000))
        yield {
            "category": "Audio",
            "subcategory": kind,
            "brand": brand,
            "title": title,
            "description": f"{kind} from {brand}, Bluetooth 5.3, {'active noise cancellation, ' if anc else ''}long battery life.",
            "price": float(max(price, 999)),
            "rating": round(random.uniform(3.5, 4.8), 1),
            "rating_count": random.randint(50, 20000),
            "tags": ["audio", brand.lower(), kind.lower(), *(["anc"] if anc else [])],
            "attributes": {"anc": anc, "type": kind},
            "stock": random.randint(0, 200),
        }


def _monitors(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(MONITOR_BRANDS)
        size, res, hz = random.choice(MONITOR_SPECS)
        title = f"{brand} {size} {res} {hz} Gaming Monitor"
        base = {"FHD": 12000, "QHD": 22000, "UWQHD": 38000, "4K": 32000}[res]
        price = int(base + random.randint(-2000, 25000))
        yield {
            "category": "Monitors",
            "subcategory": "Gaming",
            "brand": brand,
            "title": title,
            "description": f"{size} {res} panel at {hz}, low input lag, ideal for gaming and creator work.",
            "price": float(price),
            "rating": round(random.uniform(3.8, 4.7), 1),
            "rating_count": random.randint(30, 3000),
            "tags": ["monitor", brand.lower(), res.lower(), hz.lower(), "gaming"],
            "attributes": {"size": size, "resolution": res, "refresh": hz},
            "stock": random.randint(0, 60),
        }


_ACCESS_BASE_PRICE = {
    "Wireless Mouse": 1500, "Gaming Mouse": 4500, "Mechanical Keyboard": 6000,
    "USB-C Hub": 2200, "Laptop Stand": 1800, "Cooling Pad": 2500,
    "Webcam 1080p": 3000, "Webcam 4K": 9500, "Phone Stand": 600,
    "Power Bank 20000mAh": 2500, "Power Bank 10000mAh": 1500,
    "Phone Case": 599, "Phone Cover": 499, "Screen Protector": 299,
    "Tempered Glass": 399, "Fast Charger 65W": 1499, "Type-C Cable": 399,
    "Wireless Charger 15W": 1799, "Car Phone Mount": 799, "AirTag Holder": 599,
}
# Spigen / OtterBox / Caseology specialise in phone protection; restrict their
# catalog entries to phone-relevant types so listings stay coherent.
_BRAND_KIND_BIAS = {
    "Spigen": ["Phone Case", "Phone Cover", "Screen Protector", "Tempered Glass", "Car Phone Mount"],
    "OtterBox": ["Phone Case", "Phone Cover", "Screen Protector", "Tempered Glass"],
    "Caseology": ["Phone Case", "Phone Cover", "Car Phone Mount"],
}
_PHONE_ACC = {"Phone Case", "Phone Cover", "Screen Protector", "Tempered Glass",
              "Fast Charger 65W", "Type-C Cable", "Wireless Charger 15W",
              "Car Phone Mount", "AirTag Holder", "Phone Stand",
              "Power Bank 10000mAh", "Power Bank 20000mAh"}


def _accessories(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(ACCESS_BRANDS)
        kind = random.choice(_BRAND_KIND_BIAS.get(brand, ACCESS_TYPES))
        title = f"{brand} {kind}"
        base = _ACCESS_BASE_PRICE[kind]
        price = int(base + random.randint(-int(base * 0.3), int(base * 1.5)))
        is_phone = kind in _PHONE_ACC
        tags = ["accessory", brand.lower(), kind.lower()]
        if is_phone:
            tags += ["phone", "smartphone", "mobile"]
        description_extra = (
            "Compatible with iPhone, Samsung Galaxy, OnePlus, Pixel and most modern smartphones."
            if is_phone
            else "Compact, reliable, well-reviewed."
        )
        yield {
            "category": "Accessories",
            "subcategory": kind,
            "brand": brand,
            "title": title,
            "description": f"{kind} by {brand}. {description_extra}",
            "price": float(max(price, 199)),
            "rating": round(random.uniform(3.6, 4.7), 1),
            "rating_count": random.randint(50, 30000),
            "tags": tags,
            "attributes": {"type": kind, "for_phone": is_phone},
            "stock": random.randint(0, 500),
        }


def _footwear(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(FOOTWEAR_BRANDS)
        kind = random.choice(FOOTWEAR_TYPES)
        color = random.choice(FOOTWEAR_COLORS)
        audience = random.choice(FOOTWEAR_AUDIENCE)
        title = f"{brand} {kind} - {audience} ({color})"
        price = random.randint(2999, 14999)
        yield {
            "category": "Footwear",
            "subcategory": kind,
            "brand": brand,
            "title": title,
            "description": f"{audience.lower()}'s {kind.lower()} in {color.lower()}. Breathable upper, cushioned midsole.",
            "price": float(price),
            "rating": round(random.uniform(3.7, 4.7), 1),
            "rating_count": random.randint(80, 9000),
            "tags": ["footwear", brand.lower(), kind.lower(), color.lower(), audience.lower()],
            "attributes": {"color": color, "audience": audience},
            "stock": random.randint(0, 200),
        }


def _clothing(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(CLOTHING_BRANDS)
        kind = random.choice(CLOTHING_TYPES)
        color = random.choice(["Black", "White", "Navy", "Olive", "Charcoal", "Beige", "Maroon"])
        title = f"{brand} {kind} ({color})"
        price = random.randint(499, 4999)
        yield {
            "category": "Clothing",
            "subcategory": kind,
            "brand": brand,
            "title": title,
            "description": f"{brand} {kind.lower()} in {color.lower()}. Soft fabric, regular fit, easy care.",
            "price": float(price),
            "rating": round(random.uniform(3.5, 4.6), 1),
            "rating_count": random.randint(100, 15000),
            "tags": ["clothing", brand.lower(), kind.lower(), color.lower()],
            "attributes": {"color": color},
            "stock": random.randint(0, 800),
        }


def _beauty(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(BEAUTY_BRANDS)
        kind = random.choice(BEAUTY_TYPES)
        title = f"{brand} {kind}"
        price = random.randint(249, 2999)
        yield {
            "category": "Beauty",
            "subcategory": "Skincare" if "Serum" in kind or "Sunscreen" in kind or "Moisturiser" in kind or "Wash" in kind or "Lotion" in kind or "Oil" in kind else "Makeup",
            "brand": brand,
            "title": title,
            "description": f"{brand}'s {kind.lower()}. Dermatologically tested, fragrance-free formula.",
            "price": float(price),
            "rating": round(random.uniform(3.7, 4.7), 1),
            "rating_count": random.randint(200, 50000),
            "tags": ["beauty", brand.lower(), kind.lower()],
            "attributes": {"type": kind},
            "stock": random.randint(0, 1000),
        }


def _books(n: int) -> Iterable[dict]:
    for _ in range(n):
        title, author = random.choice(BOOKS_CATALOG)
        edition = random.choice(["Paperback", "Hardcover", "Indian Edition", "Anniversary Edition"])
        full_title = f"{title} — {author} ({edition})"
        price = random.randint(199, 999)
        yield {
            "category": "Books",
            "subcategory": "Non-fiction",
            "brand": author,
            "title": full_title,
            "description": f"{edition} of '{title}' by {author}.",
            "price": float(price),
            "rating": round(random.uniform(4.0, 4.9), 1),
            "rating_count": random.randint(500, 80000),
            "tags": ["book", author.lower().replace(" ", "-"), "non-fiction"],
            "attributes": {"format": edition, "author": author},
            "stock": random.randint(0, 500),
        }


def _kitchen(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(KITCHEN_BRANDS)
        kind = random.choice(KITCHEN_TYPES)
        title = f"{brand} {kind}"
        base = {"Air Fryer": 9000, "Mixer Grinder": 4000, "Induction Cooktop": 3000, "Pressure Cooker": 2200, "Electric Kettle": 1500, "Microwave Oven": 11000, "Toaster": 1800, "Coffee Maker": 4500, "Food Processor": 6500, "Sandwich Maker": 2500}[kind]
        price = int(base + random.randint(-700, 7000))
        yield {
            "category": "Kitchen",
            "subcategory": "Appliances",
            "brand": brand,
            "title": title,
            "description": f"{kind} by {brand}. Durable build, energy-efficient.",
            "price": float(max(price, 499)),
            "rating": round(random.uniform(3.7, 4.7), 1),
            "rating_count": random.randint(150, 25000),
            "tags": ["kitchen", brand.lower(), kind.lower()],
            "attributes": {"type": kind},
            "stock": random.randint(0, 200),
        }


def _furniture(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(FURNITURE_BRANDS)
        kind = random.choice(FURNITURE_TYPES)
        color = random.choice(["Oak", "Walnut", "White", "Black", "Grey", "Honey"])
        title = f"{brand} {kind} ({color})"
        base = {"Queen Bed Frame": 18000, "King Size Bed": 26000, "Study Desk": 8000, "Office Chair": 11000, "3-Seater Sofa": 32000, "Recliner": 22000, "Wardrobe": 24000, "Bookshelf": 6000, "Dining Table": 18000, "Mattress (Queen)": 15000}[kind]
        price = int(base + random.randint(-3000, 18000))
        yield {
            "category": "Furniture",
            "subcategory": "Home",
            "brand": brand,
            "title": title,
            "description": f"{kind} in {color.lower()} finish by {brand}. Sturdy, easy-assembly.",
            "price": float(price),
            "rating": round(random.uniform(3.6, 4.7), 1),
            "rating_count": random.randint(40, 4000),
            "tags": ["furniture", brand.lower(), kind.lower(), color.lower()],
            "attributes": {"color": color},
            "stock": random.randint(0, 50),
        }


def _eyewear(n: int) -> Iterable[dict]:
    for _ in range(n):
        brand = random.choice(EYEWEAR_BRANDS)
        kind = random.choice(EYEWEAR_KIND)
        shape = random.choice(EYEWEAR_SHAPE)
        material = random.choice(EYEWEAR_MATERIAL)
        color = random.choice(EYEWEAR_COLOR)
        is_sun = "Sunglasses" in kind or "Aviator" in kind or "Wayfarer" in kind
        title = f"{brand} {shape} {kind} — {material} ({color})"
        base = {"Ray-Ban": 6500, "Oakley": 7500, "Tom Ford": 18000, "Persol": 14000,
                "Carrera": 5500, "Vogue Eyewear": 4500, "Fossil": 4200,
                "Vincent Chase": 1500, "Lenskart": 1200, "John Jacobs": 3500}.get(brand, 3500)
        price = base + random.randint(-500, 6000)
        desc_bits = [
            f"{shape.lower()} {kind.lower()} from {brand}",
            f"{material.lower()} frame in {color.lower()}",
        ]
        if is_sun:
            desc_bits.append("polarised UV400 lenses")
        else:
            desc_bits.append("anti-glare and blue-light filtering lenses")
        desc_bits.append("suits square, oval and oblong face shapes" if shape in ("Round", "Aviator", "Oversized")
                         else "great for round and heart face shapes")
        yield {
            "category": "Eyewear",
            "subcategory": "Sunglasses" if is_sun else "Eyeglasses",
            "brand": brand,
            "title": title,
            "description": ". ".join(desc_bits) + ".",
            "price": float(max(price, 599)),
            "rating": round(random.uniform(3.8, 4.7), 1),
            "rating_count": random.randint(80, 8000),
            "tags": [
                "eyewear",
                kind.lower().replace(" ", "-"),
                shape.lower(),
                material.lower(),
                color.lower(),
                brand.lower().replace(" ", "-"),
                "sunglasses" if is_sun else "eyeglasses",
            ],
            "attributes": {
                "shape": shape,
                "material": material,
                "color": color,
                "lens": "polarised" if is_sun else "anti-glare",
            },
            "stock": random.randint(0, 200),
        }


CATEGORIES_PLAN = [
    ("Laptops", 240, _laptops),
    ("Mobiles", 260, _mobiles),
    ("Audio", 200, _audio),
    ("Monitors", 120, _monitors),
    ("Accessories", 240, _accessories),
    ("Footwear", 240, _footwear),
    ("Clothing", 300, _clothing),
    ("Beauty", 180, _beauty),
    ("Books", 180, _books),
    ("Kitchen", 160, _kitchen),
    ("Furniture", 80, _furniture),
    ("Eyewear", 160, _eyewear),
]


def generate_products() -> list[dict]:
    products: list[dict] = []
    used_slugs: set[str] = set()
    for cat, n, fn in CATEGORIES_PLAN:
        for raw in fn(n):
            # Unique slug — append numeric suffix on collisions
            base_slug = _slug(raw["brand"], raw["title"])
            slug = base_slug
            i = 1
            while slug in used_slugs:
                i += 1
                slug = f"{base_slug}-{i}"
            used_slugs.add(slug)
            raw["slug"] = slug
            raw["image_url"] = _img(cat, raw.get("subcategory"))
            raw["images"] = [raw["image_url"]]
            raw["currency"] = "INR"
            products.append(raw)
    return products


if __name__ == "__main__":
    items = generate_products()
    by_cat: dict[str, int] = {}
    for p in items:
        by_cat[p["category"]] = by_cat.get(p["category"], 0) + 1
    print(f"Generated {len(items)} products:")
    for c, n in sorted(by_cat.items()):
        print(f"  {c:12s} {n}")
