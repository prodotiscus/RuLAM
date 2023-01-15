import nltk
from .glue_reading import RuLamGlueReadingCommand


def make_discourse_tester(sentences) -> nltk.DiscourseTester:
    rc = RuLamGlueReadingCommand()
    dt = nltk.DiscourseTester(sentences, rc)
    return dt
