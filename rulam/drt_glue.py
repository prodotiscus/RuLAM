import nltk
from nltk.sem import drt, linearlogic
from nltk.parse.dependencygraph import DependencyGraph
from .web_udpipe_processor import web_udpipe_process_text_conllu
from .glue import RuLamGlueDict, GlueFormula


class DrtRuLamGlueDict(RuLamGlueDict):
    def get_GlueFormula_factory(self):
        return DrtGlueFormula


class DrtGlueFormula(GlueFormula):
    def __init__(self, meaning, glue, indices=None):
        if not indices:
            indices = set()

        if isinstance(meaning, str):
            self.meaning = drt.DrtExpression.fromstring(meaning)
        elif isinstance(meaning, drt.DrtExpression):
            self.meaning = meaning
        else:
            raise RuntimeError(
                "Meaning term neither string or expression: %s, %s"
                % (meaning, meaning.__class__)
            )

        if isinstance(glue, str):
            self.glue = linearlogic.LinearLogicParser().parse(glue)
        elif isinstance(glue, linearlogic.Expression):
            self.glue = glue
        else:
            raise RuntimeError(
                "Glue term neither string or expression: %s, %s"
                % (glue, glue.__class__)
            )

        self.indices = indices

    def make_VariableExpression(self, name):
        return drt.DrtVariableExpression(name)

    def make_LambdaExpression(self, variable, term):
        return drt.DrtLambdaExpression(variable, term)


class RuLamDrtGlue(nltk.sem.glue.Glue):
    def __init__(
        self, semtype_file=None, remove_duplicates=False, depparser=None, verbose=False
    ):
        nltk.sem.glue.Glue.__init__(self, semtype_file, remove_duplicates, depparser, verbose)

    def get_glue_dict(self):
        return DrtRuLamGlueDict(self.semtype_file)
    
    def dep_parse(self, sentence):
        """
        Return a dependency graph for the sentence.

        :param sentence: the sentence to be parsed
        :type sentence: list(str)
        :rtype: DependencyGraph
        """

        # TODO(sfedia): make better udpipe integration
        web_result = web_udpipe_process_text_conllu(sentence)
        depgraph = DependencyGraph(web_result)
        return [depgraph]
