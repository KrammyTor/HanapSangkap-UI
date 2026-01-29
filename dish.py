import tkinter as tk
from PIL import Image, ImageTk
import os

ACCENT_COLOR = "#74B3CE"
BAR_COLOR = "#0D6791"
CARD_BG = "#F4F7FA"
CARD_SHADOW = "#D0D5DA"
TEXT_COLOR = "#333"

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 200

# -------------------- DISH DATA --------------------
DISH_DETAILS = {

    # ===================== LUZON =====================
    "Pinakbet Ilocano": {
        "region": "Luzon",
        "description": "Simmered vegetables with bagoong, Ilocos style.",
        "ingredients": ["Ampalaya", "Sitaw", "Eggplant", "Pumpkin", "Onion", "Garlic", "Bagoong"],
        "steps": [
            "Boil water with bagoong.",
            "Add ampalaya, sitaw, eggplant, pumpkin.",
            "Add onion and garlic.",
            "Simmer 10–15 mins until tender."
        ],
        "image": "dishes_pics/pinakbet_ilocano.jpg"
    },

    "Pinakbet Tagalog": {
        "region": "Luzon",
        "description": "Tagalog-style pinakbet sautéed then stewed.",
        "ingredients": [
            "Lechon kawali", "Knorr Shrimp Cube", "Sitaw", "Kalabasa",
            "Okra", "Eggplant", "Ampalaya", "Tomato", "Onion", "Garlic",
            "Bagoong alamang", "Water", "Cooking oil", "Black pepper"
        ],
        "steps": [
            "Saute onion, garlic, ginger. Add half lechon kawali.",
            "Boil water, add Knorr cube, simmer 20 mins.",
            "Add tomato and bagoong, cook 3 mins.",
            "Add kalabasa, sitaw, okra, ampalaya, eggplant. Cook 5 mins.",
            "Add remaining lechon kawali, season, serve."
        ],
        "image": "dishes_pics/pinakbet_tagalog.jpg"
    },

    "Ginisang Ampalaya w/ Shrimp at Itlog": {
        "region": "Luzon",
        "description": "Sautéed bitter melon with egg and shrimp.",
        "ingredients": ["Ampalaya", "Tomato", "Onion", "Garlic", "Egg", "Shrimp", "Salt", "Pepper", "Garlic powder", "Oil"],
        "steps": [
            "Season shrimp, set aside. Beat eggs.",
            "Pan-fry shrimp, remove. Saute onion, garlic, tomato.",
            "Add ampalaya, cook 3 mins.",
            "Add egg, stir until cooked, add shrimp, season, serve."
        ],
        "image": "dishes_pics/ginisang_ampalaya_itlog.jpg"
    },

    "Ginisang Ampalaya": {
        "region": "Luzon",
        "description": "Sautéed bitter melon dish with tomatoes and onion.",
        "ingredients": [
            "Ampalaya",
            "Tomato",
            "Garlic",
            "Onion",
            "Salt",
            "Cooking oil"
        ],
        "steps": [
            "Salt-soak sliced ampalaya for 10 minutes and rinse.",
            "Sauté garlic and onion until soft.",
            "Add tomato and cook for 2 minutes.",
            "Add ampalaya and stir-fry for 5 minutes."
        ],
        "image": "dishes_pics/ginisang_ampalaya.jpg"
    },

    "Kare-Kare": {
        "region": "Luzon",
        "description": "Oxtail stew with peanut sauce and vegetables.",
        "ingredients": ["Oxtail", "Banana flower", "Pechay", "String beans", "Eggplant", "Ground peanuts", "Peanut butter", "Shrimp paste", "Water", "Annatto water", "Toasted ground rice", "Garlic", "Onion"],
        "steps": [
            "Boil oxtail with onion 2.5–3 hrs.",
            "Add peanuts, peanut butter, annatto water, simmer.",
            "Add toasted rice, simmer.",
            "Saute vegetables, add to pot, season, serve."
        ],
        "image": "dishes_pics/kare_kare.jpg"
    },

    "Bulanglang Batangas": {
        "region": "Luzon",
        "description": "Clear vegetable soup from Batangas.",
        "ingredients": [
            "Pumpkin",
            "Sayote",
            "Tomato",
            "Garlic",
            "Onion",
            "Water"
        ],
        "steps": [
            "Boil water with garlic and onion.",
            "Add tomatoes and simmer for 2 minutes.",
            "Add pumpkin and sayote.",
            "Simmer until vegetables are tender."
        ],
        "image": "dishes_pics/bulanglang_batangas.jpg"
    },

    "Bulanglang na Gulay": {
        "region": "Luzon",
        "description": "Batangas-style clear vegetable soup.",
        "ingredients": ["Malunggay", "Spinach", "Knorr Fish Cube", "Eggplant", "Okra", "Patola", "Papaya", "Kalabasa", "Tomato", "Onion", "Ginger", "Garlic", "Water", "Salt", "Pepper"],
        "steps": [
            "Boil water, add garlic, ginger, onion.",
            "Add tomato, papaya, kalabasa, cook 3–4 mins.",
            "Add eggplant, okra, patola, cook 3–5 mins.",
            "Add Knorr cube, malunggay, spinach, season, serve."
        ],
        "image": "dishes_pics/bulanglang_batangas.jpg"
    },

    "Ginataang Gulay Bicol": {
        "region": "Luzon",
        "description": "Vegetables cooked in coconut milk, Bicol style.",
        "ingredients": [
            "Sitaw",
            "Eggplant",
            "Pumpkin",
            "Garlic",
            "Onion",
            "Coconut milk"
        ],
        "steps": [
            "Sauté onion and garlic.",
            "Add vegetables.",
            "Pour coconut milk.",
            "Simmer until tender."
        ],
        "image": "dishes_pics/ginataang_gulay_bicol.jpg"
    },

    "Ginisang Sayote": {
        "region": "Luzon",
        "description": "Stir-fried sayote with vegetables.",
        "ingredients": [
            "Sayote",
            "Carrot",
            "Cabbage",
            "Garlic",
            "Onion"
        ],
        "steps": [
            "Sauté garlic and onion.",
            "Add sayote and carrot.",
            "Add cabbage.",
            "Cook until tender."
        ],
        "image": "dishes_pics/ginisang_sayote.jpg"
    },

    "Ginisang Repolyo at Carrot": {
        "region": "Luzon",
        "description": "Stir-fried cabbage and carrots with eggs.",
        "ingredients": ["Cabbage", "Carrot", "Eggs", "Onion", "Garlic", "Green onions", "Soy sauce", "Oyster sauce", "Salt", "Pepper", "Sugar", "Oil"],
        "steps": [
            "Salt cabbage, rinse. Beat eggs.",
            "Cook eggs, remove. Saute onion, garlic, carrots.",
            "Add cabbage, cook 2 mins.",
            "Add sauces, eggs, green onions, season, serve."
        ],
        "image": "dishes_pics/ginisang_repolyo_carrot.jpg"
    },

    "Ginisang Sitaw at Kalabasa": {
        "region": "Luzon",
        "description": "Sautéed string beans and pumpkin with dried fish.",
        "ingredients": ["Pumpkin", "String beans", "Salted dried fish", "Onion", "Garlic", "Water", "Fish sauce", "Oil", "Black pepper"],
        "steps": [
            "Heat oil, sauté garlic and onion.",
            "Add dried fish, stir.",
            "Add pumpkin, stir-fry 1 min.",
            "Add water, cover, cook 5–6 mins.",
            "Add string beans, fish sauce, pepper, cook 1–3 mins, serve."
        ],
        "image": "dishes_pics/ginisang_sitaw_kalabasa.jpg"
    },

    "Tortang Talong": {
        "region": "Luzon",
        "description": "Eggplant omelette fried in oil.",
        "ingredients": ["Chinese eggplant", "Eggs", "Salt", "Cooking oil"],
        "steps": [
            "Grill eggplant, peel skin.",
            "Beat eggs with salt.",
            "Flatten eggplant, dip in egg, fry both sides 3–4 mins, serve."
        ],
        "image": "dishes_pics/tortang_talong.jpg"
    },

    # ===================== VISAYAS =====================
    "Utan Bisaya": {
        "region": "Visayas",
        "description": "Mixed boiled vegetables with fish, Batangas-style.",
        "ingredients": ["Chinese eggplant", "Okra", "Ginger", "Tomato", "Green onions", "Spinach or alugbati", "Pumpkin", "Malunggay leaves", "Long green pepper", "Fish fillet", "String beans", "Loofah (patola)", "Salt", "Water"],
        "steps": [
            "Boil water, add ginger and pumpkin for 8 mins.",
            "Add string beans, scallions, okra, and tomato, re-boil.",
            "Add long green pepper and eggplant.",
            "Add fish, cover, cook 10 mins.",
            "Add patola, malunggay, and spinach. Cook 3–5 mins, season, serve."
        ],
        "image": "dishes_pics/utan_bisaya.jpg"
    },

    "Laswa Ilonggo": {
        "region": "Visayas",
        "description": "Light broth mixed vegetable dish.",
        "ingredients": [
            "Pumpkin",
            "Eggplant",
            "Okra",
            "Sitaw",
            "Moringa leaves"
        ],
        "steps": [
            "Boil water with onion and tomato.",
            "Add vegetables.",
            "Simmer until tender."
        ],
        "image": "dishes_pics/laswa_ilonggo.jpg"
    },

    "Law-Uy": {
        "region": "Visayas",
        "description": "Visayan vegetable stew with pumpkin, eggplant, and leafy greens.",
        "ingredients": ["Pumpkin", "Eggplant", "Okra", "Long beans", "Patola", "Leafy greens (malunggay, alugbati, spinach, saluyot)", "Tomato", "Red onion", "Ginger", "Lemongrass", "Fish sauce", "Salt", "Bouillon cubes", "Optional dried fish, shrimp, or mussels"],
        "steps": [
            "Boil water with lemongrass, ginger, onion, and optional dried fish 3–5 mins.",
            "Add pumpkin, eggplant, okra, patola, simmer 5–7 mins.",
            "Add leafy greens and tomato, cook 1–2 mins.",
            "Season with fish sauce, salt, bouillon. Serve hot."
        ],
        "image": "dishes_pics/law_uy.jpg"
    },


    "Ginisang Gulay Visayas": {
        "region": "Visayas",
        "description": "Visayan sautéed vegetables.",
        "ingredients": [
            "Cabbage",
            "Carrot",
            "Sitaw",
            "Garlic",
            "Onion"
        ],
        "steps": [
            "Sauté garlic and onion.",
            "Add vegetables.",
            "Cook until tender."
        ],
        "image": "dishes_pics/ginisang_gulay_visayas.jpg"
    },

    "Ampalaya Soup": {
        "region": "Visayas",
        "description": "Clear bitter melon soup.",
        "ingredients": [
            "Ampalaya",
            "Eggplant",
            "Tomato",
            "Garlic",
            "Onion"
        ],
        "steps": [
            "Boil water with aromatics.",
            "Add vegetables.",
            "Simmer until tender."
        ],
        "image": "dishes_pics/ampalaya_soup.jpg"
    },

    "Inabraw nga Gulay": {
        "region": "Visayas",
        "description": "Shrimp and vegetable stew with malunggay leaves.",
        "ingredients": ["Shrimps", "Eggplants", "Ampalaya", "Okra", "Tomato", "Sitaw", "Garlic", "Ginger", "Onion", "Vegetable broth or water", "Bagoong guisado", "Salt", "Pepper", "Malunggay leaves"],
        "steps": [
            "Layer shrimps, eggplants, ampalaya, okra, tomatoes, sitaw, garlic, onion, ginger in pot.",
            "Pour broth, season with bagoong, salt, pepper. Do not mix.",
            "Cook in Instant Pot 8 mins on high pressure, quick release.",
            "Add malunggay, stir, cover, keep warm 5 mins, serve."
        ],
        "image": "dishes_pics/inabraw_nga_gulay.jpg"
    },

    "Ensaladang Talong Bisaya": {
        "region": "Visayas",
        "description": "Roasted eggplant salad with vinegar dressing.",
        "ingredients": ["Eggplants", "Tomato", "Red onion", "Vinegar", "Salt", "Sugar", "Black pepper", "Bird’s eye chilies", "Fish sauce or bagoong", "Calamansi juice"],
        "steps": [
            "Roast eggplants until soft, peel and mash.",
            "Mix with tomatoes, onion, chilies.",
            "Add vinegar, sugar, salt, pepper, fish sauce, calamansi. Mix and serve."
        ],
        "image": "dishes_pics/ensaladang_talong_bisaya.jpg"
    },

    "Sitaw at Kalabasa": {
        "region": "Visayas",
        "description": "Boiled sitaw and pumpkin dish.",
        "steps": [
            "Boil water with onion and tomato.",
            "Add sliced pumpkin and cook for 5 minutes.",
            "Add string beans and simmer until tender, about 5 more minutes."
        ],
        "image": "dishes_pics/sitaw_kalabasa.jpg"
    },

    "Pinakbet Visayas Style": {
        "region": "Visayas",
        "description": "Vegetable sauté with shrimp paste and pork cubes.",
        "ingredients": ["Onion", "Garlic", "Tomato", "Pumpkin", "Eggplants", "String beans", "Okra", "Pork", "Shrimp paste", "Cooking oil", "Salt"],
        "steps": [
            "Sauté onion, garlic, tomato.",
            "Add pork, cook until browned.",
            "Stir in shrimp paste, simmer 2 mins.",
            "Add pumpkin, cook half-done.",
            "Add remaining vegetables, simmer until tender. Serve."
        ],
        "image": "dishes_pics/pinakbet_visayas.jpg"
    },

    "KBL-Style Vegetable Stew": {
        "region": "Visayas",
        "description": "Pork hocks stew with jackfruit, pigeon peas, and sweet potato leaves.",
        "ingredients": ["Pork hocks", "Unripe jackfruit", "Pigeon peas", "Potato", "Sinigang mix or batuan", "Lemongrass", "Beef or pork cube", "Water", "Salt", "Pepper"],
        "steps": [
            "Boil pork hocks in water, discard first batch.",
            "Add lemongrass, beef cube, simmer 40–45 mins.",
            "Add pigeon peas, cook 20–25 mins.",
            "Add sinigang mix, jackfruit, cook 10 mins.",
            "Add sweet potato leaves, cover, turn off heat, serve."
        ],
        "image": "dishes_pics/kbl_vegetable_stew.jpg"
    },

    "Laswa nga Gulay": {
        "region": "Visayas",
        "description": "Mixed vegetable soup with shrimp and leafy greens.",
        "ingredients": ["Shrimp", "Chinese eggplant", "Pumpkin", "String beans", "Saluyot leaves", "Alugbati", "Amaranth leaves (kulitis)", "Okra", "Tomato", "Onion", "Bagoong alamang", "Water", "Salt", "Pepper"],
        "steps": [
            "Boil water with onion and tomato 5 mins.",
            "Add pumpkin and shrimp paste, boil 5 mins.",
            "Add eggplant, string beans, okra, cook 4–5 mins.",
            "Add shrimp, cover 1 min.",
            "Add leafy greens, stir, season, serve."
        ],
        "image": "dishes_pics/laswa_nga_gulay.jpg"
    },

    # ===================== MINDANAO =====================
    "Tinuto": {
        "region": "Mindanao",
        "description": "Vegetable stew cooked in coconut milk.",
        "ingredients": [
            "Garlic, onion",
            "Eggplant",
            "Pumpkin",
            "String beans",
            "Coconut milk"
        ],
        "steps": [
            "Sauté garlic and onion until fragrant.",
            "Add eggplant, pumpkin, string beans.",
            "Pour coconut milk and bring to boil.",
            "Simmer 15 minutes until vegetables are soft."
        ],
        "image": "dishes_pics/tinuto.jpg"
    },

    "Ginisang Gulay Mindanao": {
        "region": "Mindanao",
        "description": "A traditional Mindanao-style vegetable stir-fry using local greens and a savory sauce.",
        "ingredients": [
            "Kangkong (water spinach) or other leafy greens",
            "Okra",
            "Eggplant",
            "Tomato",
            "Onion",
            "Garlic",
            "Salt and pepper",
        ],
        "steps": [
            "Heat oil in a pan over medium heat.",
            "Sauté garlic and onion until aromatic.",
            "Add tomato and cook until it becomes soft.",
            "Add eggplant and okra; stir-fry for 3–5 minutes.",
            "Add leafy greens and cook until wilted.",
            "Season with salt and pepper to taste.",
            "Serve immediately while hot."
        ],
        "image": "dishes_pics/ginisang_gulay_mindanao.jpg"
    },

    "Ginataang Sitaw": {
        "region": "Mindanao",
        "description": "String beans cooked in coconut milk with a creamy and slightly sweet flavor, a classic Filipino dish.",
        "ingredients": [
            "Sitaw (string beans)",
            "Coconut milk (gata)",
            "Tomato",
            "Onion",
            "Garlic",
            "Salt and pepper",
        ],
        "steps": [
            "Heat oil in a pan and sauté garlic, onion, and tomato until fragrant.",
            "Add sitaw and stir-fry for 2–3 minutes.",
            "Pour in coconut milk and bring to a gentle simmer.",
            "Season with salt and pepper.",
            "Cook until sitaw is tender and the sauce thickens slightly, about 10–15 minutes.",
            "Serve hot with rice."
        ],
        "image": "dishes_pics/ginataang_sitaw.jpg"
    },

    "Bulanglang Variant": {
        "region": "Mindanao",
        "description": "Boiled mixed vegetable dish with papaya and pumpkin.",
        "ingredients": ["Green papaya", "Pumpkin", "Loofah (patola)", "Lemongrass (optional)", "Tomato", "Okra", "Malunggay leaves", "Garlic", "Ginger", "Salt", "Rice washing water"],
        "steps": [
            "Boil rice washing water with garlic, ginger, lemongrass 5–7 mins.",
            "Remove lemongrass, add papaya and pumpkin, boil 6 mins.",
            "Add tomatoes, okra, loofah, cook 3–4 mins.",
            "Add malunggay and salt, stir, turn off heat, serve."
        ],
        "image": "dishes_pics/bulanglang_variant.jpg"
    },

    "Ampalaya with Gulay": {
        "region": "Mindanao",
        "description": "A healthy stir-fry of bitter melon and assorted vegetables, lightly seasoned for a fresh taste.",
        "ingredients": [
            "Ampalaya (bitter melon)",
            "Carrot",
            "Sitaw (string beans)",
            "Tomato",
            "Onion",
            "Garlic",
            "Salt and pepper",
        ],
        "steps": [
            "Heat oil in a pan over medium heat.",
            "Sauté garlic and onion until fragrant.",
            "Add tomato and cook until soft.",
            "Add ampalaya, carrot, and sitaw; stir-fry for 5–7 minutes.",
            "Season with salt and pepper.",
            "Cook until vegetables are tender but still crisp.",
            "Serve hot."
        ],
        "image": "dishes_pics/ampalaya_with_gulay.jpg"
    },

    "Sayote Tomato Stew": {
        "region": "Mindanao",
        "description": "Simple chayote stew with onion and garlic.",
        "ingredients": ["Chayotes", "Olive oil", "Onion", "Garlic", "Tomato", "Water", "Salt"],
        "steps": [
            "Boil sliced chayotes in salted water 5 mins, drain.",
            "Sauté onion in oil 5 mins, add garlic 1–2 mins.",
            "Add chayote, tomatoes, water, simmer 10 mins, serve."
        ],
        "image": "dishes_pics/sayote_tomato_stew.jpg"
    },

    "Mixed Utan": {
        "region": "Mindanao",
        "description": "Mixed boiled vegetables with leafy greens and optional fish.",
        "ingredients": ["Pumpkin", "Eggplant", "Okra", "String beans", "Patola", "Gabi (taro)", "Ampalaya", "Alugbati", "Malunggay", "Kangkong", "Ginger", "Onion", "Tomato", "Fish sauce or dried fish", "Water"],
        "steps": [
            "Boil water with ginger and onion.",
            "Add long-cooking vegetables (pumpkin, gabi, eggplant, patola), simmer 5–10 mins.",
            "Add quicker-cooking vegetables (okra, string beans, tomatoes) and fish if using, simmer 5–10 mins.",
            "Add leafy greens, cook 1–2 mins, season, serve hot."
        ],
        "image": "dishes_pics/mixed_utan.jpg"
    },

    "Pyanggang-Inspired Vegetable Stew": {
        "region": "Mindanao",
        "description": "Chicken or vegetable stew with burnt coconut and spices.",
        "ingredients": ["Chicken or protein", "Burnt coconut paste", "Turmeric", "Ginger", "Lemongrass", "Garlic", "Red onion", "Red chilies", "Coconut milk", "Water", "Vegetable oil", "Knorr liquid seasoning or salt"],
        "steps": [
            "Grill coconut, make spice paste with turmeric, ginger, lemongrass, garlic, onion, chilies.",
            "Marinate chicken with paste 10 mins.",
            "Sauté garlic, onion, add chicken and paste.",
            "Add coconut milk, water, seasoning, simmer 20–30 mins.",
            "Optional: Grill chicken 10–15 mins, baste with sauce."
        ],
        "image": "dishes_pics/pyanggang_vegetable_stew.jpg"
    },

    "Vegetable Kulma-Style Simmer": {
        "region": "Mindanao",
        "description": "Coconut-based vegetable curry with spices.",
        "ingredients": ["Potato", "Carrot", "Cauliflower", "Green beans", "Peas", "Bell pepper", "Onion", "Garlic", "Ginger", "Tomato puree", "Coconut milk", "Cashew paste or yogurt", "Spices (turmeric, chili, coriander, garam masala, cumin, cardamom, cinnamon, cloves)", "Mustard seeds, curry leaves, fennel seeds (optional)", "Oil or ghee", "Fresh coriander leaves", "Lemon juice"],
        "steps": [
            "Boil/steam vegetables 70–80% cooked, drain.",
            "Blend coconut, cashews, ginger, garlic, green chilies, spices into paste.",
            "Sauté aromatics in oil until golden, add tomato puree and spice powders.",
            "Add paste, coconut milk, cooked vegetables, simmer 10–15 mins.",
            "Finish with yogurt, lemon juice, coriander. Serve with rice or naan."
        ],
        "image": "dishes_pics/vegetable_kulma.jpg"
    },

    "Maranao Pinakbet Halal": {
        "region": "Mindanao",
        "description": "Halal-style pinakbet with fish or chicken.",
        "ingredients": ["Halal fish or chicken", "Shrimp or prawns (Halal)", "Ampalaya", "Eggplant", "Okra", "Zucchini or Pumpkin", "Long beans", "Tomato", "Onion", "Garlic", "Halal fish sauce or miso", "Ginger", "Turmeric", "Oil"],
        "steps": [
            "Sauté onion, garlic, ginger.",
            "Add Halal protein, cook until done.",
            "Add tomatoes, cook soft.",
            "Add vegetables in order of cooking time, add water or broth, simmer until tender.",
            "Season with Halal fish sauce or miso, serve with rice."
        ],
        "image": "dishes_pics/maranao_pinakbet.jpg"
    },

    "Davao Ginisang Ampalaya Spiced": {
        "region": "Mindanao",
        "description": "Sautéed ampalaya with eggs, tomatoes, and optional soy sauce.",
        "ingredients": ["Ampalaya", "Garlic", "Onion", "Tomato", "Eggs", "Cooking oil", "Water", "Salt", "Black pepper", "Soy sauce or fish sauce", "Optional sugar"],
        "steps": [
            "Soak sliced ampalaya in salted water 20–30 mins, drain.",
            "Sauté garlic and onion until fragrant.",
            "Add tomatoes, cook until soft.",
            "Add ampalaya, stir-fry 2–3 mins, add water, simmer 5 mins.",
            "Add beaten eggs, scramble until cooked.",
            "Season with soy sauce, salt, pepper, optional sugar, serve hot with rice."
        ],
        "image": "dishes_pics/davao_ginisang_ampalaya.jpg"
    },

    "Cagayan de Oro Kalabasa Sitaw Curry": {
        "region": "Mindanao",
        "description": "Coconut-based curry with pumpkin and string beans.",
        "ingredients": ["Cooking oil", "Garlic", "Onion", "Water", "Coconut milk", "Pumpkin", "Yard-long beans", "Shrimp paste (optional)", "Fish sauce", "Salt", "Black pepper", "Optional protein: pork, shrimp, chicken"],
        "steps": [
            "Sauté garlic and onion in oil.",
            "Add pork if using, cook until browned.",
            "Add coconut milk, simmer gently.",
            "Add pumpkin, cook 10–15 mins, add string beans 5–8 mins.",
            "Stir in shrimp paste, fish sauce, salt, pepper. Serve hot with rice."
        ],
        "image": "dishes_pics/cdo_kalabasa_sitaw_curry.jpg"
    },

    "Moro Carrot Potato Ampalaya": {
        "region": "Mindanao",
        "description": "Mixed vegetable sauté with ampalaya, carrots, potatoes, and optional protein.",
        "ingredients": ["Chicken or other protein", "Potato", "Carrot", "Ampalaya", "Garlic", "Onion", "Soy sauce", "Vinegar", "Black pepper", "Cooking oil", "Salt", "Optional sugar or oyster sauce"],
        "steps": [
            "Salt ampalaya, rinse after 10–15 mins.",
            "Parboil potatoes and carrots.",
            "Sauté garlic and onion until fragrant, add protein, cook until browned.",
            "Add ampalaya, potatoes, carrots, tomatoes, season, cook 5–7 mins.",
            "Adjust seasoning, serve hot with rice."
        ],
        "image": "dishes_pics/moro_carrot_potato_ampalaya.jpg"
    },
}

class DishScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        self._scroll_job = None

        # -------------------- TOP BAR --------------------
        top_bar = tk.Frame(self, bg=BAR_COLOR, height=60)
        top_bar.pack(fill="x", side="top")
        
        self.origin_label_top = tk.Label(
            top_bar, font=("Helvetica", 14, "italic"),
            fg="white", bg=BAR_COLOR
        )
        self.origin_label_top.pack(pady=15)

        # -------------------- BOTTOM BAR --------------------
        bottom_bar = tk.Frame(self, bg=BAR_COLOR, height=75)
        bottom_bar.pack(fill="x", side="bottom")

        button_center_frame = tk.Frame(bottom_bar, bg=BAR_COLOR)
        button_center_frame.pack(expand=True)

        self.back_card = tk.Frame(
            button_center_frame, bg=ACCENT_COLOR, width=140, height=45,
            highlightthickness=2, highlightbackground="#0A4F7A",
            relief="raised", bd=4, cursor="hand2"
        )
        self.back_card.pack(side="left", padx=15, pady=10)
        self.back_card.pack_propagate(False)

        self.back_label = tk.Label(
            self.back_card, text="BACK", font=("Arial", 11, "bold"),
            fg="white", bg=ACCENT_COLOR
        )
        self.back_label.pack(expand=True)

        self.scan_card = tk.Frame(
            button_center_frame, bg="#FF6B6B", width=160, height=45,
            highlightthickness=2, highlightbackground="#C94C4C",
            relief="raised", bd=4, cursor="hand2"
        )
        self.scan_card.pack(side="left", padx=15, pady=10)
        self.scan_card.pack_propagate(False)

        self.scan_label = tk.Label(
            self.scan_card, text="SCAN AGAIN", font=("Arial", 11, "bold"),
            fg="white", bg="#FF6B6B"
        )
        self.scan_label.pack(expand=True)

        # -------------------- MAIN CONTENT --------------------
        content_main = tk.Frame(self, bg="white")
        content_main.pack(expand=True, fill="both", padx=25, pady=10)

        # LEFT SIDE: Photo and Description
        left_card_outer = tk.Frame(content_main, bg=CARD_SHADOW, padx=2, pady=2)
        left_card_outer.pack(side="left", fill="y", padx=(0, 20))

        # FIXED: We keep pack_propagate(False) but set a specific height (e.g., 450)
        # to ensure the image stays exactly where it is.
        self.left_side = tk.Frame(left_card_outer, bg="white", width=360, height=460)
        self.left_side.pack(fill="both", expand=True)
        self.left_side.pack_propagate(False)

        # Image inside the card - FIXED size
        self.image_label = tk.Label(self.left_side, bg="white", width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
        self.image_label.pack(pady=(15, 5))

        # Title - Reduced pady to 2 to prevent pushing the description down
        self.title_label = tk.Label(
            self.left_side, font=("Arial", 20, "bold"),
            fg=BAR_COLOR, bg="white", wraplength=320, justify="center"
        )
        self.title_label.pack(pady=2)

        # Description - Anchor "n" and a tighter wraplength
        self.desc_label = tk.Label(
            self.left_side, font=("Helvetica", 12),
            fg=TEXT_COLOR, bg="white", wraplength=310, 
            justify="center", anchor="n"
        )
        self.desc_label.pack(fill="both", expand=True, pady=(2, 10), padx=10)

        # RIGHT SIDE: Recipe Card
        recipe_outer = tk.Frame(content_main, bg=CARD_SHADOW, padx=2, pady=2)
        recipe_outer.pack(side="left", expand=True, fill="both")

        recipe_inner = tk.Frame(recipe_outer, bg=CARD_BG)
        recipe_inner.pack(expand=True, fill="both")

        card_header = tk.Frame(recipe_inner, bg=CARD_BG)
        card_header.pack(fill="x", padx=20, pady=(15, 0))

        tk.Label(
            card_header, text="How to Cook", font=("Helvetica", 20, "bold"),
            fg=ACCENT_COLOR, bg=CARD_BG
        ).pack(side="left")

        scroll_nav_frame = tk.Frame(card_header, bg=CARD_BG)
        scroll_nav_frame.pack(side="right")

        self.up_canvas = tk.Canvas(scroll_nav_frame, width=55, height=55, bg=CARD_BG, highlightthickness=0)
        self.up_canvas.pack(side="left", padx=5)
        self._draw_scroll_button(self.up_canvas, "▲")
        
        self.down_canvas = tk.Canvas(scroll_nav_frame, width=55, height=55, bg=CARD_BG, highlightthickness=0)
        self.down_canvas.pack(side="left", padx=5)
        self._draw_scroll_button(self.down_canvas, "▼")

        recipe_body = tk.Frame(recipe_inner, bg=CARD_BG)
        recipe_body.pack(fill="both", expand=True, pady=10)

        self.canvas = tk.Canvas(recipe_body, bg=CARD_BG, highlightthickness=0)
        self.scroll_content = tk.Frame(self.canvas, bg=CARD_BG)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True, padx=20)

        # -------------------- BINDINGS --------------------
        self.up_canvas.bind("<Button-1>", lambda e: self.start_scroll(-1))
        self.up_canvas.bind("<ButtonRelease-1>", lambda e: self.stop_scroll())
        self.down_canvas.bind("<Button-1>", lambda e: self.start_scroll(1))
        self.down_canvas.bind("<ButtonRelease-1>", lambda e: self.stop_scroll())

        self.back_card.bind("<Button-1>", lambda e: self.go_back())
        self.back_label.bind("<Button-1>", lambda e: self.go_back())
        self.scan_card.bind("<Button-1>", lambda e: self.scan_again())
        self.scan_label.bind("<Button-1>", lambda e: self.scan_again())

    def _draw_scroll_button(self, canvas, symbol):
        w, h = 55, 55
        canvas.delete("all")
        canvas.create_oval(2, 2, w-2, h-2, fill=BAR_COLOR, outline=BAR_COLOR)
        canvas.create_text(w//2, h//2, text=symbol, fill="white", font=("Arial", 16, "bold"))

    def start_scroll(self, direction):
        if self._scroll_job: self.after_cancel(self._scroll_job)
        self.canvas.yview_scroll(direction, "units")
        self._scroll_job = self.after(50, lambda: self.start_scroll(direction))

    def stop_scroll(self):
        if self._scroll_job:
            self.after_cancel(self._scroll_job)
            self._scroll_job = None

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        dish_name = getattr(self.controller, "selected_dish", None)
        from dish import DISH_DETAILS 
        
        if not dish_name or dish_name not in DISH_DETAILS: return
        data = DISH_DETAILS[dish_name]

        self.title_label.config(text=dish_name)
        self.desc_label.config(text=data.get("description", ""))
        self.origin_label_top.config(text=f"Origin: {data.get('region', 'Unknown')}")

        if os.path.exists(data.get("image", "")):
            # Force resize to constant dimensions
            img = Image.open(data["image"]).resize((IMAGE_WIDTH, IMAGE_HEIGHT))
            imgtk = ImageTk.PhotoImage(img)
            self.image_label.config(image=imgtk)
            self.image_label.image = imgtk

        for widget in self.scroll_content.winfo_children(): 
            widget.destroy()

        # --- INGREDIENTS ---
        tk.Label(self.scroll_content, text="Ingredients:", font=("Helvetica", 14, "bold"),
                 fg=ACCENT_COLOR, bg=CARD_BG).pack(anchor="w", pady=(5, 5))
        
        ing_split_container = tk.Frame(self.scroll_content, bg=CARD_BG)
        ing_split_container.pack(fill="x", anchor="w")

        left_col = tk.Frame(ing_split_container, bg=CARD_BG)
        left_col.pack(side="left", anchor="n", expand=True, fill="both")
        
        right_col = tk.Frame(ing_split_container, bg=CARD_BG)
        right_col.pack(side="left", anchor="n", expand=True, fill="both")

        ingredients = data.get("ingredients", [])
        for i, ing in enumerate(ingredients):
            target_frame = left_col if i % 2 == 0 else right_col
            lbl = tk.Label(target_frame, text=f"• {ing}", font=("Helvetica", 12),
                           fg=TEXT_COLOR, bg=CARD_BG, justify="left", 
                           wraplength=130, anchor="nw")
            lbl.pack(fill="x", anchor="w", pady=2, padx=(0, 10))

        # --- STEPS ---
        tk.Label(self.scroll_content, text="Steps:", font=("Helvetica", 14, "bold"),
                 fg=ACCENT_COLOR, bg=CARD_BG).pack(anchor="w", pady=(15, 5))
        
        for i, step in enumerate(data.get("steps", []), 1):
            tk.Label(self.scroll_content, text=f"{i}. {step}", font=("Helvetica", 12),
                     fg=TEXT_COLOR, bg=CARD_BG, wraplength=330, justify="left").pack(anchor="w", pady=4)

        self.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)

    def go_back(self):
        from recipe import RecipeScreen
        self.controller.show_frame(RecipeScreen)

    def scan_again(self):
        for name, frame in self.controller.frames.items():
            if "ScanScreen" in str(name):
                if hasattr(frame, 'reset_screen'): frame.reset_screen()
                self.controller.show_frame(name)
                break