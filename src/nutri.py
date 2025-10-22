import utils
import pandas as pd

def main():
    df = pd.read_csv('./data/mercadona_food_no_nutri.csv', index_col='id')
    updated = utils.extract_nutrition_to_df(
        df,
        images_dir="./data/img",
        prompt_path="./prompts/nutri_prompt.md",
        model="gpt-4o",
        start_from_id=None,     # or e.g., 9000
        save_every=50,
        out_csv_path="./data/mercadona_food.csv",
    )



if __name__ == "__main__":
    main()

