I've got a Pandas dataframe with data from a Spanish supermarket (Mercadona).
```bash
df.info()
 <class 'pandas.core.frame.DataFrame'>
 Index: 3025 entries, 7026 to 11431
 Data columns (total 67 columns):
   # Column Non-Null Count Dtype
    --- ------ -------------- -----
     0 ean 3025 non-null int64
     1 status 0 non-null float64
     2 is_bulk 3025 non-null bool
     3 packaging 2774 non-null object
     4 published 3025 non-null bool
     5 share_url 3025 non-null object
     6 display_name 3025 non-null object
     7 is_variable_weight 3025 non-null bool
     8 details_brand 2479 non-null object
     9 details_origin 1303 non-null object
    10 details_counter_info 96 non-null object
    11 details_danger_mentions 0 non-null object
    12 details_alcohol_by_volume 173 non-null object
    13 details_mandatory_mentions 1321 non-null object
    14 details_production_variant 438 non-null object
    15 details_usage_instructions 1327 non-null object
    16 details_storage_instructions 2551 non-null object
    17 price_iva 2216 non-null float64
    18 price_is_new 3025 non-null bool
    19 price_is_pack 3025 non-null bool
    20 price_pack_size 488 non-null float64
    21 price_unit_name 887 non-null object
    22 price_unit_size 2986 non-null float64
    23 price_bulk_price 3025 non-null float64
    24 price_unit_price 3025 non-null float64
    25 price_approx_size 3025 non-null bool
    26 price_size_format 3025 non-null object
    27 price_total_units 887 non-null float64
    28 price_unit_selector 3025 non-null bool
    29 price_bunch_selector 3025 non-null bool
    30 price_drained_weight 181 non-null float64
    31 price_selling_method 3025 non-null int64
    32 price_reference_price 3025 non-null float64
    33 price_min_bunch_amount 3025 non-null float64
    34 price_reference_format 3025 non-null object
    35 allergens 2715 non-null object
    36 ingredients 2688 non-null object
    37 level_0_cat_id 3025 non-null int64
    38 level_0_cat_name 3025 non-null object
    39 level_0_cat_order 3025 non-null int64
    40 level_1_cat_id 3025 non-null int64
    41 level_1_cat_name 3025 non-null object
    42 level_1_cat_order 3025 non-null int64
    43 level_2_cat_id 3025 non-null int64
    44 level_2_cat_name 3025 non-null object
    45 level_2_cat_order 3025 non-null int64
    46 img_0_url 3025 non-null object
    47 img_0_perspective 3025 non-null Int64
    48 img_1_url 2923 non-null object
    49 img_1_perspective 2923 non-null Int64
    50 img_2_url 390 non-null object
    51 img_2_perspective 390 non-null Int64
    52 img_3_url 51 non-null object
    53 img_3_perspective 51 non-null Int64
    54 img_4_url 5 non-null object
    55 img_4_perspective 5 non-null Int64
    56 img_5_url 1 non-null object
    57 img_5_perspective 1 non-null Int64
    58 img_6_url 0 non-null object
    59 img_6_perspective 0 non-null Int64
    60 img_0_nutri_info_file 2 non-null string
    61 img_1_nutri_info_file 2870 non-null string
    62 img_2_nutri_info_file 192 non-null string
    63 img_3_nutri_info_file 41 non-null string
    64 img_4_nutri_info_file 4 non-null string
    65 img_5_nutri_info_file 0 non-null string
    66 img_6_nutri_info_file 0 non-null string
    dtypes: Int64(7), bool(8), float64(10), int64(8), object(27), string(7)
    memory usage: 1.4+ MB
```

I also have a folder (`../data/img/`) full of products' images with filename in the format: `{product_ID}_img_{x}.jpg`

- `product_ID` is an integer number.
- `x` is also an integer, from 0 to n-1 (n = number of images for that product)

I established the, a priori, useful images to use. They are stored in the following columns:
```
img_0_nutri_info_file
img_1_nutri_info_file
img_2_nutri_info_file
img_3_nutri_info_file
img_4_nutri_info_file
img_5_nutri_info_file
img_6_nutri_info_file
```

The vast majority of useful files are stored in the 'img_1_nutri_info_file' column, but we'll check all 7 columns for strings containing a filename.

I need a Python function with a single argument (the dataframe), that will iterate over its rows and:
- Get the list of image files stored in columns 'img_{x}_nutri_info_file'.
- Send those images (corresponding to one single product) to ChatGPT, using the openai library and the prompt I'm uploading. I do have an OpenAI API key. Tell me how to store it inside a suitable secrets file, and where to place it.
- Get the resulting JSON. An example JSON would be:
```json
{
    "resultados":
    [
        {
            "source": "/mnt/data/1393_img_1.jpg",
            "datos":
            {
                "valor_energético": 400,
                "grasas": 32.00,
                "grasas_saturadas": 13.00,
                "carbohidratos": 4.00,
                "azúcares": 0.50,
                "proteinas": 13.00,
                "sal": 1.90
            }
        },
        {
            "source": "/mnt/data/2830_img_1.jpg",
            "datos":
            {
                "valor_energético": 110,
                "grasas": 2.10,
                "grasas_saturadas": 0.70,
                "carbohidratos": 0.00,
                "azúcares": 0.00,
                "proteinas": 22.00,
                "sal": 0.14
            }
        },
        {
            "source": "/mnt/data/2830_img_2.jpg",
            "datos":
            {
                "valor_energético": 110,
                "grasas": 2.10,
                "grasas_saturadas": 0.70,
                "carbohidratos": 0.00,
                "azúcares": 0.00,
                "proteinas": 22.00,
                "sal": 0.14
            }
        },
        {
            "source": "/mnt/data/2832_img_1.jpg",
            "datos":
            {
                "valor_energético": 143,
                "grasas": 8.60,
                "grasas_saturadas": 2.50,
                "carbohidratos": 0.50,
                "azúcares": 0.50,
                "proteinas": 16.50,
                "sal": 1.47
            }
        },
        {
            "source": "/mnt/data/2867_img_1.jpg",
            "datos":
            {
                "valor_energético": 206,
                "grasas": 16.00,
                "grasas_saturadas": 6.00,
                "carbohidratos": 2.00,
                "azúcares": 0.50,
                "proteinas": 17.00,
                "sal": 0.60
            }
        }
    ],
    "log":
    [
        {
            "source": "/mnt/data/1393_img_1.jpg",
            "mensaje": "Tabla por 100 g detectada. Energía en kJ y kcal (se usa kcal=400). Normalización de comas decimales: 0,5→0.50; 1,9→1.90. Validaciones OK (saturadas≤grasas; azúcares≤carbohidratos). Sin campos faltantes ni adicionales."
        },
        {
            "source": "/mnt/data/2830_img_1.jpg",
            "mensaje": "Tabla por 100 g detectada. Energía en kJ y kcal (se usa kcal=110). Normalización de comas decimales: 2,1→2.10; 0,7→0.70; 0,14→0.14. Validaciones OK. Sin campos faltantes ni adicionales."
        },
        {
            "source": "/mnt/data/2830_img_2.jpg",
            "mensaje": "Tabla por 100 g detectada. Mismos valores que la anterior (kcal=110). Normalización de decimales aplicada. Validaciones OK. Sin campos faltantes ni adicionales."
        },
        {
            "source": "/mnt/data/2832_img_1.jpg",
            "mensaje": "Tabla por 100 g detectada. Energía indicada en kcal=143. Valores con signo '<': carbohidratos '<0,5 g' y azúcares '<0,5 g' → se registra 0.50 en ambos. Campos adicionales no incluidos en el esquema: grasas monoinsaturadas y poliinsaturadas. Validaciones OK."
        },
        {
            "source": "/mnt/data/2867_img_1.jpg",
            "mensaje": "Tabla por 100 g detectada. Energía en kJ y kcal (se usa kcal=206). Normalización de decimales (0,5→0.50). Validaciones OK. Sin campos faltantes ni adicionales."
        }
    ]
}
```

 In this example JSON, I used images from different products. You will only encounter results corresponding to the same product. Ideally, there will only be one image to send, which also contains the nutritional information to extract, and you'll get just one result with the extracted nutritional info in the "datos" key. But there could be images, which do not contain the needed info, or even more than one image with the nutritional table, so you'll need to check that all images sent per row refer to the same product_ID, and that all resulting nutritional info dictionaries contain the same values. The next step is then to:
 - Add those nutritional values into the following columns in the dataframe:
 ```
 "valor_energético"
 "grasas"
 "grasas_saturadas"
 "carbohidratos"
 "azúcares"
 "proteinas"
 "sal"
```

 You'll need to create them first and prepopulate them with NaN.

 If the JSON results contain a warning (see the uploaded prompt) for the image file from which you get the nutritional data, add the message to a general log specifying the image filename + the message.

 This log will be printed out to the terminal as you go.

 Lastly, the dataframe with the added nutritional info will be saved as CSV to the `../data/` directory with the name `mercadona_food.csv`.

 I think this is all I need. Ask me any doubt before doing any work.

Additional notes:
1. Use GPT-4o with vision for layout understanding and Structured Outputs to force valid JSON.
2. Use the current directory (`./nutri_prompt.md`).
3. The image folder is `../data/img/`
4. Dataframe columns `img_{i}_nutri_info_file` do contain just the filename.
5. Process only those rows where any `img_{i}_nutri_info_file` is non-null.
6. Overwrite columns filled from a previous run.
7. If two images for the same product return slightly different numbers (e.g., grasas=16.0 vs 16.1), log conflict, calculate the mean value and add it to the dataframe.
8. If the model reports a validation anomaly (e.g., saturadas > grasas), write the numbers to the dataframe and log the validation error.
9. Use the environment variable OPENAI_API_KEY, loaded via .env (using python-dotenv) and ignored in git.
10. Create the 7 nutrition columns up front:
  valor_energético: Pandas nullable integer Int64
  The rest: Pandas nullable Float64 
11. The output path is `../data/mercadona_food.csv` (overwrite if exists).
12. Order by 'id' (product ID), which is the index.
13. Add another optional argument, which will be the id from which to run the function (from that row onwards, once ordered by id). Defaults to the first row of the dataframe.
14. Save to csv periodically.





