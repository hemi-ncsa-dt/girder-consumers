import os

from openmsistream.girder.girder_upload_stream_processor import (
    GirderUploadStreamProcessor,
)

from common.base import extract_igsn, parse_date, run_uploader


class SphinxGirderUploader(GirderUploadStreamProcessor):
    def _process_downloaded_data_file(self, datafile, lock):
        metadata = {}
        if datafile.full_filepath.suffix.upper() == ".NMD":
            metadata["data_type"] = "nmd_raw"
        if datafile.full_filepath.suffix.upper() == ".NMPROJ":
            metadata["data_type"] = "nmd_project"
        if igsn := extract_igsn(datafile.full_filepath):
            metadata["igsn"] = igsn
        metadata.update(parse_date(str(datafile.full_filepath), self.logger))

        return self._GirderUploadStreamProcessor__process_downloaded_data_file(
            datafile, metadata=metadata or None
        )


def main():
    replace_existing = os.getenv("REPLACE_EXISTING", "true").lower() == "true"
    run_uploader(SphinxGirderUploader, replace_existing=replace_existing)


if __name__ == "__main__":
    main()
