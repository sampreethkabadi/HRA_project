# =============================================================================
# preprocess.py
# Team Crimson -- HRA Web Analytics Dashboard
#
# PURPOSE:
#   Read the two raw Parquet log files, clean and enrich them, and write out
#   four smaller, analysis-ready Parquet files. Every visualization in the
#   dashboard reads from these output files -- never from the raw data.
#
# INPUT FILES:
#   Data/2026-033-23_cns-logs.parquet   -- CNS Center website logs (16M rows)
#   Data/2026-01-13_hra-logs.parquet    -- HRA ecosystem logs (12.8M rows)
#
# OUTPUT FILES:
#   Data/processed/cns_clean.parquet         -- CNS logs, cleaned
#   Data/processed/hra_events.parquet        -- HRA event tracking rows only
#   Data/processed/hra_portal_cdn.parquet    -- HRA portal/CDN rows, meaningful files only
#   Data/processed/hra_full_traffic.parquet  -- Full HRA logs including bots (for AI trend)
#
# HOW TO RUN:
#   python preprocess.py
#
# NOTE:
#   Run this once before building any visualizations. It will take a few
#   minutes because the raw files are large (16M + 12.8M rows). After this
#   runs, all visualization scripts will be fast because they work on the
#   much smaller processed files.
# =============================================================================


# --- Standard library ---
import gc       # Garbage collector -- explicitly free memory between steps
import os       # Used to create output directories and check file paths

# --- Third-party libraries ---
import pandas as pd  # The core data manipulation library. A DataFrame is like
                     # an Excel spreadsheet in Python -- rows and columns.


# =============================================================================
# CONSTANTS
# Defining all fixed values here at the top means you only need to change one
# line if a file path or threshold changes. This is standard practice -- avoid
# "magic numbers/strings" scattered through the code.
# =============================================================================

# --- Input file paths ---
CNS_RAW_PATH = "Data/2026-033-23_cns-logs.parquet"
HRA_RAW_PATH = "Data/2026-01-13_hra-logs.parquet"

# --- Output directory ---
# All processed files go into a single folder so they are easy to find.
OUTPUT_DIR = "Data/processed"

# --- Output file paths ---
CNS_CLEAN_PATH       = os.path.join(OUTPUT_DIR, "cns_clean.parquet")
HRA_EVENTS_PATH      = os.path.join(OUTPUT_DIR, "hra_events.parquet")
HRA_PORTAL_CDN_PATH  = os.path.join(OUTPUT_DIR, "hra_portal_cdn.parquet")
HRA_FULL_PATH        = os.path.join(OUTPUT_DIR, "hra_full_traffic.parquet")

# --- Traffic type labels ---
# These are the exact string values that appear in the traffic_type column.
# Storing them as constants prevents typos later (e.g., "Likely human" vs
# "Likely Human" would silently filter everything out).
HUMAN_LABEL   = "Likely Human"
BOT_LABEL     = "Bot"
AI_BOT_LABEL  = "AI-Assistant / Bot"

# --- HRA site labels ---
# The HRA logs have a 'site' column that tells us which part of the platform
# a row came from. We use these to split the data.
SITE_EVENTS = "Events"   # Custom user interaction tracking -- our main focus
SITE_PORTAL = "Portal"   # The main humanatlas.io website
SITE_CDN    = "CDN"      # Static file delivery (JS, CSS, images, 3D models)
SITE_APPS   = "Apps"     # The HRA applications hub at apps.humanatlas.io
SITE_API    = "API"      # Backend API calls
SITE_KG     = "KG"       # Knowledge Graph

# --- Meaningful content types for file-level analysis ---
# The CDN rows contain a lot of noise: JavaScript bundles, CSS, fonts, icons.
# We only care about scientifically meaningful content. This list defines what
# counts as "meaningful" for the geographic file download analysis (MISC-1).
MEANINGFUL_CONTENT_TYPES = {
    "application/pdf",           # Publications and presentations
    "model/gltf+json",           # 3D organ/tissue models (text-based GLTF)
    "application/octet-stream",  # Binary 3D models (GLB format)
    "application/json",          # HRA datasets and API responses
    "text/html",                 # Portal and app pages
}

# --- Meaningful file extensions (second filter layer) ---
MEANINGFUL_EXTENSIONS = {".pdf", ".glb", ".gltf", ".json", ".csv", ".html"}

# --- CDN noise path prefixes to exclude (third filter layer) ---
# Paths starting with any of these are framework/build artifacts, not content.
NOISE_PATH_PREFIXES = ("/_next/", "/static/", "/chunks/", "/fonts/", "/icons/")

# --- Under-used element threshold for Q2 ---
# Any UI element with fewer than this many clicks is flagged as "under-used".
UNDER_USED_THRESHOLD = 5


# =============================================================================
# HELPER FUNCTIONS
# Small, reusable functions that each do one specific thing. Breaking logic
# into functions makes the code easier to read, test, and debug.
# =============================================================================

def extract_field(query_list, key):
    """
    Pull a single value out of the query column by its key.

    The 'query' column in the HRA logs is a list of (key, value) tuples, like:
        [("sessionId", "abc123"), ("app", "ccf-rui"), ("event", "click")]

    This function searches that list for a specific key and returns its value.
    If the key is not found (or the input is not a list), it returns None.

    Parameters
    ----------
    query_list : list or any
        The value from the 'query' column for one row.
    key : str
        The key to look for (e.g., "event", "app", "sessionId").

    Returns
    -------
    str or None
        The value associated with the key, or None if not found.

    Example
    -------
    query_list = [("app", "ccf-rui"), ("event", "click"), ("path", "rui.register")]
    extract_field(query_list, "app")    # returns "ccf-rui"
    extract_field(query_list, "missing") # returns None
    """
    if not isinstance(query_list, list):
        # Guard clause: if the column value is NaN or some other type,
        # skip it rather than crashing.
        return None
    for k, v in query_list:
        if k == key:
            return v
    return None


def extract_path(query_list):
    """
    Extract the UI element path from the query column, handling both old and
    new event schema versions.

    IMPORTANT: This is the single most critical function in the entire pipeline.
    Older events store the UI element path under the key 'e.path'.
    Newer events (version sv=0) store it under 'path'.
    If you only check one key, you silently undercount events -- sometimes by
    more than half.

    Strategy: check 'path' first (newer format). If not found, fall back to
    'e.path' (older format). If neither exists, return None.

    Parameters
    ----------
    query_list : list or any
        The value from the 'query' column for one row.

    Returns
    -------
    str or None
        The dot-notation UI element path, e.g. "rui.stage-content.register"

    Example
    -------
    Old event: [("e.path", "rui.register"), ("event", "click")]
    New event: [("path", "rui.register"), ("event", "click"), ("sv", "0")]
    Both return "rui.register".
    """
    if not isinstance(query_list, list):
        return None

    path_val  = None  # Will hold value of 'path' key if found
    epath_val = None  # Will hold value of 'e.path' key if found

    for k, v in query_list:
        if k == "path":
            path_val = v
        elif k == "e.path":
            epath_val = v

    # Prefer newer 'path' key; fall back to older 'e.path'
    return path_val if path_val is not None else epath_val


def extract_file_name(uri_stem):
    """
    Extract just the file name from a URL path.

    The cs_uri_stem column contains the full path like:
        /docs/publications/2022-Borner_Tissue-Registration-and-EUIs.pdf

    We want just:
        2022-Borner_Tissue-Registration-and-EUIs.pdf

    Parameters
    ----------
    uri_stem : str or any
        A URL path string from the cs_uri_stem column.

    Returns
    -------
    str or None
        The file name portion of the path.

    Example
    -------
    extract_file_name("/docs/publications/paper.pdf")  # returns "paper.pdf"
    extract_file_name("/")                              # returns "" (root)
    extract_file_name(float('nan'))                    # returns None
    """
    if not isinstance(uri_stem, str):
        return None
    # rsplit splits from the right on '/', limit 1 split, take the last piece
    return uri_stem.rsplit("/", 1)[-1]


def extract_file_extension(uri_stem):
    """
    Extract the file extension from a URL path for filtering purposes.

    Parameters
    ----------
    uri_stem : str or any
        A URL path string.

    Returns
    -------
    str
        Lowercase file extension including the dot (e.g. ".pdf"), or ""
        if there is no extension.

    Example
    -------
    extract_file_extension("/docs/paper.pdf")  # returns ".pdf"
    extract_file_extension("/about")           # returns ""
    """
    if not isinstance(uri_stem, str):
        return ""
    # os.path.splitext splits "paper.pdf" into ("paper", ".pdf")
    _, ext = os.path.splitext(uri_stem)
    return ext.lower()


def is_meaningful_file_mask(df):
    """
    Return a boolean Series identifying scientifically meaningful file rows.

    Vectorized replacement for the old row-by-row apply(is_meaningful_file).
    Applies three filter layers:
    1. Content type must be in MEANINGFUL_CONTENT_TYPES
    2. File extension must be in MEANINGFUL_EXTENSIONS
    3. URL path must NOT start with a known noise prefix

    Parameters
    ----------
    df : pd.DataFrame
        Must have 'sc_content_type', 'cs_uri_stem', and 'file_extension' cols.

    Returns
    -------
    pd.Series of bool
    """
    # Layer 1: content type (strip charset suffix, then check membership)
    content_type = df["sc_content_type"].astype(str).str.split(";").str[0].str.strip()
    mask = content_type.isin(MEANINGFUL_CONTENT_TYPES)

    # Layer 2: file extension
    mask &= df["file_extension"].isin(MEANINGFUL_EXTENSIONS)

    # Layer 3: exclude noise path prefixes
    uri = df["cs_uri_stem"].astype(str)
    noise_mask = uri.str.startswith(NOISE_PATH_PREFIXES[0])
    for prefix in NOISE_PATH_PREFIXES[1:]:
        noise_mask |= uri.str.startswith(prefix)
    mask &= ~noise_mask

    return mask


def normalize_columns(df):
    """
    Lowercase all column names to handle minor casing differences between
    the two datasets. For example, 'Traffic_Type' and 'traffic_type' both
    become 'traffic_type'.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        Same DataFrame with all column names lowercased.
    """
    df.columns = df.columns.str.lower().str.strip()
    return df


def parse_dates(df):
    """
    Parse the 'date' column into a proper datetime type, then derive two
    additional columns that are used heavily in time-series visualizations:
    - 'date_parsed' : a proper datetime object (e.g., 2025-01-05 00:00:00)
    - 'year_month'  : a Period object representing the month (e.g., 2025-01)

    The 'errors=coerce' argument means any row with an unparseable date gets
    NaT (Not a Time) instead of crashing the entire script.

    Parameters
    ----------
    df : pd.DataFrame
        Must have a 'date' column.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with two new columns added.
    """
    df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
    # to_period("M") converts a datetime to just year+month, e.g. 2025-01.
    # This makes monthly grouping very clean: df.groupby("year_month").
    df["year_month"]  = df["date_parsed"].dt.to_period("M")
    return df


# =============================================================================
# LOAD
# Read the raw Parquet files into DataFrames. Parquet is a compressed columnar
# format -- it loads much faster than CSV and uses less memory because pandas
# only decompresses the columns it needs.
# =============================================================================

def load_raw_data():
    """
    Load both raw Parquet files and normalize their column names.

    Returns
    -------
    tuple of (pd.DataFrame, pd.DataFrame)
        (cns, hra) -- the two raw datasets.
    """
    print("Loading CNS logs...")
    cns = pd.read_parquet(CNS_RAW_PATH)
    cns = normalize_columns(cns)
    print(f"  CNS loaded: {len(cns):,} rows, {len(cns.columns)} columns")

    print("Loading HRA logs...")
    hra = pd.read_parquet(HRA_RAW_PATH)
    hra = normalize_columns(hra)
    print(f"  HRA loaded: {len(hra):,} rows, {len(hra.columns)} columns")

    return cns, hra


# =============================================================================
# PROCESS: CNS LOGS
# Produces cns_clean.parquet -- human traffic only, with parsed dates and
# extracted file names. Used for: Q1 (traffic trends), MISC-1 (geography),
# MISC-2 (cache), MISC-3 (performance), MISC-4 (file size vs load time).
# =============================================================================

def process_cns(cns):
    """
    Clean and enrich the CNS website logs.

    Steps:
    1. Filter to human traffic only
    2. Parse dates
    3. Extract file name and extension from URL path
    4. Normalize content type (strip charset info)

    Parameters
    ----------
    cns : pd.DataFrame
        Raw CNS log data.

    Returns
    -------
    pd.DataFrame
        Cleaned CNS data, ready for analysis.
    """
    print("\nProcessing CNS logs...")
    initial_rows = len(cns)

    # Step 1: Keep only human traffic.
    # Bots and AI crawlers are excluded from all user behavior analysis.
    # We do this early so all subsequent operations work on a smaller dataset.
    cns_clean = cns[cns["traffic_type"] == HUMAN_LABEL].copy()
    # .copy() is important here -- it creates an independent copy rather than
    # a "view" of the original. Without it, pandas may raise a
    # SettingWithCopyWarning when we add new columns below.

    print(f"  Bot filter: {initial_rows:,} -> {len(cns_clean):,} rows "
          f"({len(cns_clean)/initial_rows*100:.1f}% human)")

    # Step 2: Parse dates and add year_month column.
    cns_clean = parse_dates(cns_clean)

    # Step 3: Extract file name from the URL path.
    # /docs/publications/paper.pdf -> paper.pdf
    cns_clean["file_name"] = cns_clean["cs_uri_stem"].apply(extract_file_name)

    # Step 4: Extract file extension for filtering.
    # /docs/publications/paper.pdf -> .pdf
    cns_clean["file_extension"] = cns_clean["cs_uri_stem"].apply(extract_file_extension)

    # Step 5: Normalize content type -- strip charset suffix.
    # "text/html; charset=utf-8" -> "text/html"
    cns_clean["content_type_clean"] = (
        cns_clean["sc_content_type"]
        .astype(str)
        .str.split(";")
        .str[0]
        .str.strip()
    )

    print(f"  CNS clean output: {len(cns_clean):,} rows")
    return cns_clean


# =============================================================================
# PROCESS: HRA FULL TRAFFIC
# Produces hra_full_traffic.parquet -- the complete HRA dataset with NO bot
# filter. This is intentional: the AI bot growth analysis (AQ3) needs to
# compare AI-bot share against total traffic, so we need all traffic types.
# =============================================================================

def process_hra_full(hra):
    """
    Minimal processing of the full HRA dataset (all traffic types retained).
    Only adds parsed dates and year_month. Used exclusively for AQ3 (AI bot
    growth trend analysis).

    Parameters
    ----------
    hra : pd.DataFrame
        Raw HRA log data.

    Returns
    -------
    pd.DataFrame
    """
    print("\nProcessing HRA full traffic (all traffic types, for AI trend)...")
    # Select only the columns needed for AQ3 to avoid copying the full DataFrame.
    cols_needed = ["date", "site", "traffic_type"]
    cols_present = [c for c in cols_needed if c in hra.columns]
    hra_full = hra[cols_present].copy()
    hra_full = parse_dates(hra_full)
    print(f"  HRA full output: {len(hra_full):,} rows")
    return hra_full


# =============================================================================
# PROCESS: HRA EVENTS
# Produces hra_events.parquet -- the 114K user interaction events with all
# query fields extracted into their own columns. This is the core dataset for
# Q1, Q2, Q3, Q4, Q5, AQ1, AQ2, AQ5.
# =============================================================================

def process_hra_events(hra):
    """
    Extract and enrich the HRA event tracking rows.

    The 'query' column contains everything encoded as a list of (key, value)
    tuples. This function unpacks all the important fields into proper columns
    so downstream code can filter and group without re-parsing the query list
    every time.

    Extracted fields:
    - event_type  : click, hover, pageView, keyboard, modelChange, error
    - app         : ccf-rui, ccf-eui, cde-ui, etc.
    - session_id  : groups all actions from one user session
    - path        : dot-notation UI element name (unified: path OR e.path)
    - version     : schema version (sv field), distinguishes old vs new events
    - page_url    : the page the user was on (from e.url, for pageView events)
    - event_value : the value set (from e.value, for modelChange events)

    Parameters
    ----------
    hra : pd.DataFrame
        Raw HRA log data (all sites).

    Returns
    -------
    pd.DataFrame
        Events-only rows with all query fields as columns.
    """
    print("\nProcessing HRA events...")

    # Step 1: Filter to human traffic only.
    hra_human = hra[hra["traffic_type"] == HUMAN_LABEL].copy()

    # Step 2: Filter to Events site only.
    # The 'site' column tells us which part of the HRA platform a row came
    # from. Only 'Events' rows contain user interaction data.
    events = hra_human[hra_human["site"] == SITE_EVENTS].copy()
    print(f"  Events rows (human): {len(events):,}")

    # Step 3: Parse dates.
    events = parse_dates(events)

    # Step 4: Extract individual fields from the query column.
    # We call apply() to run our helper function on every row.
    # This is the slow part -- apply() is a Python-level loop.
    # For 114K rows it is fast enough; for millions it would need optimization.
    print("  Extracting query fields (this may take a moment)...")

    events["event_type"]  = events["query"].apply(lambda q: extract_field(q, "event"))
    events["app"]         = events["query"].apply(lambda q: extract_field(q, "app"))
    # Note: the key in the data is 'sessionid' (lowercase) -- normalize it.
    events["session_id"]  = events["query"].apply(
        lambda q: extract_field(q, "sessionid") or extract_field(q, "sessionId")
    )
    events["version"]     = events["query"].apply(lambda q: extract_field(q, "sv"))
    events["page_url"]    = events["query"].apply(lambda q: extract_field(q, "e.url"))
    events["event_value"] = events["query"].apply(lambda q: extract_field(q, "e.value"))

    # Step 5: Extract UI element path using the unified extractor.
    # This MUST use extract_path() -- not extract_field(q, "path") -- because
    # it handles both old (e.path) and new (path) schema versions.
    events["path"] = events["query"].apply(extract_path)

    # Step 6: Report how many rows have null paths (informational).
    null_paths = events["path"].isna().sum()
    print(f"  Rows with no path value: {null_paths:,} "
          f"({null_paths/len(events)*100:.1f}%) -- expected for non-click events")

    # Step 7: Add app_prefix for grouping -- the first segment of the path.
    # "rui.stage-content.register" -> "rui"
    # "eui.body-ui.spatial-search-button" -> "eui"
    # This lets us group elements by app without knowing all app names in advance.
    events["app_prefix"] = events["path"].str.split(".").str[0]

    print(f"  HRA events output: {len(events):,} rows")

    # Step 8: Validate expected counts against known values from exploration.
    rui_count = (events["app"] == "ccf-rui").sum()
    print(f"  Validation -- RUI events: {rui_count:,} (expected ~9,430)")

    return events


# =============================================================================
# PROCESS: HRA PORTAL + CDN
# Produces hra_portal_cdn.parquet -- the HRA rows for Portal, CDN, and Apps
# sites, filtered to meaningful files only. Used for: MISC-1 (geography),
# MISC-2 (cache), MISC-3 (performance), MISC-4 (file size vs load time),
# MISC-5 (airport performance), AQ3 (geographic reach by portal).
# =============================================================================

def process_hra_portal_cdn(hra):
    """
    Filter and enrich the HRA non-events rows for infrastructure analysis.

    Keeps rows from Portal, CDN, and Apps sites (not Events, not API, not KG).
    Applies the three-layer meaningful file filter to remove CDN noise.
    Adds file name, extension, cleaned content type, and parsed dates.

    Parameters
    ----------
    hra : pd.DataFrame
        Raw HRA log data (all sites).

    Returns
    -------
    pd.DataFrame
    """
    print("\nProcessing HRA Portal + CDN rows...")

    # Step 1: Human traffic only.
    hra_human = hra[hra["traffic_type"] == HUMAN_LABEL].copy()

    # Step 2: Keep only Portal, CDN, and Apps rows.
    # Events and API rows are handled in separate output files.
    # KG is excluded -- it is less relevant for the visualization questions.
    target_sites = {SITE_PORTAL, SITE_CDN, SITE_APPS}
    portal_cdn = hra_human[hra_human["site"].isin(target_sites)].copy()
    print(f"  Portal + CDN + Apps rows: {len(portal_cdn):,}")

    # Step 3: Parse dates.
    portal_cdn = parse_dates(portal_cdn)

    # Step 4: Add file name and extension columns.
    portal_cdn["file_name"]      = portal_cdn["cs_uri_stem"].apply(extract_file_name)
    portal_cdn["file_extension"] = portal_cdn["cs_uri_stem"].apply(extract_file_extension)

    # Step 5: Normalize content type.
    portal_cdn["content_type_clean"] = (
        portal_cdn["sc_content_type"]
        .astype(str)
        .str.split(";")
        .str[0]
        .str.strip()
    )

    # Step 6: Apply the three-layer meaningful file filter.
    # We use apply() with axis=1 to pass each row as a Series to is_meaningful_file().
    # This is the correct way to filter on multiple columns simultaneously.
    print("  Applying meaningful file filter...")
    meaningful_mask = is_meaningful_file_mask(portal_cdn)
    portal_cdn_meaningful = portal_cdn[meaningful_mask].copy()

    print(f"  After meaningful file filter: {len(portal_cdn_meaningful):,} rows "
          f"({len(portal_cdn_meaningful)/len(portal_cdn)*100:.1f}% of Portal+CDN)")

    # Step 7: Infer app identity from the URL path prefix.
    # There is no dedicated 'app' column for these rows.
    # We approximate by checking cs_uri_stem path prefixes.
    # This is an accepted approximation -- flag it in the visualization notes.
    def infer_app(uri):
        if not isinstance(uri, str):
            return "unknown"
        if "/ccf-rui" in uri:
            return "rui"
        elif "/ccf-eui" in uri:
            return "eui"
        elif "/cde" in uri:
            return "cde"
        elif "/asctb" in uri:
            return "asctb"
        else:
            return "portal"

    portal_cdn_meaningful["inferred_app"] = portal_cdn_meaningful["cs_uri_stem"].apply(infer_app)

    print(f"  HRA portal+cdn output: {len(portal_cdn_meaningful):,} rows")
    return portal_cdn_meaningful


# =============================================================================
# SAVE
# Write processed DataFrames to Parquet files in the output directory.
# Parquet preserves column types (datetime, int, float) correctly, unlike CSV
# which converts everything to strings.
# =============================================================================

def save(df, path, label):
    """
    Save a DataFrame to a Parquet file.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to save.
    path : str
        Output file path.
    label : str
        Human-readable label for the print statement.
    """
    df.to_parquet(path, index=False)
    # index=False means the row numbers (0, 1, 2, ...) are NOT saved as a
    # column. They are meaningless here and would just waste space.
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"  Saved {label}: {len(df):,} rows -> {path} ({size_mb:.1f} MB)")


# =============================================================================
# MAIN
# Orchestrates the full pipeline. Running this file executes the steps below
# in order. Each step is independent -- if one fails, you can fix it and rerun
# without redoing the others (just comment out the completed steps).
# =============================================================================

def main():
    print("=" * 60)
    print("HRA Preprocessing Pipeline -- Team Crimson")
    print("=" * 60)

    # Create the output directory if it does not exist.
    # exist_ok=True means it will not raise an error if the folder is
    # already there -- safe to run multiple times.
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- CNS: load, process, save, free ---
    print("Loading CNS logs...")
    cns = pd.read_parquet(CNS_RAW_PATH)
    cns = normalize_columns(cns)
    print(f"  CNS loaded: {len(cns):,} rows, {len(cns.columns)} columns")

    cns_clean = process_cns(cns)
    del cns
    gc.collect()

    print("\nSaving processed files...")
    save(cns_clean, CNS_CLEAN_PATH, "CNS clean")
    del cns_clean
    gc.collect()

    # --- HRA: load, process all three outputs, save, free ---
    print("\nLoading HRA logs...")
    hra = pd.read_parquet(HRA_RAW_PATH)
    hra = normalize_columns(hra)
    print(f"  HRA loaded: {len(hra):,} rows, {len(hra.columns)} columns")

    hra_full = process_hra_full(hra)
    save(hra_full, HRA_FULL_PATH, "HRA full traffic")
    del hra_full
    gc.collect()

    hra_events = process_hra_events(hra)
    save(hra_events, HRA_EVENTS_PATH, "HRA events")
    del hra_events
    gc.collect()

    hra_portal_cdn = process_hra_portal_cdn(hra)
    save(hra_portal_cdn, HRA_PORTAL_CDN_PATH, "HRA portal+cdn")
    del hra_portal_cdn, hra
    gc.collect()

    # --- Summary ---
    print("\n" + "=" * 60)
    print("Preprocessing complete. Output files:")
    print(f"  {CNS_CLEAN_PATH}")
    print(f"  {HRA_EVENTS_PATH}")
    print(f"  {HRA_PORTAL_CDN_PATH}")
    print(f"  {HRA_FULL_PATH}")
    print("=" * 60)


# This is the standard Python entry point idiom.
# It means: only run main() if this file is executed directly (python preprocess.py).
# If this file is imported as a module by another script, main() will NOT run
# automatically -- only the functions and constants are imported.
if __name__ == "__main__":
    main()
