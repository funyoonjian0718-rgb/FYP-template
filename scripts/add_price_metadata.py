import json
from pathlib import Path

PRICE_MAP = {
    "Nasi Lemak": 6.0,
    "Roti Canai": 1.8,
    "Char Kuey Teow": 7.5,
    "Teh Tarik": 2.2,
    "Laksa (Curry)": 7.0,
    "Mee Goreng": 6.8,
    "Nasi Goreng": 6.5,
    "Hainanese Chicken Rice": 7.5,
    "Satay": 6.0,
    "Rendang": 8.0,
    "Kuih-Muih (Assorted)": 3.0,
    "Cendol": 4.0,
    "Nasi Putih": 0.6,
    "Mee": 0.8,
    "Kangkung (Water Spinach)": 2.5,
    "Sambal Belacan": 0.5,
    "Ayam Goreng (Fried Chicken)": 5.0,
    "Ikan Bakar (Grilled Fish)": 8.0,
    "Telur (Egg)": 0.8,
    "Tahu (Tofu)": 2.0,
    "Tempeh": 2.5,
    "Pisang (Banana)": 1.2,
    "Betik (Papaya)": 2.5,
    "Jambu (Guava)": 2.0,
    "Tembikai (Watermelon)": 1.8,
    "Mangga (Mango)": 3.5,
    "Durian": 6.0,
    "Air Kosong (Water)": 0.2,
    "Teh O (Tea without milk)": 1.2,
    "Kopi O (Coffee without milk)": 1.5,
    "Susu Rendah Lemak (Low-fat Milk)": 3.0,
    "Yogurt (Plain)": 4.0,
    "Santan (Coconut Milk)": 0.8,
    "Ubi Keledek (Sweet Potato)": 1.0,
    "Sagu": 0.7,
    "Bihun (Rice Vermicelli)": 0.9,
    "Kuey Teow (Flat Rice Noodles)": 0.9,
    "Satay Sauce (Kuah Kacang)": 1.0,
    "Sambal Sauce": 0.3,
    "Nasi Tomato (Tomato Rice)": 5.0,
    "Nasi Dagang": 7.0,
    "Keropok Lekor": 3.5,
    "Popcorn": 1.5,
    "Kacang (Peanuts)": 2.0,
    "Epal (Apple)": 3.0,
    "Limau (Orange)": 2.5,
}

BASE_DIR = Path(__file__).resolve().parents[1]
FOODS_PATH = BASE_DIR / "data" / "foods.json"


def main() -> None:
    with FOODS_PATH.open("r", encoding="utf-8") as f:
        foods = json.load(f)

    missing = []
    for item in foods:
        name = item.get("name")
        if name in PRICE_MAP:
            item["price_myr"] = PRICE_MAP[name]
        else:
            missing.append(name)

    with FOODS_PATH.open("w", encoding="utf-8") as f:
        json.dump(foods, f, ensure_ascii=False, indent=2)

    print(f"Updated {len(foods)} foods with price_myr")
    if missing:
        print("Missing prices for:")
        for name in missing:
            print(f" - {name}")


if __name__ == "__main__":
    main()
