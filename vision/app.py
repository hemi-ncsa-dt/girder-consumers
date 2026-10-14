from openmsistream.girder.girder_upload_stream_processor import (
    GirderUploadStreamProcessor,
)

from common.base import extract_igsn, parse_date, run_uploader


class VisionGirderUploader(GirderUploadStreamProcessor):
    def _process_downloaded_data_file(self, datafile, lock):
        metadata = {"data_type": "vision_data"}
        # IGSN comes from the folder(s) the file sits in, not the file name
        if igsn := extract_igsn(datafile.full_filepath.parent):
            metadata["igsn"] = igsn
        metadata.update(parse_date(str(datafile.full_filepath), self.logger))
        return self._GirderUploadStreamProcessor__process_downloaded_data_file(
            datafile, metadata=metadata
        )


def main():
    run_uploader(VisionGirderUploader)


if __name__ == "__main__":
    main()
