import os
import re
from openmsistream.girder.girder_upload_stream_processor import (
    GirderUploadStreamProcessor,
)

igsn_pattern = re.compile(r"^[A-Z]{6}[0-9]{5}[A-Z0-9\-]*$", re.IGNORECASE)


class MaximaGirderUploader(GirderUploadStreamProcessor):
    def _process_downloaded_data_file(self, datafile, lock):
        metadata = {}
        parts = datafile.full_filepath.parts
        filename = datafile.full_filepath.name
        try:
            target_index = parts.index("automatic_mode") + 1
            result = parts[target_index]
            igsn = result.split("_")[0].upper()
            if filename == "instructions.txt":
                metadata["data_type"] = "xrd_metadata"
            elif filename.endswith(".h5"):
                if filename.startswith("xrd_calibrant"):
                    metadata["data_type"] = "xrd_calibrant_raw"
                else:
                    metadata["data_type"] = "xrd_raw"
            elif filename.endswith(".tif") or filename.endswith(".tiff"):
                metadata["data_type"] = "xrd_derived"
            elif filename.endswith(".xrf"):
                metadata["data_type"] = "xrf_raw"
            if igsn_pattern.match(igsn):
                metadata["igsn"] = igsn
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

    girder_uploader = MaximaGirderUploader(
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
    # start the processor running
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
    # shut down when that function returns
    girder_uploader.close()
    msg = "Girder upload stream processor "
    msg += "shut down"
    girder_uploader.logger.info(msg)
    msg = (
        f"{n_read} total messages were consumed, {n_msgs_procd} messages were "
        f"successfully processed, and {n_files_procd} files were uploaded "
        f"to Girder"
    )
    girder_uploader.logger.info(msg)


if __name__ == "__main__":
    main()
