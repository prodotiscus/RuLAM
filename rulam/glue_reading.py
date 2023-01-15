import nltk
from functools import reduce
from operator import add
from .drt_glue import RuLamDrtGlue
from .anaphora_resolution import resolve_anaphora


BASIC_GRAMMAR_FILENAME = "basic_rules.semtype"


class RuLamGlueReadingCommand(nltk.inference.discourse.ReadingCommand):
    def __init__(self, semtype_file=None, remove_duplicates=False, depparser=None):
        """
        :param semtype_file: name of file where grammar can be loaded
        :param remove_duplicates: should duplicates be removed?
        :param depparser: the dependency parser
        """
        if semtype_file is None:
            semtype_file = BASIC_GRAMMAR_FILENAME
        self._glue = RuLamDrtGlue(
            semtype_file=semtype_file,
            remove_duplicates=remove_duplicates,
            depparser=depparser,
        )

    def parse_to_readings(self, sentence):
        """:see: ReadingCommand.parse_to_readings()"""
        return self._glue.parse_to_meaning(sentence)

    def process_thread(self, sentence_readings):
        """:see: ReadingCommand.process_thread()"""
        return [self.combine_readings(sentence_readings)]
        # try:
        #     return [self.combine_readings(sentence_readings)]
        # except nltk.sem.drt.AnaphoraResolutionException:
        #     return []

    def combine_readings(self, readings):
        """:see: ReadingCommand.combine_readings()"""
        thread_reading = reduce(add, readings)
        return resolve_anaphora(thread_reading.simplify())

    def to_fol(self, expression):
        """:see: ReadingCommand.to_fol()"""
        return expression.fol()
