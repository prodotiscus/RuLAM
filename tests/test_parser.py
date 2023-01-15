import pytest
import requests

import sys
import os
# TODO(sfedia): makes test suite able to import submodules, but the solution looks lame
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../.."))

import rulam


def test_get_parser_default_integration_type():
    parser = rulam.parser.get_parser(["Заяц бежит", "Он серый"])
    parser.readings(show_thread_readings=True, filter=True)


def test_get_parser_web_udpipe_integration_type():
    parser = rulam.parser.get_parser(["Заяц бежит", "Он серый"], rulam.parser.IntegrationTypes.WEB_UDPIPE_GLUE)
    parser.readings(show_thread_readings=True, filter=True)


def test_get_parser_local_udpipe_integration_type():
    with pytest.raises(NotImplementedError) as not_implemented_error:
        rulam.parser.get_parser(["Заяц бежит", "Он серый"], rulam.parser.IntegrationTypes.LOCAL_UDPIPE_GLUE)
        assert str(not_implemented_error) == "Local UDPipe integration is not yet available."
