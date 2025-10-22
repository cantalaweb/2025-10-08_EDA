# utils.py

import os
import io
import re
import json
import base64
import html
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
import unicodedata
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from unicodedata import normalize as ucnorm


# =====
# UTILS
# =====

# -------------------------------
# Configuration constants
# -------------------------------
IMG_COLS = [
    "img_0_nutri_info_file",
    "img_1_nutri_info_file",
    "img_2_nutri_info_file",
    "img_3_nutri_info_file",
    "img_4_nutri_info_file",
    "img_5_nutri_info_file",
    "img_6_nutri_info_file",
]

NUTRI_COLS_ORDER = [
    "valor_energético",  # Int64
    "grasas",
    "grasas_saturadas",
    "carbohidratos",
    "azúcares",
    "proteinas",
    "sal",
]

PRODUCT_FILENAME_REGEX = re.compile(r"^(\d+)_img_\d+\.jpg$", re.IGNORECASE)


def _load_prompt(prompt_path: str) -> str:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def _b64_data_url(image_path: str) -> str:
    # Encodes local image to data URL (JPEG)
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _same_product_id(filenames: List[str]) -> Optional[str]:
    """
    Ensure all filenames share the same leading product ID prefix.
    Returns that product_id (as string) if OK, else None.
    """
    product_ids = set()
    for name in filenames:
        m = PRODUCT_FILENAME_REGEX.match(name)
        if not m:
            return None
        product_ids.add(m.group(1))
    return list(product_ids)[0] if len(product_ids) == 1 else None

def _ensure_integer_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce index to integer (nullable Int64), then to plain Python int for comparisons.
    If any index values are non-numeric, raises a ValueError.
    """
    idx = pd.to_numeric(pd.Index(df.index), errors="coerce")
    if pd.isna(idx).any():
        bad = [df.index[i] for i, ok in enumerate(~pd.isna(idx)) if not ok][:5]
        raise ValueError(f"Non-numeric index values found (examples: {bad}). Cannot coerce to integer.")
    df = df.copy()
    # Make it Int64 to keep NA-safety, then sort
    df.index = pd.Index(idx.astype("int64"))
    df = df.sort_index()
    return df


def _all_equal(nums: list[float]) -> bool:
    if not nums:
        return False
    first = nums[0]
    return all(abs(x - first) < 1e-9 for x in nums[1:])


def _resolve_consensus_or_mean(norm_list: list[dict]) -> tuple[dict, list[str]]:
    """
    Given a list of normalized 'datos' dicts (same keys), produce a final dict where:
    - If all non-null values for a field are equal -> consensus value
    - Else -> mean of available values (rounded: Int for energy, 2 decimals for floats)
    Returns (final_dict, logs_list).
    """
    final = {}
    logs = []
    for k in NUTRI_COLS_ORDER:
        vals = []
        for d in norm_list:
            v = d.get(k, None)
            if v is None:
                continue
            if isinstance(v, (int, float)):
                vals.append(float(v))
        if not vals:
            final[k] = None
            logs.append(f"{k}: no values found → NaN")
            continue
        if _all_equal(vals):
            # consensus
            val = vals[0]
            if k == "valor_energético":
                final[k] = int(round(val))
            else:
                final[k] = float(f"{val:.2f}")
            logs.append(f"{k}: consensus={final[k]}")
        else:
            # mean
            mean_val = sum(vals) / len(vals)
            if k == "valor_energético":
                final[k] = int(round(mean_val))
                logs.append(f"{k}: mean of {vals} → {final[k]}")
            else:
                final[k] = float(f"{mean_val:.2f}")
                logs.append(f"{k}: mean of {vals} → {final[k]:.2f}")
    return final, logs


def _normalize_datos_types(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure comparable types (floats with 2 decimals for non-energy; energy int).
    """
    out = {}
    for k in NUTRI_COLS_ORDER:
        v = d.get(k, None)
        if v is None:
            out[k] = None
            continue
        if k == "valor_energético":
            try:
                out[k] = int(v)
            except Exception:
                out[k] = None
        else:
            try:
                # round to 2 decimals for comparison and storage
                out[k] = float(f"{float(v):.2f}")
            except Exception:
                out[k] = None
    return out


def _datos_equal(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return _normalize_datos_types(a) == _normalize_datos_types(b)


def _init_openai() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found. Put it in a .env file at project root.")
    return OpenAI(api_key=api_key)


def _call_model_with_images_chat(
    client,
    model: str,
    system_prompt: str,
    user_prompt: str,
    image_paths: list,
    max_retries: int = 3,
    retry_backoff_sec: float = 3.0,
):
    """
    Use Chat Completions API with vision + JSON mode.
    """
    # user content: text + multiple image parts (data URLs)
    user_content = [{"type": "text", "text": user_prompt}]
    for p in image_paths:
        # Reuse your existing helper that returns a data URL:
        # data_url = _b64_data_url(p)
        fname = os.path.basename(p)
        user_content.append({"type": "text", "text": f"FILENAME: {fname}"})
        user_content.append({
            "type": "image_url",
            "image_url": {"url": _b64_data_url(p)}
        })

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,  # e.g., "gpt-4o"
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0,
            )
            text = resp.choices[0].message.content
            return json.loads(text)
        except Exception as e:
            last_err = e
            if attempt == max_retries:
                raise
            time.sleep(retry_backoff_sec * attempt)
    # If we somehow exit loop:
    raise last_err



def extract_nutrition_to_df(
    df: pd.DataFrame,
    images_dir: str = "../data/img",
    prompt_path: str = "./nutri_prompt.md",
    model: str = "gpt-4o",
    start_from_id: Optional[int] = None,
    save_every: int = 50,
    out_csv_path: str = "../data/mercadona_food.csv",
) -> pd.DataFrame:
    """
    Iterates rows with at least one non-null 'img_{i}_nutri_info_file',
    sends images to GPT-4o with structured JSON output, writes 7 nutrition cols,
    logs issues, and saves CSV periodically and at the end.

    - Orders the dataframe by its index (assumed product ID).
    - If start_from_id is provided, starts from that index and onward.
    - Overwrites existing nutrition values.
    - On conflicting JSON across images → logs conflict, leaves NaNs, continue.
    - On validation warnings in model JSON → writes numbers, logs the warning.
    """
    # Ensure index is integer
    df = _ensure_integer_index(df)

    # Ensure index is sorted by product id
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()

    # Optional slicing by start_from_id
    if start_from_id is not None:
        df_proc = df.loc[df.index >= start_from_id].copy()
    else:
        df_proc = df.copy()

    # Create/overwrite nutrition columns with required dtypes
    if "valor_energético" not in df_proc.columns:
        df_proc["valor_energético"] = pd.Series(pd.array([pd.NA] * len(df_proc), dtype="Int64"), index=df_proc.index)
    else:
        df_proc["valor_energético"] = df_proc["valor_energético"].astype("Int64", errors="ignore")

    for col in ["grasas", "grasas_saturadas", "carbohidratos", "azúcares", "proteinas", "sal"]:
        if col not in df_proc.columns:
            df_proc[col] = pd.Series(pd.array([pd.NA] * len(df_proc), dtype="Float64"), index=df_proc.index)
        else:
            df_proc[col] = df_proc[col].astype("Float64", errors="ignore")

    # Filter to rows with any of the 7 image columns as non-null string
    has_any_img = df_proc[IMG_COLS].apply(lambda s: s.fillna("").astype(str).str.len() > 0).any(axis=1)
    df_proc = df_proc.loc[has_any_img].copy()

    if df_proc.empty:
        print("No rows with candidate images found. Nothing to do.")
        return df

    # Prepare model + prompt
    client = _init_openai()
    system_prompt = _load_prompt(prompt_path)

    processed = 0
    overall_log: List[str] = []

    for pid, row in df_proc.iterrows():
        # Collect candidate filenames from the 7 columns
        raw_files = []
        for c in IMG_COLS:
            val = row.get(c, None)
            if isinstance(val, str) and val.strip():
                raw_files.append(val.strip())

        # Deduplicate while preserving order
        filenames = list(dict.fromkeys(raw_files))

        # Validate same product id across all filenames
        prod_id_from_names = _same_product_id(filenames)
        if prod_id_from_names is None:
            msg = f"[{pid}] CONFLICT: Filenames do not match pattern or share same product ID → {filenames}"
            print(msg)
            overall_log.append(msg)
            processed += 1
            if processed % save_every == 0:
                df.sort_index().to_csv(out_csv_path, index=True)
            continue

        # Optional: ensure filename product id matches row index
        row_label_int = int(pid)
        if str(row_label_int) != prod_id_from_names:
            msg = f"[row_label={row_label_int}] WARNING: Row index != filename product ID ({prod_id_from_names}). Proceeding but logging."
            print(msg)
            overall_log.append(msg)

        # Resolve full paths, filter missing
        full_paths = []
        missing = []
        for name in filenames:
            p = os.path.join(images_dir, name)
            if os.path.exists(p):
                full_paths.append(p)
            else:
                missing.append(name)
        if missing:
            msg = f"[{pid}] WARNING: Missing files skipped: {missing}"
            print(msg)
            overall_log.append(msg)

        if not full_paths:
            msg = f"[{pid}] SKIP: No existing image files."
            print(msg)
            overall_log.append(msg)
            processed += 1
            if processed % save_every == 0:
                df.sort_index().to_csv(out_csv_path, index=True)
            continue

        # Build user message:
        # Keep user message minimal; the extraction rules live in system prompt.
        user_prompt = (
            "Analiza estas imágenes del mismo producto y devuelve el JSON estrictamente según las instrucciones.\n"
            "Recuerda: si no hay tabla válida por 100 g, regístralo en el log.\n"
            "Si hay varias tablas, asegúrate de dar valores consistentes (o informa conflicto en el log)."
        )

        try:
            data = _call_model_with_images_chat(
                client=client,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image_paths=full_paths,
            )
        except Exception as e:
            msg = f"[{pid}] ERROR: API call failed: {e}"
            print(msg)
            overall_log.append(msg)
            processed += 1
            if processed % save_every == 0:
                df.sort_index().to_csv(out_csv_path, index=True)
            continue

        # Expect keys: "resultados": [ { "source": "...", "datos": {...} }, ...], "log": [...]
        resultados = data.get("resultados", [])
        logs = data.get("log", [])

        # Print logs (kept)
        if isinstance(logs, list):
            for entry in logs:
                src = entry.get("source", "")
                msg = entry.get("mensaje", "")
                if msg:
                    line = f"[{pid}] LOG ({os.path.basename(src) if src else src}): {msg}"
                    print(line)
                    overall_log.append(line)

        # Map datos by exact filename when possible
        datos_by_file = {}
        for r in (resultados or []):
            src = r.get("source", "")
            datos = r.get("datos", {})
            if datos:
                datos_by_file[os.path.basename(src)] = datos

        # First try: strict match by filenames we sent
        selected_datos = []
        strict_miss = []
        for p in full_paths:
            base = os.path.basename(p)
            if base in datos_by_file:
                selected_datos.append(datos_by_file[base])
            else:
                strict_miss.append(base)

        # Fallback: if nothing matched but we do have resultados with datos, use them
        if not selected_datos and resultados:
            # Warn once about source mismatch
            if strict_miss:
                warn = (f"[{pid}] WARNING: Model 'source' names did not match filenames "
                        f"(e.g., {strict_miss[:2]}...). Falling back to use all 'datos' from 'resultados'.")
                print(warn)
                overall_log.append(warn)
            selected_datos = [r.get("datos") for r in resultados if r.get("datos")]

        if not selected_datos:
            msg = f"[{pid}] INFO: No 'datos' parsed from any image. Leaving NaNs."
            print(msg)
            overall_log.append(msg)
            processed += 1
            if processed % save_every == 0:
                df.sort_index().to_csv(out_csv_path, index=True)
            continue

        # Consistency check as before...
        # If still nothing, bail out
        if not selected_datos:
            msg = f"[{pid}] INFO: No 'datos' parsed from any image. Leaving NaNs."
            print(msg)
            overall_log.append(msg)
            processed += 1
            if processed % save_every == 0:
                df.sort_index().to_csv(out_csv_path, index=True)
            continue

        # Normalize all selected 'datos'
        norm_list = [_normalize_datos_types(d) for d in selected_datos]

        # Are all dicts exactly equal?
        all_equal = all(norm_list[i] == norm_list[0] for i in range(1, len(norm_list)))

        if all_equal:
            final_datos = norm_list[0]
        else:
            # Resolve per-field (consensus or mean)
            resolved, res_logs = _resolve_consensus_or_mean(norm_list)
            print(f"[{pid}] CONFLICT: Resolved per-field via consensus/mean.")
            overall_log.append(f"[{pid}] CONFLICT: Resolved per-field via consensus/mean.")
            for line in res_logs:
                l = f"[{pid}] RESOLVE {line}"
                print(l)
                overall_log.append(l)
            final_datos = resolved

        # Assign to df (overwrite allowed)
        # Note: work on original df (not filtered view), using pid index
        if "valor_energético" in final_datos:
            df.loc[pid, "valor_energético"] = (
                pd.NA if final_datos["valor_energético"] is None else int(final_datos["valor_energético"])
            )

        for col in ["grasas", "grasas_saturadas", "carbohidratos", "azúcares", "proteinas", "sal"]:
            df.loc[pid, col] = (
                pd.NA if final_datos.get(col, None) is None else float(final_datos[col])
            )

        # Progress logging
        msg_ok = f"[{pid}] OK: Nutrition values written."
        print(msg_ok)
        overall_log.append(msg_ok)

        processed += 1
        if processed % save_every == 0:
            print(f"[SAVE] Periodic save after {processed} rows → {out_csv_path}")
            df.sort_index().to_csv(out_csv_path, index=True)

    # Final save
    df.sort_index().to_csv(out_csv_path, index=True)
    print(f"[DONE] Saved: {out_csv_path}")
    return df


def _norm(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    t = str(s).lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    t = t.replace(";", ",")
    return t

# ==============
# SEMÁFORO (FoP)
# ==============
def _classify_product_simple(category, fat_g=None, sat_g=None, sugars_g=None, salt_g=None, sodium_g=None, per=None):
    if per is None:
        per = "100g" if category == "food" else "100ml"

    if salt_g is None and sodium_g is not None and not pd.isna(sodium_g):
        salt_g = sodium_g * 2.5  # sal = sodio * 2.5

    thresholds = {
        "food": {   # por 100 g
            "fat":    {"low": 3.0,  "high": 17.5},
            "sat":    {"low": 1.5,  "high": 5.0},
            "sugars": {"low": 5.0,  "high": 22.5},
            "salt":   {"low": 0.30, "high": 1.50},
        },
        "drink": {  # por 100 ml
            "fat":    {"low": 1.5,  "high": 8.75},
            "sat":    {"low": 0.75, "high": 2.5},
            "sugars": {"low": 2.5,  "high": 11.25},
            "salt":   {"low": 0.30, "high": 1.50},
        },
    }

    vals = {"fat": fat_g, "sat": sat_g, "sugars": sugars_g, "salt": salt_g}

    def color_for(nutrient, value):
        if value is None or pd.isna(value):
            return None
        low = thresholds[category][nutrient]["low"]
        high = thresholds[category][nutrient]["high"]
        if value <= low:
            return "green"
        elif value >= high:
            return "red"
        else:
            return "amber"

    colors = {k: color_for(k, v) for k, v in vals.items()}
    reds   = sum(1 for c in colors.values() if c == "red")
    greens = sum(1 for c in colors.values() if c == "green")
    ambers = sum(1 for c in colors.values() if c == "amber")

    if reds >= 2:
        decision = "no saludable"
    elif greens >= 3 and reds == 0:
        decision = "saludable"
    else:
        decision = "a valorar"

    return {
        "nutrients": {
            "fat":    {"value_g": fat_g,    "color": colors["fat"]},
            "sat":    {"value_g": sat_g,    "color": colors["sat"]},
            "sugars": {"value_g": sugars_g, "color": colors["sugars"]},
            "salt":   {"value_g": salt_g,   "color": colors["salt"]},
        },
        "reds": reds, "greens": greens, "ambers": ambers, "decision": decision,
    }


def add_traffic_lights(
    df,
    *,
    colmap=None,
    category_default="food",
    category_col=None,
    price_size_format_col="price_size_format",  # 'kg'->food, 'l'->drink
    level2_col="level_2_cat_name",              # atajo 3 verdes si no hay tabla y está en lista
    level0_col="level_0_cat_name"               # override 3 rojos si es 'Bodega'
):
    """
    Añade columnas:
      tl_fat, tl_sat, tl_sugars, tl_salt, tl_reds, tl_greens, tl_ambers, tl_decision
    Reglas:
      1) Categoría por fila: 'kg' -> food, 'l' -> drink (si no, usa 'category' o category_default).
      2) Si NO hay datos nutricionales y level_2_cat_name está en la lista blanca, asigna 3 verdes (sal=None).
      3) Si level_0_cat_name == 'Bodega', fuerza 3 rojos y 'no saludable'.

    Puedes mapear nombres de columnas con colmap:
      {"fat_g":"grasas", "sat_g":"grasas_saturadas", "sugars_g":"azucares",
       "salt_g":"sal", "sodium_g":"sodio", "per":"por", "category":"categoria"}
    """

    # --- util: normalizar acentos y minúsculas ---
    def _norm(s):
        if s is None or (isinstance(s, float) and pd.isna(s)):
            return ""
        t = str(s).lower().strip()
        t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
        return t

    # Lista blanca (normalizada) para el atajo 3 verdes sin tabla
    SAFE_L2_CATS = {
        "vacuno","cerdo","pollo","pavo y otras aves","conejo","cordero","manzana y pera",
        "fruta tropical","platanoy uva","platano y uva","citricos","naranja","melon y sandia",
        "melony sandia","otras verduras y hortalizas","otras frutas","carne congelada","arroz",
        "alubias","garbanzos","lentejas y otros","frutos secos","te","hierbas","melocoton",
        "colorante y pimenton","limon","sal y bicarbonato","leche en polvo","leche desnatada",
        "leche entera","leche semidesnatada","verdura","huevos","agua sin gas","pescado congelado",
        "marisco","sepia, pulpo y calamar congelado","agua con gas","otras especias","pimienta",
        "hielo","lechuga","repollo y col","calabacin y pimiento","setas y champinones",
        "pepino y zanahoria","corvina","sardina","trucha","bacalao","lenguado","dorada",
        "lubina","salmon","boqueron","sepia, pulpo y calamar","rodaballo",
    }

    # --- mapeo de columnas ---
    colmap = colmap or {}
    fat_col    = colmap.get("fat_g", "fat_g")
    sat_col    = colmap.get("sat_g", "sat_g")
    sugars_col = colmap.get("sugars_g", "sugars_g")
    salt_col   = colmap.get("salt_g", "salt_g")
    sodium_col = colmap.get("sodium_g", "sodium_g")
    per_col    = colmap.get("per", "per")
    category_col = category_col or colmap.get("category", "category")

    for c in [fat_col, sat_col, sugars_col, salt_col, sodium_col, per_col,
              category_col, price_size_format_col, level2_col, level0_col]:
        if c not in df.columns:
            df[c] = np.nan

    # --- clasificador de semáforo por fila ---
    def _classify_product_simple(category, fat_g=None, sat_g=None, sugars_g=None, salt_g=None, sodium_g=None, per=None):
        if per is None:
            per = "100g" if category == "food" else "100ml"
        if salt_g is None and sodium_g is not None and not pd.isna(sodium_g):
            salt_g = sodium_g * 2.5  # sal = sodio * 2.5
        thresholds = {
            "food": {"fat":{"low":3.0,"high":17.5},"sat":{"low":1.5,"high":5.0},"sugars":{"low":5.0,"high":22.5},"salt":{"low":0.30,"high":1.50}},
            "drink":{"fat":{"low":1.5,"high":8.75},"sat":{"low":0.75,"high":2.5},"sugars":{"low":2.5,"high":11.25},"salt":{"low":0.30,"high":1.50}},
        }
        def color_for(nutrient, value):
            if value is None or pd.isna(value):
                return None
            low = thresholds[category][nutrient]["low"]
            high = thresholds[category][nutrient]["high"]
            if value <= low: return "green"
            elif value >= high: return "red"
            else: return "amber"
        colors = {
            "fat": color_for("fat", fat_g),
            "sat": color_for("sat", sat_g),
            "sugars": color_for("sugars", sugars_g),
            "salt": color_for("salt", salt_g),
        }
        reds   = sum(1 for c in colors.values() if c == "red")
        greens = sum(1 for c in colors.values() if c == "green")
        ambers = sum(1 for c in colors.values() if c == "amber")
        if reds >= 2: decision = "no saludable"
        elif greens >= 3 and reds == 0: decision = "saludable"
        else: decision = "a valorar"
        return {
            "nutrients": {
                "fat":{"value_g":fat_g,"color":colors["fat"]},
                "sat":{"value_g":sat_g,"color":colors["sat"]},
                "sugars":{"value_g":sugars_g,"color":colors["sugars"]},
                "salt":{"value_g":salt_g,"color":colors["salt"]},
            },
            "reds":reds,"greens":greens,"ambers":ambers,"decision":decision
        }

    # --- helpers de categorías ---
    def _in_whitelist_level2(val):
        if isinstance(val, (list, tuple, set)):
            return any(_norm(x) in SAFE_L2_CATS for x in val)
        if isinstance(val, str):
            parts = [p.strip() for p in re.split(r"[|;,]", val)] if any(sep in val for sep in "|;,") else [val]
            return any(_norm(p) in SAFE_L2_CATS for p in parts)
        return False

    def _is_bodega(val):
        if isinstance(val, (list, tuple, set)):
            return any(_norm(x) == "bodega" for x in val)
        return _norm(val) == "bodega"

    # --- apply fila a fila ---
    def _row_apply(row):
        fat_v, sat_v, sug_v, salt_v, sod_v = row[fat_col], row[sat_col], row[sugars_col], row[salt_col], row[sodium_col]
        no_nutri = all(pd.isna(v) for v in [fat_v, sat_v, sug_v, salt_v, sod_v])

        # Atajo 3 verdes si no hay tabla y L2 ∈ whitelist
        if no_nutri and _in_whitelist_level2(row.get(level2_col)):
            res = {
                "tl_fat":    "green",
                "tl_sat":    "green",
                "tl_sugars": "green",
                "tl_salt":   None,
                "tl_reds":   0,
                "tl_greens": 3,
                "tl_ambers": 0,
                "tl_decision": "saludable",
            }
        else:
            # Categoria por 'price_size_format': 'l'->drink, 'kg'->food; si no, usa 'category' o default
            psf = row.get(price_size_format_col)
            psf_l = psf.strip().lower() if isinstance(psf, str) else None
            if psf_l == "l":
                category = "drink"
            elif psf_l == "kg":
                category = "food"
            else:
                raw_cat = row.get(category_col)
                category = "drink" if str(raw_cat).lower().strip() == "drink" else ("food" if pd.notna(raw_cat) else category_default)

            r = _classify_product_simple(
                category=category,
                fat_g=fat_v, sat_g=sat_v, sugars_g=sug_v, salt_g=salt_v, sodium_g=sod_v,
                per=row[per_col] if pd.notna(row[per_col]) else None,
            )
            res = {
                "tl_fat":    r["nutrients"]["fat"]["color"],
                "tl_sat":    r["nutrients"]["sat"]["color"],
                "tl_sugars": r["nutrients"]["sugars"]["color"],
                "tl_salt":   r["nutrients"]["salt"]["color"],
                "tl_reds":   r["reds"],
                "tl_greens": r["greens"],
                "tl_ambers": r["ambers"],
                "tl_decision": r["decision"],
            }

        # Override final: 'Bodega' => 3 rojos
        if _is_bodega(row.get(level0_col)):
            res["tl_fat"] = "red"
            res["tl_sat"] = "red"
            res["tl_sugars"] = "red"
            # tl_salt: lo dejamos como esté (puede ser None o su color real)
            res["tl_reds"] = 3
            res["tl_greens"] = 0
            res["tl_ambers"] = 0
            res["tl_decision"] = "no saludable"

        return pd.Series(res)

    return df.join(df.apply(_row_apply, axis=1))



# ===================
# HEURÍSTICA DE NOVA
# ===================

def _clean_html_and_normalize(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    soup = BeautifulSoup(s, "lxml")
    for tag in soup.find_all(['br','p','div','li']):
        tag.insert_before('\n')
    for tag in soup(['script','style']):
        tag.decompose()
    txt = soup.get_text(separator=' ', strip=True)
    txt = html.unescape(txt)
    txt = ucnorm('NFKC', txt)
    # baja a minúsculas y quita acentos igual que tu _norm()
    txt = txt.lower()
    txt = "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")
    # homogeneiza separadores
    txt = txt.replace(";", ",")
    return re.sub(r"[ \t]+", " ", txt).strip()

# --- Regex para códigos E con variantes (espacios/guiones/letra/romanos/paréntesis) ---
E_CODE_RE = re.compile(
    r"""
    \b
    e                      # E/e
    [\s\-]?                # separador opcional
    (?P<num>\d{3,4})       # 3-4 dígitos
    (?P<letter>[a-d])?     # sufijo letra (a-d) opcional
    (?:                    # subíndice romano opcional
        [\s\-]*            # separador
        (?:\(|\-)?         # paréntesis o guion opcional
        (?P<roman>i{1,3}|iv|v|vi{0,3})
        \)?
    )?
    \b
    """,
    re.IGNORECASE | re.VERBOSE
)

def _normalize_e_match(m: re.Match) -> str:
    num = m.group('num')
    letter = (m.group('letter') or '').lower()
    roman = (m.group('roman') or '').lower()
    return f"E-{num}{letter}{roman}"

# --- Nombres comunes → E-code (amplía según tus datos) ---
NAME_TO_E = {
    # Conservantes
    r"\bsorbato\s+potasico[s]?\b": "E-202",
    r"\bacido\s+sorbico\b": "E-200",
    r"\bbenzoato\s+sodico[s]?\b": "E-211",
    r"\bacido\s+benzoico\b": "E-210",
    r"\bnitrito\s+sodico\b": "E-250",
    r"\bnitrito\s+potasico\b": "E-249",
    r"\bnitrato\s+sodico\b": "E-251",
    r"\bnitrato\s+potasico\b": "E-252",
    r"\bsulfitos?\b": "E-220..E-228",  # familia

    # Antioxidantes
    r"\bascorbato\s+sodico\b": "E-301",
    r"\bascorbato\s+cal[c|c]ico\b": "E-302",
    r"\bacido\s+ascorbico\b": "E-300",
    r"\beritorbato\s+sodico\b": "E-316",
    r"\btocoferol(?:es)?\b": "E-306",

    # Colorantes
    r"\bcaramelo\s+amonico\b": "E-150c",
    r"\bcaramelo\s+natural\b": "E-150a",
    r"\bcarbon\s+vegetal\b": "E-153",
    r"\bbeta?-?caroten[oa]?\b": "E-160a",

    # Texturizantes/estabilizantes
    r"\bgoma\s+xantana\b": "E-415",
    r"\bcarragenan(?:o|os|atos)?\b": "E-407",
    r"\bagar-?agar\b": "E-406",
    r"\bgoma\s+guar\b": "E-412",
    r"\bpectinas?\b": "E-440",
    r"\balginato(?:s)?\b": "E-401..E-405",  # familia

    # Emulgentes
    r"\blecitina(?:s)?(?:\s+de\s+soja)?\b": "E-322",
    r"\bmonogliceridos\s+y\s+digliceridos(?:\s+de\s+[^\s]+)?\s*de\s+acidos\s+grasos\b": "E-471",
    r"\bacetato\s+de\s+mono\s+y\s+digliceridos\b": "E-472e",

    # Otros
    r"\bedta\s+de\s+calcio\s+y\s+disodio\b": "E-385",
    r"\bglutamato\s+monosodico\b": "E-621",
    r"\baroma\s+de\s+humo\b": "aroma_humo",
}
NAME_PATTERNS = [(re.compile(pat, re.IGNORECASE), code) for pat, code in NAME_TO_E.items()]

# --- Clases tecnológicas (marcadores de procesado) ---
TECH_CLASSES_RE = re.compile(
    r"\b("
    r"conservador(?:es)?|antioxidante(?:s)?|colorante(?:s)?|estabilizante(?:s)?|"
    r"emulgente(?:s)?|espesante(?:s)?|gelificante(?:s)?|"
    r"potenciador(?:es)?\s+del\s+sabor|aromas?|"
    r"acidulante(?:s)?|corrector(?:es)?\s+de\s+la?\s*acidez|regulador(?:es)?\s+de\s+acidez|"
    r"gasificante(?:s)?"
    r")\b",
    re.IGNORECASE
)


def classify_ultraprocessed_from_ingredients(ingredients_text):
    """
    Devuelve {"label": "UPF (NOVA-4) / Procesado (NOVA-3) / Min/Ingred (NOVA-1/2)",
              "score": int, "triggers": {...}}
    Mejora: captura códigos E con variantes, nombres en claro, familias y clases tecnológicas.
    """
    # 1) Limpieza y normalización robusta (HTML + Unicode + acentos)
    txt = _clean_html_and_normalize(ingredients_text)

    # 2) Códigos E explícitos (con variantes)
    e_matches = list(E_CODE_RE.finditer(txt))
    e_codes = { _normalize_e_match(m) for m in e_matches }

    # 3) Nombres en claro → E-code o familia
    names_found = set()
    mapped_e = set()
    families = set()
    for pat, code in NAME_PATTERNS:
        for m in pat.finditer(txt):
            names_found.add(m.group(0))
            if ".." in code:
                families.add(code)
            elif code != "aroma_humo":
                mapped_e.add(code)

    # 4) Clases tecnológicas (delatan procesado aunque no haya E-code)
    classes_found = {m.group(0).lower() for m in TECH_CLASSES_RE.finditer(txt)}

    # 5) Otros detonantes ya existentes (edulcorantes, “cosméticos”, industriales, etc.)
    SWEETENERS = [
        "aspartame","acesulfame","sucralosa","sacarina","ciclamato","neotame","advantame",
        "stevia","esteviosido","glucosidos de esteviol","eritritol","xilitol","maltitol","sorbitol",
        "edulcorante","sweetener"
    ]
    COSMETIC_ADDITIVES = [
        "aroma","aromas","saborizante","flavor","flavour","humo liquido","smoke flavour",
        "colorante","color","color added","color added",
        "estabilizante","emulgente","espesante","gelificante","potenciador del sabor"
    ]
    INDUSTRIAL_INGREDIENTS = [
        "jarabe de glucosa","jarabe de fructosa","jarabe de glucosa-fructosa","jarabe de maiz",
        "proteina aislada","proteina texturizada","maltodextrina","dextrosa",
        "aceites refinados","aceite refinado","grasa vegetal","aceite vegetal",
        "grasas hidrogenadas","parcialmente hidrogenad","interesterificad"
    ]
    PROCESADO_CULINARIO = ["en salmuera","en vinagre","curado","fermentado","ahumado","salado","conserva de","encurtido"]

    # 6) Contadores y triggers (unificados)
    sweeteners_found = [w for w in SWEETENERS if w in txt]
    cosmetic_found    = [w for w in COSMETIC_ADDITIVES if w in txt]
    industrial_found  = [w for w in INDUSTRIAL_INGREDIENTS if w in txt]
    cul_proc_found    = [w for w in PROCESADO_CULINARIO if w in txt]
    mentions_flavour  = bool(re.search(r"\baromas?\b|\bflavou?r(ings?)?\b", txt))

    # Unifica E-codes: explícitos + mapeados por nombre
    all_e = sorted(e_codes | mapped_e)

    found = {
        "e_numbers": all_e,
        "families": sorted(families),                  # p.ej. E-220..E-228 (sulfitos)
        "named_additives": sorted(names_found),        # coincidencias literales (texto)
        "classes": sorted(classes_found),              # conservador/antioxidante/…
        "sweeteners": sweeteners_found,
        "cosmetic_additives": cosmetic_found,
        "industrial_ingredients": industrial_found,
        "procesado_culinario": cul_proc_found,
        "mentions_flavourings": mentions_flavour,
    }

    # 7) Scoring conservador (compatible con tu lógica previa, pero más sensible)
    n_e       = len(all_e)
    n_family  = len(families)
    n_sweet   = len(sweeteners_found)
    n_cosm    = len(cosmetic_found)
    n_ind     = len(industrial_found)
    n_class   = len(classes_found)

    score = 0
    # Señales fuertes
    if n_sweet >= 1: score += 2
    if n_ind   >= 1: score += 1
    # Señales medias
    if n_cosm  >= 1: score += 1
    if n_cosm  >= 2: score += 1
    # Cantidad de aditivos
    if n_e     >= 2: score += 1
    if n_e     >= 4: score += 1
    # Familias/clases ayudan a no perder casos sin E-code explícito
    if n_family >= 1: score += 1
    if n_class  >= 1 and n_e == 0: score += 1  # solo clases, sin E-code → aún así cuenta

    # Regla para NOVA-3 “culinario” (como ya hacías)
    if len(cul_proc_found) >= 1 and n_cosm == 0 and n_ind == 0 and n_sweet == 0:
        return {"label": "Procesado (NOVA-3)", "score": 0, "triggers": found}

    # Umbrales finales
    if score >= 3:
        label = "UPF (NOVA-4)"
    elif score >= 1:
        label = "Procesado (NOVA-3)"
    else:
        label = "Min/Ingred (NOVA-1/2)"

    return {"label": label, "score": score, "triggers": found}


def add_nova_from_ingredients(df, ingredients_col="ingredients"):
    pred = df[ingredients_col].apply(classify_ultraprocessed_from_ingredients)
    df = df.copy()
    df["nova_label"] = pred.apply(lambda d: d["label"])
    df["nova_score"] = pred.apply(lambda d: d["score"])
    # opcional (pesado): df["nova_triggers"] = pred.apply(lambda d: d["triggers"])
    return df

# =======================
# RANKING MIXTO (N + NOVA)
# =======================
# Patrones por defecto (puedes cambiarlos al llamar a add_mixed_score)
WHITELIST_OILS_RE = re.compile(r"\b(virgen extra|extra virgin|virgen|prensado en frio|cold pressed)\b")
WHITELIST_SINGLE_RE = re.compile(r"\b(100%\b|solo\b|unico ingrediente|único ingrediente)\b")
BLACKLIST_SWEETENERS_RE = re.compile(r"\b(aspartam|acesulfam|sucralos|sacarina|ciclamat|eritritol|xilitol|maltitol|stevia|esteviol)\w*\b", re.I)

def mixed_score_row(
    row,
    *,
    ing_col="ingredients",
    tl_cols=("tl_fat","tl_sat","tl_sugars","tl_salt"),
    nova_label_col="nova_label",
    weight_nutrition=0.6,
    weight_processing=0.4,
    whitelist_oils_re=WHITELIST_OILS_RE,
    whitelist_single_re=WHITELIST_SINGLE_RE,
    blacklist_sweeteners_re=BLACKLIST_SWEETENERS_RE,
):
    # 1) Nutrición
    color_points = {"green": 2, "amber": 1, "red": 0, None: 1}
    N = sum(color_points.get(row.get(c), 1) for c in tl_cols)
    N_norm = 100 * N / 8.0

    # 2) Procesamiento
    nova = str(row.get(nova_label_col, "")).lower()
    if "nova-4" in nova or "upf" in nova:
        P = 0
    elif "nova-3" in nova or "procesado" in nova:
        P = 2
    else:
        P = 3  # NOVA-1/2
    P_norm = 100 * P / 3.0

    # 3) Guardarraíles basados en ingredientes
    ingred = _norm(row.get(ing_col, ""))
    only_fat_red = (row.get("tl_fat") == "red") and all(row.get(c) == "green" for c in ("tl_sat","tl_sugars","tl_salt"))

    # A) Aceites vírgenes / ingrediente único
    if whitelist_oils_re.search(ingred) and (whitelist_single_re.search(ingred) or "," not in ingred):
        if only_fat_red:
            N_norm = min(100, N_norm + (2/8)*100)  # tratar 'fat' como verde

    # B) Frutos secos 100%
    if (("100%" in ingred) or ("solo" in ingred) or ("unico ingrediente" in ingred) or ("único ingrediente" in ingred)) and \
       any(w in ingred for w in ["almendra","nuez","avellana","cacahuete","pistacho","anacardo","semilla"]):
        if only_fat_red:
            N_norm = min(100, N_norm + (2/8)*100)

    # C) Bebidas con edulcorantes
    cap_class = False
    if "drink" in str(row.get("category","")).lower() and blacklist_sweeteners_re.search(ingred):
        N_norm = min(N_norm, 80)
        P_norm = min(P_norm, 50)
        cap_class = True

    # 4) Mixto
    M = weight_nutrition * N_norm + weight_processing * P_norm

    # 5) Etiqueta final
    if M >= 75:
        label = "Saludable"
    elif M >= 55:
        label = "A valorar"
    else:
        label = "No saludable"

    if cap_class and label == "Saludable":
        label = "A valorar"

    return round(M,1), label

def add_mixed_score(
    df,
    *,
    ing_col="ingredients",
    tl_cols=("tl_fat","tl_sat","tl_sugars","tl_salt"),
    nova_label_col="nova_label",
    weight_nutrition=0.6,
    weight_processing=0.4,
    whitelist_oils_re=WHITELIST_OILS_RE,
    whitelist_single_re=WHITELIST_SINGLE_RE,
    blacklist_sweeteners_re=BLACKLIST_SWEETENERS_RE,
):
    scorer = lambda row: mixed_score_row(
        row,
        ing_col=ing_col,
        tl_cols=tl_cols,
        nova_label_col=nova_label_col,
        weight_nutrition=weight_nutrition,
        weight_processing=weight_processing,
        whitelist_oils_re=whitelist_oils_re,
        whitelist_single_re=whitelist_single_re,
        blacklist_sweeteners_re=blacklist_sweeteners_re,
    )
    scores = df.apply(scorer, axis=1)
    df = df.copy()
    df["mixed_score"], df["mixed_label"] = zip(*scores)
    return df
