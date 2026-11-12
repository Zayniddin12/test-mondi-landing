# Restoran menyusi. Narxlar so'mda; buyurtma summasi shu yerdan hisoblanadi,
# mijoz yuborgan narxga ishonilmaydi.
CATEGORIES = [
    {"id": "coffee", "title": "Qahva"},
    {"id": "food", "title": "Taomlar"},
    {"id": "dessert", "title": "Shirinliklar"},
    {"id": "drinks", "title": "Ichimliklar"},
]

ITEMS = [
    {"id": "espresso", "category": "coffee", "name": "Espresso", "desc": "Kuchli, quyuq, 30 ml", "price": 18000, "emoji": "☕"},
    {"id": "cappuccino", "category": "coffee", "name": "Kapuchino", "desc": "Espresso va ko'pikli sut", "price": 25000, "emoji": "☕"},
    {"id": "latte", "category": "coffee", "name": "Latte", "desc": "Yumshoq sutli qahva", "price": 27000, "emoji": "🥛"},
    {"id": "raf", "category": "coffee", "name": "Raf qahva", "desc": "Qaymoq va vanil bilan", "price": 32000, "emoji": "☕"},
    {"id": "caesar", "category": "food", "name": "Sezar salati", "desc": "Tovuq, parmezan, kruton", "price": 48000, "emoji": "🥗"},
    {"id": "club", "category": "food", "name": "Klub sendvich", "desc": "Tovuq, bekon, pomidor", "price": 52000, "emoji": "🥪"},
    {"id": "pasta", "category": "food", "name": "Karbonara", "desc": "Spagetti, bekon, qaymoqli sous", "price": 58000, "emoji": "🍝"},
    {"id": "burger", "category": "food", "name": "Mondi burger", "desc": "Mol go'shti, cheddar, fri", "price": 62000, "emoji": "🍔"},
    {"id": "cheesecake", "category": "dessert", "name": "Cheesecake", "desc": "Klassik Nyu-York", "price": 35000, "emoji": "🍰"},
    {"id": "tiramisu", "category": "dessert", "name": "Tiramisu", "desc": "Mascarpone va qahva", "price": 38000, "emoji": "🍮"},
    {"id": "croissant", "category": "dessert", "name": "Kruassan", "desc": "Sariyog'li, issiq", "price": 22000, "emoji": "🥐"},
    {"id": "lemonade", "category": "drinks", "name": "Limonad", "desc": "Yalpiz va limon", "price": 24000, "emoji": "🍋"},
    {"id": "tea", "category": "drinks", "name": "Choy (choynak)", "desc": "Qora yoki yashil", "price": 15000, "emoji": "🍵"},
    {"id": "water", "category": "drinks", "name": "Suv 0.5 l", "desc": "Gazsiz", "price": 6000, "emoji": "💧"},
]

BY_ID = {i["id"]: i for i in ITEMS}
