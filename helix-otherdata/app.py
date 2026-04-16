import os

import pandas as pd
from openmsistream.girder.girder_upload_stream_processor import (
    GirderUploadStreamProcessor,
)

from common.base import extract_igsn, parse_date, run_uploader


class HelixOtherDataGirderUploader(GirderUploadStreamProcessor):
    def _process_downloaded_data_file(self, datafile, lock):
        metadata = {}
        if igsn := extract_igsn(datafile.full_filepath):
            metadata["igsn"] = igsn
        metadata.update(parse_date(str(datafile.full_filepath), self.logger))
        try:
            suffix = datafile.full_filepath.suffix.lower()
            df = None
            if suffix == ".csv":
                df = pd.read_csv(datafile.full_filepath)
            elif suffix in [".xls", ".xlsx"]:
                df = pd.read_excel(datafile.full_filepath)

            if df is not None:
                if (
                    "Sample_IGSN" in df.columns or "Sample_ID" in df.columns
                ) and "PDV_FileName" in df.columns:
                    metadata["data_type"] = "pdv_experiment_log"
        except Exception as exc:
            msg = f"Error processing file path for metadata extraction: {exc}"
            self.logger.error(msg, exc_info=exc)
            pass
        return self._GirderUploadStreamProcessor__process_downloaded_data_file(
            datafile, metadata=metadata or None
        )


def main():
    replace_existing = os.getenv("REPLACE_EXISTING", "true").lower() == "true"
    run_uploader(HelixOtherDataGirderUploader, replace_existing=replace_existing)


if __name__ == "__main__":
    main()
