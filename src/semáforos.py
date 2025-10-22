import pandas as pd
from utils import add_traffic_lights, add_nova_from_ingredients, add_mixed_score

def main():
    colmap = {
        "fat_g": "grasas",
        "sat_g": "grasas_saturadas",
        "sugars_g": "azúcares",
        "salt_g": "sal",
        "sodium_g": "sodio"
        # "category": "categoria",  # opcional
        # "per": "por"              # opcional: "100g"/"100ml"
    }

    df = pd.read_csv('./data/mercadona_food.csv', index_col='id')
    df = add_traffic_lights(df, colmap=colmap, category_default="food")                # tl_*
    df = add_nova_from_ingredients(df)         # nova_label, nova_score
    df = add_mixed_score(df)                   # mixed_score, mixed_label
    df.to_csv('./data/mercadona_food_final.csv')  
    
    print(df[["ingredients","tl_fat","tl_sat","tl_sugars","tl_salt","nova_label","mixed_score","mixed_label"]])



if __name__ == "__main__":
    main()

