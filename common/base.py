import os
import re

import dateutil.parser


igsn_pattern = re.compile(r"^[A-Z]{6}[0-9]{5}[A-Z0-9\-]*$", re.IGNORECASE)


def extract_igsn(filepath):
    """Find the first IGSN in any component of *filepath*.

    Tests the first underscore-delimited token of each path part, which
    handles both bare IGSN folder names and filenames/folder names like
    ``JHAMAL00004-01_abc_2026-04-15_...csv``.
    Returns the IGSN string (upper-cased) or ``None`` if not found.
    """
    for part in filepath.parts:
        try:
            candidate = part.split("--")[1]  # old HELIX osciloscope
        except IndexError:
            candidate = part
        candidate = candidate.split("_")[0]
        if igsn_pattern.match(candidate):
            return candidate.upper()
    return None


_date_time_pattern = re.compile(
    r"(?<![0-9])(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})(?![0-9])"
)


def parse_date(name, logger):
    """Parse experiment_date from a filename or folder name.

    Matches the first occurrence of YYYY-MM-DD_HH-MM-SS anywhere in *name*,
    regardless of how many underscore-delimited segments surround it.
    Examples that are handled correctly:
      - ``IGSN_a_b_c_2026-04-15_17-10-04``
      - ``JHAMAL00004-01_abc_1_894_2026-04-15_17-10-04_shot10_ch1.csv``
    """
    metadata = {}
    if m := _date_time_pattern.search(name):
        try:
            date, time = m.group(1), m.group(2)
            metadata["experiment_date"] = dateutil.parser.parse(
                f"{date} {time.replace('-', ':')}+00:00"
            ).isoformat()
        except Exception as exc:
            msg = f"Error parsing date and time from '{name}': {exc}"
            logger.error(msg, exc_info=exc)
    return metadata


def run_uploader(cls, **extra_kwargs):
    """Instantiate *cls* from environment variables and run until complete."""
    girder_api_url = os.getenv("GIRDER_API_URL")
    girder_api_key = os.getenv("GIRDER_API_KEY")
    girder_folder_id = os.getenv("GIRDER_FOLDER_ID")
    config_file = os.getenv("CONFIG_FILE")
    mode = os.getenv("MODE", "disk")
    topic_name = os.getenv("TOPIC_NAME")
    heartbeat_topic_name = os.getenv("HEARTBEAT_TOPIC_NAME")
    heartbeat_program_id = os.getenv("HEARTBEAT_PROGRAM_ID")

    uploader = cls(
        girder_api_url,
        girder_api_key,
        config_file,
        topic_name,
        girder_root_folder_id=girder_folder_id,
        heartbeat_topic_name=heartbeat_topic_name,
        heartbeat_program_id=heartbeat_program_id,
        heartbeat_interval_secs=120,
        mode=mode,
        **extra_kwargs,
    )
    uploader.logger.info(
        f"Listening to the {topic_name} topic for files to upload to "
        f"Girder using the API at {girder_api_url}"
    )
    (
        n_read,
        n_msgs_procd,
        n_files_procd,
        procd_fps,
    ) = uploader.process_files_as_read()
    uploader.close()
    uploader.logger.info("Girder upload stream processor shut down")
    uploader.logger.info(
        f"{n_read} total messages were consumed, {n_msgs_procd} messages were "
        f"successfully processed, and {n_files_procd} files were uploaded "
        f"to Girder"
    )


# --- tabular content sniffing -------------------------------------------------

_TABULAR_SUFFIXES = (".csv", ".xls", ".xlsx")

# Strip parenthesised unit annotations, then squash anything that isn't
# alphanumeric into single underscores: "Flyer_Thickness (um)" -> "flyer_thickness",
# "PDV_10_FileName" -> "pdv_10_filename", "Sample material" -> "sample_material".
_units_pattern = re.compile(r"\([^)]*\)")
_non_alnum_pattern = re.compile(r"[^0-9a-z]+")


def normalize_column(name):
    """Return a canonical, comparable form of a spreadsheet column name."""
    name = _units_pattern.sub(" ", str(name).lower())
    return _non_alnum_pattern.sub("_", name).strip("_")


def read_table_columns(filepath, logger=None):
    """Return the normalized column names of a tabular file, or ``None``.

    Only the header row is parsed, so this is cheap regardless of file size.
    ``None`` means "not a tabular file, or unreadable" - both of which simply
    mean "no content-based data_type".
    """
    suffix = filepath.suffix.lower()
    if suffix not in _TABULAR_SUFFIXES:
        return None
    import pandas as pd  # local: only helix-otherdata depends on pandas

    try:
        reader = pd.read_csv if suffix == ".csv" else pd.read_excel
        return [normalize_column(col) for col in reader(filepath, nrows=0).columns]
    except Exception as exc:
        if logger is not None:
            msg = f"Could not read header of '{filepath}': {exc}"
            logger.error(msg, exc_info=exc)
        return None


# Content signatures, most specific first. Each entry is
# ``(data_type, (required_group, ...))`` and matches when *every* group has at
# least one column whose normalized name fully matches the group's pattern.
# Adding support for a new spreadsheet generation should be a matter of
# loosening a pattern here rather than editing a consumer.
COLUMN_SIGNATURES = (
    (
        "pdv_experiment_log",
        (
            r"sample_(igsn|id)",
            # single-probe logs use PDV_FileName; multi-probe (MPDV) logs use
            # per-channel PDV_<n>_FileName columns.
            r"pdv(_\d+)?_file_?name",
        ),
    ),
)

_compiled_signatures = tuple(
    (data_type, tuple(re.compile(p) for p in patterns))
    for data_type, patterns in COLUMN_SIGNATURES
)


def detect_data_type(filepath, logger=None):
    """Classify a tabular file by its columns. Returns a data_type or ``None``."""
    columns = read_table_columns(filepath, logger)
    if not columns:
        return None
    for data_type, patterns in _compiled_signatures:
        if all(any(p.fullmatch(col) for col in columns) for p in patterns):
            return data_type
    return None
