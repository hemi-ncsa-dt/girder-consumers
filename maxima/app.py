from openmsistream.girder.girder_upload_stream_processor import (
    GirderUploadStreamProcessor,
)

from common.base import extract_igsn, parse_date, run_uploader


class MaximaGirderUploader(GirderUploadStreamProcessor):
    def _process_downloaded_data_file(self, datafile, lock):
        metadata = {}
        if igsn := extract_igsn(datafile.full_filepath):
            metadata["igsn"] = igsn
        metadata.update(parse_date(str(datafile.full_filepath), self.logger))
        filename = datafile.full_filepath.name.lower()
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
        return self._GirderUploadStreamProcessor__process_downloaded_data_file(
            datafile, metadata=metadata or None
        )


def main():
    run_uploader(MaximaGirderUploader)


if __name__ == "__main__":
    main()
