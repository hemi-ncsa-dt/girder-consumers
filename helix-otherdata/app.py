import os

from openmsistream.girder.girder_upload_stream_processor import (
    GirderUploadStreamProcessor,
)

from common.base import detect_data_type, extract_igsn, parse_date, run_uploader


class HelixOtherDataGirderUploader(GirderUploadStreamProcessor):
    def _process_downloaded_data_file(self, datafile, lock):
        metadata = {}
        if igsn := extract_igsn(datafile.full_filepath):
            metadata["igsn"] = igsn
        metadata.update(parse_date(str(datafile.full_filepath), self.logger))
        if data_type := detect_data_type(datafile.full_filepath, self.logger):
            metadata["data_type"] = data_type
        return self._GirderUploadStreamProcessor__process_downloaded_data_file(
            datafile, metadata=metadata or None
        )


def main():
    replace_existing = os.getenv("REPLACE_EXISTING", "true").lower() == "true"
    run_uploader(HelixOtherDataGirderUploader, replace_existing=replace_existing)


if __name__ == "__main__":
    main()
