import json

import sys
import os

# TODO: makes test suite able to import submodules, but the solution looks lame
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../.."))
from dyn_fcfg import web_udpipe_processor


def pretty_print(dct) -> str:
    print(json.dumps(dct, indent=4, ensure_ascii=False))


def print_web_udpipe_processor_result(text):
    pretty_print(web_udpipe_processor.parse_text(text))
