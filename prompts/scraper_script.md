I need to capture some data using Python. I need the data to be stored in a Pandas DataFrame. And the data will be captured using an internal REST API from a Spanish supermarket (Mercadona).

The REST API has only three endpoints:
https://tienda.mercadona.es/api/categories/
https://tienda.mercadona.es/api/categories/{category_id}/
https://tienda.mercadona.es/api/products/{product_id}/

You would need to call the first endpoint to get the list of categories:
```json
{
  "count": 26,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 12,  // category_id
      "name": "Aceite, especias y salsas",
      "order": 7,
      "is_extended": false,
      "categories": [
        {
          "id": 112,  // category_id
          "name": "Aceite, vinagre y sal",
          "order": 7,
          "layout": 1,
          "published": true,
          "is_extended": false
        },
        {
          "id": 115,  // category_id
          "name": "Especias",
          "order": 7,
          "layout": 1,
          "published": true,
          "is_extended": false
        },
        {
          "id": 116,  // category_id
          "name": "Mayonesa, ketchup y mostaza",
          "order": 7,
          "layout": 1,
          "published": true,
          "is_extended": false
        },
        {
          "id": 117,  // category_id
          "name": "Otras salsas",
          "order": 7,
          "layout": 1,
          "published": true,
          "is_extended": false
        }
      ]
    },
    {
      "id": 18,  // category_id
      "name": "Agua y refrescos",
      "order": 8,
      "is_extended": false,
      "categories": [
        {
          "id": 156,  // category_id
          "name": "Agua",
          "order": 8,
          "layout": 1,
          "published": true,
          "is_extended": false
        },
        {
          "id": 163,  // category_id
          "name": "Isotónico y energético",
          "order": 8,
          "layout": 1,
          "published": true,
          "is_extended": false
        },
        {
          "id": 158,  // category_id
          "name": "Refresco de cola",
          "order": 8,
          "layout": 1,
          "published": true,
          "is_extended": false
        },
        {
          "id": 159,  // category_id
          "name": "Refresco de naranja y de limón",
          "order": 8,
          "layout": 1,
          "published": true,
          "is_extended": false
        },
        {
          "id": 161,  // category_id
          "name": "Tónica y bitter",
          "order": 8,
          "layout": 1,
          "published": true,
          "is_extended": false
        },
        {
          "id": 162,  // category_id
          "name": "Refresco de té y sin gas",
          "order": 8,
          "layout": 1,
          "published": true,
          "is_extended": false
        }
      ]
    },
    // ...and so on.
```

Then iterate over it and calling the second endpoint with each category_id, in order to get the list of products from that category:
```json
{
  "id": 80,  // requested category_id 
  "name": "Galletas",
  "order": 18,
  "layout": 1,
  "published": true,
  "is_extended": false,
  "categories": [
    {
      "id": 821,
      "name": "Galletas desayuno",
      "order": 18,
      "layout": 2,
      "published": true,
      "is_extended": false,
      "image": null,
      "subtitle": null,
      "products": [
        {
          "id": "14132",  // product_id to request in the third endpoint
          "slug": "galletas-maria-dorada-hacendado-paquete",
          "limit": 999,
          "badges": {
            "is_water": false,
            "requires_age_check": false
          },
          "status": null,
          "packaging": "Paquete",
          "published": true,
          "share_url": "https://tienda.mercadona.es/product/14132/galletas-maria-dorada-hacendado-paquete",
          "thumbnail": "https://prod-mercadona.imgix.net/images/55efb2a2e65c2bc310d6b72853663cc5.jpg?fit=crop&h=300&w=300",
          "categories": [
            {
              "id": 7,
              "name": "Cereales y galletas",
              "level": 0,
              "order": 18
            }
          ],
          "display_name": "Galletas María dorada Hacendado",
          "unavailable_from": null,
          "price_instructions": {
            "iva": 10,
            "is_new": false,
            "is_pack": false,
            "pack_size": null,
            "unit_name": "ud.",
            "unit_size": 0.8,
            "bulk_price": "1.75",
            "unit_price": "1.40",
            "approx_size": false,
            "size_format": "kg",
            "total_units": 4,
            "unit_selector": true,
            "bunch_selector": false,
            "drained_weight": null,
            "selling_method": 0,
            "tax_percentage": "10.000",
            "price_decreased": false,
            "reference_price": "1.750",
            "min_bunch_amount": 1,
            "reference_format": "kg",
            "previous_unit_price": null,
            "increment_bunch_amount": 1
          },
          "unavailable_weekdays": []
        },
        // ...and so on.
```

From this list of products, disregard everything, except the product_ids. Use them to fetch all product data with the third endpoint.

From each requested product, only the following keys would be necessary:
```json
{
  "id": "14132",   //  product_id
  "ean": "8480000141323",
  "photos": [
    {
      "zoom": "https://prod-mercadona.imgix.net/images/55efb2a2e65c2bc310d6b72853663cc5.jpg?fit=crop&h=1600&w=1600",
      "perspective": 1
    },
    {
      "zoom": "https://prod-mercadona.imgix.net/images/557274632d7eb8309a01faf73f58cded.jpg?fit=crop&h=1600&w=1600",
      "perspective": 9
    }
  ],
  "status": null,
  "details": {
    "brand": "Hacendado",
    "origin": "España",
    "description": "Galletas María dorada Hacendado",
    "counter_info": null,
    "danger_mentions": "",
    "alcohol_by_volume": null,
    "mandatory_mentions": "",
    "production_variant": "",
    "usage_instructions": "",
    "storage_instructions": ""
  },
  "is_bulk": false,
  "packaging": "Paquete",
  "published": true,
  "share_url": "https://tienda.mercadona.es/product/14132/galletas-maria-dorada-hacendado-paquete",
  "categories": [
    {
      "id": 7,
      "level": 0,
      "order": 18,
      "name": "Cereales y galletas",
      "categories": [
        {
          "id": 80,
          "name": "Galletas",
          "level": 1,
          "order": 18,
          "categories": [
            {
              "id": 821,
              "name": "Galletas desayuno",
              "level": 2,
              "order": 18
            }
          ]
        }
      ]
    }
  ],
  "extra_info": [null],
  "display_name": "Galletas María dorada Hacendado",
  "is_variable_weight": false,
  "price_instructions": {
    "iva": 10,
    "is_new": false,
    "is_pack": false,
    "pack_size": null,
    "unit_name": "ud.",
    "unit_size": 0.8,
    "bulk_price": "1.75",
    "unit_price": "1.40",
    "approx_size": false,
    "size_format": "kg",
    "total_units": 4,
    "unit_selector": true,
    "bunch_selector": false,
    "drained_weight": null,
    "selling_method": 0,
    "reference_price": "1.750",
    "min_bunch_amount": 1,
    "reference_format": "kg",
    "increment_bunch_amount": 1
  },
  "nutrition_information": {
    "allergens": "",
    "ingredients": ""
  }
}
```

Please flatten the fields so that they all become dataframe columns. For example, get rid of 'nutrition_information', and put 'allergens' and 'ingredients' as columns. Likewise for 'details' and 'price_instructions'.

Flatten 'categories'  as well. Make them like this:
```
    level_0_cat_id
    level_0_cat_name
    level_0_cat_order
    level_1_cat_id
    level_1_cat_name
    level_1_cat_order
    level_2_cat_id
    level_2_cat_name
    level_2_cat_order
    ...and so on, if there are any more levels.
```

Flatten 'photos' as well. Make them like this:
```
    img_0_url
    img_0_perspective
    img_1_url
    img_1_perspective
    ...and so on, if there are any more photos.
```

All photos will be downloaded to ./img and renamed following this pattern:
```
    {product_id}_img_0.jpg
    {product_id}_img_1.jpg
    ...and so on, if there are any more photos.
```

The dataframe will be named `mercadona`, and contain all products, essentially.

Be sure to track all requested category IDs and product IDs, so as not to fetch them again if encountered down the iterations.

At the end, save the entire Pandas dataframe to a file in the current directory:
```python
mercadona.to_csv('mercadona.csv', index=False)
```

Additional notes:
- Implement error handling and save periodically.
- Rate limiting: add small random delays between API requests to avoid overwhelming their server. Be polite.
- From the results of calling the first endpoint, grab all category IDs. And from the results of requesting each category ID using the second endpoint, grab all product IDs. Since, most probably, you'll encounter duplicates, you'll need to track which category IDs have been already requested. Likewise for the product IDs. Or just store them in a couple of Sets, so they'll be unique, and pop them out once successfully fetched data from them.













I think that is all. If you have any questions or doubts, ask me before doing anything.
