
from vcr import VCR


vcr = VCR(
    cassette_library_dir = "cassettes", filter_query_parameters = ["key"]
)

