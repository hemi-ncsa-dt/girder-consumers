import os
import re

import pandas as pd
from openmsistream.girder.girder_upload_stream_processor import (
    GirderUploadStreamProcessor,
)

igsn_pattern = re.compile(r"^[A-Z]{6}[0-9]{5}[A-Z0-9\-]*$", re.IGNORECASE)


class HelixOtherDataGirderUploader(GirderUploadStreamProcessor):
    def _process_downloaded_data_file(self, datafile, lock):
        metadata = {}
        try:
            for part in datafile.full_filepath.parts:
                if igsn := igsn_pattern.match(part):
                    metadata["igsn"] = igsn.group(0).upper()
                    break
            suffix = datafile.full_filepath.suffix.lower()
            df = None
            if suffix == ".csv":
                df = pd.read_csv(datafile.full_filepath)
            elif suffix in [".xls", ".xlsx"]:
                df = pd.read_excel(datafile.full_filepath)

            if df is not None:
                if "Sample_IGSN" in df.columns and "PDF_FileName" in df.columns:
                    metadata["data_type"] = "pdv_experiment_log"
        except Exception as exc:
            msg = f"Error processing file path for metadata extraction: {exc}"
            self.logger.error(msg, exc_info=exc)
            pass
        return self._GirderUploadStreamProcessor__process_downloaded_data_file(
            datafile, metadata=metadata or None
        )


def main():
    girder_api_url = os.getenv("GIRDER_API_URL")
    girder_api_key = os.getenv("GIRDER_API_KEY")
    girder_folder_id = os.getenv("GIRDER_FOLDER_ID")
    config_file = os.getenv("CONFIG_FILE")
    mode = os.getenv("MODE", "disk")
    topic_name = os.getenv("TOPIC_NAME")
    heartbeat_topic_name = os.getenv("HEARTBEAT_TOPIC_NAME")
    heartbeat_program_id = os.getenv("HEARTBEAT_PROGRAM_ID")

    girder_uploader = HelixOtherDataGirderUploader(
        girder_api_url,
        girder_api_key,
        config_file,
        topic_name,
        girder_root_folder_id=girder_folder_id,
        heartbeat_topic_name=heartbeat_topic_name,
        heartbeat_program_id=heartbeat_program_id,
        heartbeat_interval_secs=120,
        mode=mode,
    )
    msg = (
        f"Listening to the {topic_name} topic for files to upload to "
        f"Girder using the API at {girder_api_url}"
    )
    girder_uploader.logger.info(msg)
    (
        n_read,
        n_msgs_procd,
        n_files_procd,
        procd_fps,
    ) = girder_uploader.process_files_as_read()
    girder_uploader.close()
    msg = "Girder upload stream processor shut down"
    girder_uploader.logger.info(msg)
    msg = (
        f"{n_read} total messages were consumed, {n_msgs_procd} messages were "
        f"successfully processed, and {n_files_procd} files were uploaded "
        f"to Girder"
    )
    girder_uploader.logger.info(msg)


if __name__ == "__main__":
    main()
