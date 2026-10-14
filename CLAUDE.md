# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

One Dockerized Kafka→Girder uploader per AIMD-L instrument (`helix`, `helix-otherdata`, `maxima`, `sphinx`, `profilometry`). Each consumer is a single `<instrument>/app.py` built on OpenMSIStream's `GirderUploadStreamProcessor`: it consumes file chunks from a Kafka topic, reassembles them, and uploads them to Girder with metadata attached. Shared code lives in `common/base.py`.

There are no tests, linters, or packaging config. The only automated check is the Docker build in CI.

## Build and run

Images must be built from the **repo root** (the Dockerfiles `COPY common/` and `<instrument>/app.py`):

```bash
docker build -f sphinx/Dockerfile -t sphinx-consumer .
```

To run locally without Docker, run from the repo root so `common` is importable: `pip install -r sphinx/requirements.txt && PYTHONPATH=. python sphinx/app.py`.

Runtime configuration comes entirely from environment variables, read in `common.base.run_uploader`: `GIRDER_API_URL`, `GIRDER_API_KEY`, `GIRDER_FOLDER_ID`, `CONFIG_FILE` (OpenMSIStream/Kafka config), `TOPIC_NAME`, `MODE` (default `disk`), `HEARTBEAT_TOPIC_NAME`, `HEARTBEAT_PROGRAM_ID`. `sphinx` and `helix-otherdata` also read `REPLACE_EXISTING` (default `true`).

## Consumer pattern

Every instrument-specific consumer follows the same shape:

1. Subclass `GirderUploadStreamProcessor` and override `_process_downloaded_data_file(self, datafile, lock)`.
2. Build a `metadata` dict: `igsn` via `extract_igsn(datafile.full_filepath)`, `experiment_date` via `parse_date(...)`, and an instrument-specific `data_type` chosen from the file name or extension (for example `pdv_trace`, `xrd_raw`, `nmd_raw`).
3. Delegate to the name-mangled parent method `self._GirderUploadStreamProcessor__process_downloaded_data_file(datafile, metadata=metadata or None)`.
4. `main()` calls `run_uploader(Cls, **extra_kwargs)`, which builds the processor from env vars and runs `process_files_as_read()`.

`profilometry` uses the base class unchanged (no metadata). `helix-otherdata` does not pick `data_type` by file name. It calls `detect_data_type`, which classifies the file by its spreadsheet columns.

`data_type` and `igsn` values are consumed downstream (Dagster pipelines and Girder dashboards key on them), so treat renaming them as a breaking change.

### Shared helpers (`common/base.py`)

- `extract_igsn`: scans each path component and tests the first `_`-delimited token against `^[A-Z]{6}[0-9]{5}[A-Z0-9-]*$`. It also handles the old HELIX oscilloscope naming, where the IGSN follows `--`. Returns the IGSN upper-cased.
- `parse_date`: finds the first `YYYY-MM-DD_HH-MM-SS` in the name and stores it as a UTC ISO timestamp.
- `detect_data_type`: reads only the header row of a `.csv`/`.xls`/`.xlsx` file and normalizes the column names (lower-cased, unit annotations removed, separators turned into `_`). It then matches them against `COLUMN_SIGNATURES`. Each signature is `(data_type, (pattern, ...))` and applies when every pattern fully matches at least one column. To support a new spreadsheet layout, add or loosen a signature here instead of changing a consumer. `pandas` is imported lazily, so only consumers that call this function need it in their `requirements.txt`.

## Adding a consumer

Create `<name>/app.py`, `<name>/requirements.txt` (at minimum `openmsistream>=1.8.7`, `python-dateutil`, `kafka-python<3`), and `<name>/Dockerfile` by copying an existing one and replacing the folder name. The Dockerfiles are identical apart from that name. CI discovers services automatically.

## CI

`.github/workflows/docker-build.yml` builds only the services whose top-level folder changed. A change under `common/` rebuilds every service. Pushes to `main` publish `docker.io/xarthisius/<service>-consumer:latest`. PRs build but do not push.

## Conventions

- `kafka-python` is pinned `<3` in every `requirements.txt`. Keep the pin when adding consumers.
- Commit messages are a single short line, with no `Co-Authored-By: Claude` trailer.
