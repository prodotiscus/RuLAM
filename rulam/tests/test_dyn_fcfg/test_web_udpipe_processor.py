import pytest
import requests

import sys
import os
# TODO: makes test suite able to import submodules, but the solution looks lame
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../.."))

from dyn_fcfg import web_udpipe_processor


def test_request_udpipe_processing_connection_error(mocker):
    mocker.patch("requests.post", side_effect=requests.exceptions.ConnectionError)
    with pytest.raises(web_udpipe_processor.WebUDPipeProcessorError) as proc_err:
        web_udpipe_processor.web_udpipe_process_text_conllu("Я иду в лес.")
        assert str(proc_err) == "Failed to establish connection to the server."


def test_request_udpipe_processing_non_json_value(mocker):
    mocker.patch("requests.Response.json", side_effect=requests.exceptions.JSONDecodeError("a", "b", 1))
    with pytest.raises(web_udpipe_processor.WebUDPipeProcessorError) as proc_err:
        web_udpipe_processor.web_udpipe_process_text_conllu("Я иду в лес.")
        assert str(proc_err) == "Server has produced non-JSON value."


def test_request_udpipe_processing_invalid_json_value(mocker):
    mocker.patch("requests.Response.json", return_value={"error": "something"})
    with pytest.raises(web_udpipe_processor.WebUDPipeProcessorError) as proc_err:
        web_udpipe_processor.web_udpipe_process_text_conllu("Я иду в лес.")
        assert str(proc_err) == "Server has produced invalid JSON value."


@pytest.mark.parametrize(
    "input_text, output",
    [
        (
            "Я иду домой.", [[
            {
                "ID": 1,
                "FORM": "Я",
                "LEMMA": "я",
                "UPOSTAG": "PRON",
                "XPOSTAG": "_",
                "FEATS": "Case=Nom|Number=Sing|Person=1",
                "HEAD": 2,
                "DEPREL": "nsubj",
                "DEPS": "_",
                "MISC": "_"
            },
            {
                "ID": 2,
                "FORM": "иду",
                "LEMMA": "идти",
                "UPOSTAG": "VERB",
                "XPOSTAG": "_",
                "FEATS": "Aspect=Imp|Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin|Voice=Act",
                "HEAD": 0,
                "DEPREL": "root",
                "DEPS": "_",
                "MISC": "_"
            },
            {
                "ID": 3,
                "FORM": "домой",
                "LEMMA": "домой",
                "UPOSTAG": "ADV",
                "XPOSTAG": "_",
                "FEATS": "Degree=Pos",
                "HEAD": 2,
                "DEPREL": "advmod",
                "DEPS": "_",
                "MISC": "SpaceAfter=No"
            },
            {
                "ID": 4,
                "FORM": ".",
                "LEMMA": ".",
                "UPOSTAG": "PUNCT",
                "XPOSTAG": "_",
                "FEATS": "_",
                "HEAD": 2,
                "DEPREL": "punct",
                "DEPS": "_",
                "MISC": "SpaceAfter=No"
            }
        ]]),
        ("Сначала один. Потом другой.", [
        [
            {
                "ID": 1,
                "FORM": "Сначала",
                "LEMMA": "сначала",
                "UPOSTAG": "ADV",
                "XPOSTAG": "_",
                "FEATS": "Degree=Pos",
                "HEAD": 2,
                "DEPREL": "advmod",
                "DEPS": "_",
                "MISC": "_"
            },
            {
                "ID": 2,
                "FORM": "один",
                "LEMMA": "один",
                "UPOSTAG": "DET",
                "XPOSTAG": "_",
                "FEATS": "Case=Nom|Gender=Masc|Number=Sing|PronType=Ind",
                "HEAD": 0,
                "DEPREL": "root",
                "DEPS": "_",
                "MISC": "SpaceAfter=No"
            },
            {
                "ID": 3,
                "FORM": ".",
                "LEMMA": ".",
                "UPOSTAG": "PUNCT",
                "XPOSTAG": "_",
                "FEATS": "_",
                "HEAD": 2,
                "DEPREL": "punct",
                "DEPS": "_",
                "MISC": "_"
            }
        ],
        [
            {
                "ID": 1,
                "FORM": "Потом",
                "LEMMA": "потом",
                "UPOSTAG": "ADV",
                "XPOSTAG": "_",
                "FEATS": "Degree=Pos",
                "HEAD": 2,
                "DEPREL": "advmod",
                "DEPS": "_",
                "MISC": "_"
            },
            {
                "ID": 2,
                "FORM": "другой",
                "LEMMA": "другой",
                "UPOSTAG": "ADJ",
                "XPOSTAG": "_",
                "FEATS": "Case=Nom|Degree=Pos|Gender=Masc|Number=Sing",
                "HEAD": 0,
                "DEPREL": "root",
                "DEPS": "_",
                "MISC": "SpaceAfter=No"
            },
            {
                "ID": 3,
                "FORM": ".",
                "LEMMA": ".",
                "UPOSTAG": "PUNCT",
                "XPOSTAG": "_",
                "FEATS": "_",
                "HEAD": 2,
                "DEPREL": "punct",
                "DEPS": "_",
                "MISC": "SpaceAfter=No"
            }
        ]
    ])
])
def test_parse_text(input_text, output):
    result = web_udpipe_processor.parse_text(input_text)
    assert result == output


@pytest.mark.parametrize("value", ["", "  ", " \t "])
def test_parse_text_with_empty_value(value):
    with pytest.raises(web_udpipe_processor.WebUDPipeProcessorError) as proc_error:
        web_udpipe_processor.parse_text(value)
        assert str(proc_error) == "Empty value"
