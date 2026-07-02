from openmsistream.girder.girder_upload_stream_processor import (
    GirderUploadStreamProcessor,
)

from common.base import run_uploader


def main():
    run_uploader(GirderUploadStreamProcessor)


if __name__ == "__main__":
    main()
