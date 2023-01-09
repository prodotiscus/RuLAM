import nltk
from .glue_wrapper import RulLamGlueReadingCommand


def make_discourse_tester(sentences) -> nltk.DiscourseTester:
    rc = RulLamGlueReadingCommand()
    dt = nltk.DiscourseTester(sentences, rc)
    return dt
