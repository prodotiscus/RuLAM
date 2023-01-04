import requests
import typing as tp

"""
Simple but slow web-interaction to UDPipe REST API
UDPipe REST API Reference: https://lindat.mff.cuni.cz/services/udpipe/api-reference.php
CoNLL-U Format: http://universaldependencies.org/docs/format.html
"""

class WebUDPipeProcessorError(Exception):
    pass


REST_API_URL = "http://lindat.mff.cuni.cz/services/udpipe/api/process"


def request_udpipe_processing(text: str) -> tp.Dict[str, tp.Any]:
    req = requests.post(REST_API_URL, data = {
        "model": "russian",
        "tokenizer": 1,
        "tagger": 1,
        "parser": 1,
        "data": text
    })
    return req.json()


def web_udpipe_process_text_conllu(text: str) -> str:
    try:
        json_result = request_udpipe_processing(text)
    except requests.exceptions.ConnectionError:
        raise WebUDPipeProcessorError
    text_with_comments = json_result["result"]
    return "\n".join(
        line for line in text_with_comments.splitlines() if not line.startswith("#")
    )


# TODO: type description should be more obvious
DictParsedConllu = tp.List[tp.Dict[str, str]]


# TODO: list and dict comprehensions are unreadable
def postprocess_conllu(conllu: str) -> DictParsedConllu:
    fields = "ID FORM LEMMA UPOSTAG XPOSTAG FEATS HEAD DEPREL DEPS MISC".split()
    return [
        {
            fields[e]: (
                field_content if fields[e] not in ("ID", "HEAD") else int(field_content)
            )
            for (e, field_content) in enumerate(line.split("\t"))
        }
        for line in conllu.splitlines()
    ]


def parse_text(text: str) -> DictParsedConllu:
    return postprocess_conllu(
        web_udpipe_process_text_conllu(text)
    )


if __name__ == "__main__":
    res = parse_text("Я пошёл домой.")
    print(res)
