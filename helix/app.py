from openmsistream.girder.girder_upload_stream_processor import (
    GirderUploadStreamProcessor,
)

from common.base import extract_igsn, parse_date, run_uploader


class HelixGirderUploader(GirderUploadStreamProcessor):
    def _process_downloaded_data_file(self, datafile, lock):
        metadata = {}
        if datafile.full_filepath.suffix.lower() == ".csv":
            metadata["data_type"] = "pdv_trace"
        if igsn := extract_igsn(datafile.full_filepath):
            metadata["igsn"] = igsn
        metadata.update(parse_date(str(datafile.full_filepath), self.logger))

        return self._GirderUploadStreamProcessor__process_downloaded_data_file(
            datafile, metadata=metadata or None
        )


def main():
    run_uploader(HelixGirderUploader)


if __name__ == "__main__":
    main()
