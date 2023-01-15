import os
from itertools import chain

import nltk
from nltk.internals import Counter
from nltk.sem import drt, linearlogic
from nltk.sem.logic import (
    AbstractVariableExpression,
    Expression,
    LambdaExpression,
    Variable,
    VariableExpression,
)
from nltk.parse.dependencygraph import DependencyGraph
from .web_udpipe_processor import web_udpipe_process_text_conllu
from functools import reduce
from operator import add
import os
from nltk.sem.logic import (
    AbstractVariableExpression,
    ApplicationExpression,
    BinaryExpression,
    EqualityExpression,
    Expression,
    LambdaExpression,
    NegatedExpression,
    Variable,
)
from .symbolizer import SimplestSymbolizer
import re


OPTIONAL_RELATIONSHIPS = ["nmod", "vmod", "punct"]
BASIC_GRAMMAR_FILENAME = "basic_rules.semtype"

class RuLamGlueDict(dict):
    def __init__(self, filename, encoding=None):
        self.filename = filename
        self.file_encoding = encoding
        self.read_file()

    def read_file(self, empty_first=True):
        if empty_first:
            self.clear()
        
        contents = open(
            os.path.abspath(os.path.join("rulam", "grammars", self.filename)),
            encoding=self.file_encoding
        ).read()

        lines = contents.splitlines()

        for line in lines:  # example: 'n : (\\x.(<word> x), (v-or))'
            #     lambdacalc -^  linear logic -^
            line = line.strip()  # remove trailing newline
            if not len(line):
                continue  # skip empty lines
            if line[0] == "#":
                continue  # skip commented out lines

            parts = line.split(
                " : ", 2
            )  # ['verb', '(\\x.(<word> x), ( subj -o f ))', '[subj]']

            glue_formulas = []
            paren_count = 0
            tuple_start = 0
            tuple_comma = 0

            relationships = None

            if len(parts) > 1:
                for (i, c) in enumerate(parts[1]):
                    if c == "(":
                        if paren_count == 0:  # if it's the first '(' of a tuple
                            tuple_start = i + 1  # then save the index
                        paren_count += 1
                    elif c == ")":
                        paren_count -= 1
                        if paren_count == 0:  # if it's the last ')' of a tuple
                            meaning_term = parts[1][
                                tuple_start:tuple_comma
                            ]  # '\\x.(<word> x)'
                            glue_term = parts[1][tuple_comma + 1 : i]  # '(v-r)'
                            glue_formulas.append(
                                [meaning_term, glue_term]
                            )  # add the GlueFormula to the list
                    elif c == ",":
                        if (
                            paren_count == 1
                        ):  # if it's a comma separating the parts of the tuple
                            tuple_comma = i  # then save the index
                    elif c == "#":  # skip comments at the ends of lines
                        if (
                            paren_count != 0
                        ):  # if the line hasn't parsed correctly so far
                            raise RuntimeError(
                                "Formula syntax is incorrect for entry " + line
                            )
                        break  # break to the next line

            if len(parts) > 2:  # if there is a relationship entry at the end
                rel_start = parts[2].index("[") + 1
                rel_end = parts[2].index("]")
                if rel_start == rel_end:
                    relationships = frozenset()
                else:
                    relationships = frozenset(
                        r.strip() for r in parts[2][rel_start:rel_end].split(",")
                    )

            try:
                start_inheritance = parts[0].index("(")
                end_inheritance = parts[0].index(")")
                sem = parts[0][:start_inheritance].strip()
                supertype = parts[0][start_inheritance + 1 : end_inheritance]
            except:
                sem = parts[0].strip()
                supertype = None

            if sem not in self:
                self[sem] = {}

            if (
                relationships is None
            ):  # if not specified for a specific relationship set
                # add all relationship entries for parents
                if supertype:
                    for rels in self[supertype]:
                        if rels not in self[sem]:
                            self[sem][rels] = []
                        glue = self[supertype][rels]
                        self[sem][rels].extend(glue)
                        self[sem][rels].extend(
                            glue_formulas
                        )  # add the glue formulas to every rel entry
                else:
                    if None not in self[sem]:
                        self[sem][None] = []
                    self[sem][None].extend(
                        glue_formulas
                    )  # add the glue formulas to every rel entry
            else:
                if relationships not in self[sem]:
                    self[sem][relationships] = []
                if supertype:
                    self[sem][relationships].extend(self[supertype][relationships])
                self[sem][relationships].extend(
                    glue_formulas
                )  # add the glue entry to the dictionary

    def __str__(self):
        accum = ""
        for pos in self:
            str_pos = "%s" % pos
            for relset in self[pos]:
                i = 1
                for gf in self[pos][relset]:
                    if i == 1:
                        accum += str_pos + ": "
                    else:
                        accum += " " * (len(str_pos) + 2)
                    accum += "%s" % gf
                    if relset and i == len(self[pos][relset]):
                        accum += " : %s" % relset
                    accum += "\n"
                    i += 1
        return accum

    def to_glueformula_list(self, depgraph, node=None, counter=None, verbose=False):
        if node is None:
            # TODO: should it be depgraph.root? Is this code tested?
            top = depgraph.nodes[0]
            depList = list(chain.from_iterable(top["deps"].values()))
            root = depgraph.nodes[depList[0]]

            return self.to_glueformula_list(depgraph, root, Counter(), verbose)

        glueformulas = self.lookup(node, depgraph, counter)
        for dep_idx in chain.from_iterable(node["deps"].values()):
            dep = depgraph.nodes[dep_idx]
            glueformulas.extend(
                self.to_glueformula_list(depgraph, dep, counter, verbose)
            )
        return glueformulas

    def lookup(self, node, depgraph, counter):
        semtype_names = self.get_semtypes(node)

        semtype = None
        for name in semtype_names:
            if name in self:
                semtype = self[name]
                break
        if semtype is None:
            # TODO(sfedia): handle exceptions related to missing semtype
            # raise KeyError, "There is no GlueDict entry for sem type '%s' (for '%s')" % (sem, word)
            return []

        self.add_missing_dependencies(node, depgraph)

        lookup = self._lookup_semtype_option(semtype, node, depgraph)

        if not len(lookup):
            raise KeyError(
                "There is no GlueDict entry for sem type of '%s' "
                "with tag '%s', and rel '%s'" % (node["word"], node["tag"], node["rel"])
            )

        # TODO(sfedia): work on symbolization
        return self.get_glueformulas_from_semtype_entry(
            lookup, node, depgraph, counter
        )

    def add_missing_dependencies(self, node, depgraph):
        rel = node["rel"].lower()

        if rel == "main":
            headnode = depgraph.nodes[node["head"]]
            subj = self.lookup_unique("subj", headnode, depgraph)
            relation = subj["rel"]
            node["deps"].setdefault(relation, [])
            node["deps"][relation].append(subj["address"])
            # node['deps'].append(subj['address'])

    def _lookup_semtype_option(self, semtype, node, depgraph):
        # TODO(sfedia): OPTIONAL_RELATIONSHIPS
        relationships = frozenset(
            depgraph.nodes[dep]["rel"].lower()
            for dep in chain.from_iterable(node["deps"].values())
            if depgraph.nodes[dep]["rel"].lower() not in OPTIONAL_RELATIONSHIPS
        )

        try:
            lookup = semtype[relationships]
        except KeyError:
            # An exact match is not found, so find the best match where
            # 'best' is defined as the glue entry whose relationship set has the
            # most relations of any possible relationship set that is a subset
            # of the actual depgraph
            best_match = frozenset()
            for relset_option in set(semtype) - {None}:
                if (
                    len(relset_option) > len(best_match)
                    and relset_option < relationships
                ):
                    best_match = relset_option
            if not best_match:
                if None in semtype:
                    best_match = None
                else:
                    return None
            lookup = semtype[best_match]

        return lookup

    def get_semtypes(self, node):
        """
        Based on the node, return a list of plausible semtypes in order of
        plausibility.
        """
        rel = node["rel"].lower()

        # TODO(sfedia): clean up there
        if rel in ["nmod", "vmod"]:
            return [node["ctag"], rel]
        else:
            # TODO(sfedia): add if-branch for quantifiers (e.g., каждый) etc.
            return [node["ctag"]]

    def get_glueformulas_from_semtype_entry(
        self, lookup, node, depgraph, counter
    ):
        glueformulas = []

        node_symb = SimplestSymbolizer(node)

        glueFormulaFactory = self.get_GlueFormula_factory()
        for meaning, glue in lookup:
            gf = glueFormulaFactory(self.get_meaning_formula(meaning, node, node_symb), glue)
            if not len(glueformulas):
                gf.word = node_symb.symb()
            else:
                gf.word = f"{node_symb.symb()}{len(glueformulas) + 1}"

            gf.glue = self.initialize_labels(gf.glue, node, depgraph, counter.get())

            glueformulas.append(gf)
        return glueformulas

    # TODO(sfedia): get rid of unused argument
    def get_meaning_formula(self, generic, node, node_symbolizer):
        node_symb = node_symbolizer.symb().replace(".", "")
        generic = generic.replace("<word>", node_symb)
        generic = re.sub(
            r"<feat[.]([A-Z][a-z]+)[.]symb>",
            lambda m: node_symbolizer.symbolize_feature(m.group(1)),
            generic
        )
        return generic

    def initialize_labels(self, expr, node, depgraph, unique_index):
        if isinstance(expr, linearlogic.AtomicExpression):
            name = self.find_label_name(expr.name.lower(), node, depgraph, unique_index)
            if name[0].isupper():
                return linearlogic.VariableExpression(name)
            else:
                return linearlogic.ConstantExpression(name)
        else:
            return linearlogic.ImpExpression(
                self.initialize_labels(expr.antecedent, node, depgraph, unique_index),
                self.initialize_labels(expr.consequent, node, depgraph, unique_index),
            )

    def find_label_name(self, name, node, depgraph, unique_index):
        try:
            dot = name.index(".")

            before_dot = name[:dot]
            after_dot = name[dot + 1 :]
            if before_dot == "super":
                return self.find_label_name(
                    after_dot, depgraph.nodes[node["head"]], depgraph, unique_index
                )
            else:
                return self.find_label_name(
                    after_dot,
                    self.lookup_unique(before_dot, node, depgraph),
                    depgraph,
                    unique_index,
                )
        except ValueError:
            lbl = self.get_label(node)
            if name == "f":
                return lbl
            elif name == "v":
                return "%sv" % lbl
            elif name == "r":
                return "%sr" % lbl
            elif name == "super":
                return self.get_label(depgraph.nodes[node["head"]])
            elif name == "var":
                return f"{lbl.upper()}{unique_index}"
            elif name == "a":
                return self.get_label(self.lookup_unique("conja", node, depgraph))
            elif name == "b":
                return self.get_label(self.lookup_unique("conjb", node, depgraph))
            else:
                return self.get_label(self.lookup_unique(name, node, depgraph))

    def get_label(self, node):
        """
        Pick an alphabetic character as identifier for an entity in the model.

        :param value: where to index into the list of characters
        :type value: int
        """
        value = node["address"]

        letter = [
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "v",
            "w",
            "x",
            "y",
            "z",
            "a",
            "b",
            "c",
            "d",
            "e",
        ][value - 1]
        num = int(value) // 26
        if num > 0:
            return letter + str(num)
        else:
            return letter

    def lookup_unique(self, rel, node, depgraph):
        """
        Lookup 'key'. There should be exactly one item in the associated relation.
        """
        deps = [
            depgraph.nodes[dep]
            for dep in chain.from_iterable(node["deps"].values())
            if depgraph.nodes[dep]["rel"].lower() == rel.lower()
        ]

        if len(deps) == 0:
            raise KeyError(
                "'{}' doesn't contain a feature '{}'".format(node["word"], rel)
            )
        elif len(deps) > 1:
            raise KeyError(
                "'{}' should only have one feature '{}'".format(node["word"], rel)
            )
        else:
            return deps[0]

    def get_GlueFormula_factory(self):
        return GlueFormula


class GlueFormula:
    def __init__(self, meaning, glue, indices=None):
        if not indices:
            indices = set()

        if isinstance(meaning, str):
            self.meaning = Expression.fromstring(meaning)
        elif isinstance(meaning, Expression):
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

    def applyto(self, arg):
        """self = (\\x.(walk x), (subj -o f))
        arg  = (john        ,  subj)
        returns ((walk john),          f)
        """
        if self.indices & arg.indices:  # if the sets are NOT disjoint
            raise linearlogic.LinearLogicApplicationException(
                f"'{self}' applied to '{arg}'.  Indices are not disjoint."
            )
        else:  # if the sets ARE disjoint
            return_indices = self.indices | arg.indices

        try:
            return_glue = linearlogic.ApplicationExpression(
                self.glue, arg.glue, arg.indices
            )
        except linearlogic.LinearLogicApplicationException as e:
            raise linearlogic.LinearLogicApplicationException(
                f"'{self.simplify()}' applied to '{arg.simplify()}'"
            ) from e

        arg_meaning_abstracted = arg.meaning
        if return_indices:
            for dep in self.glue.simplify().antecedent.dependencies[
                ::-1
            ]:  # if self.glue is (A -o B), dep is in A.dependencies
                arg_meaning_abstracted = self.make_LambdaExpression(
                    Variable("v%s" % dep), arg_meaning_abstracted
                )
        return_meaning = self.meaning.applyto(arg_meaning_abstracted)

        return self.__class__(return_meaning, return_glue, return_indices)

    def make_VariableExpression(self, name):
        return VariableExpression(name)

    def make_LambdaExpression(self, variable, term):
        return LambdaExpression(variable, term)

    def lambda_abstract(self, other):
        assert isinstance(other, GlueFormula)
        assert isinstance(other.meaning, AbstractVariableExpression)
        return self.__class__(
            self.make_LambdaExpression(other.meaning.variable, self.meaning),
            linearlogic.ImpExpression(other.glue, self.glue),
        )

    def compile(self, counter=None):
        """From Iddo Lev's PhD Dissertation p108-109"""
        if not counter:
            counter = Counter()
        (compiled_glue, new_forms) = self.glue.simplify().compile_pos(
            counter, self.__class__
        )
        return new_forms + [
            self.__class__(self.meaning, compiled_glue, {counter.get()})
        ]

    def simplify(self):
        return self.__class__(
            self.meaning.simplify(), self.glue.simplify(), self.indices
        )

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.meaning == other.meaning
            and self.glue == other.glue
        )

    def __ne__(self, other):
        return not self == other

    # sorting for use in doctests which must be deterministic
    def __lt__(self, other):
        return str(self) < str(other)

    def __str__(self):
        assert isinstance(self.indices, set)
        accum = f"{self.meaning} : {self.glue}"
        if self.indices:
            accum += (
                " : {" + ", ".join(str(index) for index in sorted(self.indices)) + "}"
            )
        return accum

    def __repr__(self):
        return "%s" % self


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

class PossibleAntecedents(list, nltk.sem.drt.DrtExpression, Expression):
    def free(self):
        """Set of free variables."""
        return set(self)

    def replace(self, variable, expression, replace_bound=False, alpha_convert=True):
        """Replace all instances of variable v with expression E in self,
        where v is free in self."""
        result = PossibleAntecedents()
        for item in self:
            if item == variable:
                self.append(expression)
            else:
                self.append(item)
        return result

    def _pretty(self):
        s = "%s" % self
        blank = " " * len(s)
        return [blank, blank, s]

    def __str__(self):
        return "[" + ",".join("%s" % it for it in self) + "]"


class AnaphoraResolutionException(Exception):
    pass


def resolve_anaphora(expression, trail=[]):
    if isinstance(expression, ApplicationExpression):
        if expression.is_pronoun_function():
            possible_antecedents = PossibleAntecedents()
            for ancestor in trail:
                for ref in ancestor.get_refs():
                    refex = expression.make_VariableExpression(ref)

                    # ==========================================================
                    # Don't allow resolution to itself or other types
                    # ==========================================================
                    if refex.__class__ == expression.argument.__class__ and not (
                        refex == expression.argument
                    ):
                        possible_antecedents.append(refex)

            if len(possible_antecedents) == 1:
                resolution = possible_antecedents[0]
            else:
                resolution = possible_antecedents
            return expression.make_EqualityExpression(expression.argument, resolution)
        else:
            r_function = resolve_anaphora(expression.function, trail + [expression])
            r_argument = resolve_anaphora(expression.argument, trail + [expression])
            return expression.__class__(r_function, r_argument)

    elif isinstance(expression, nltk.sem.drt.DRS):
        r_conds = []
        for cond in expression.conds:
            r_cond = resolve_anaphora(cond, trail + [expression])

            # if the condition is of the form '(x = [])' then raise exception
            if isinstance(r_cond, EqualityExpression):
                if isinstance(r_cond.first, PossibleAntecedents):
                    # Reverse the order so that the variable is on the left
                    temp = r_cond.first
                    r_cond.first = r_cond.second
                    r_cond.second = temp
                if isinstance(r_cond.second, PossibleAntecedents):
                    if not r_cond.second:
                        raise AnaphoraResolutionException(
                            "Variable '%s' does not "
                            "resolve to anything." % r_cond.first
                        )

            r_conds.append(r_cond)
        if expression.consequent:
            consequent = resolve_anaphora(expression.consequent, trail + [expression])
        else:
            consequent = None
        return expression.__class__(expression.refs, r_conds, consequent)

    elif isinstance(expression, AbstractVariableExpression):
        return expression

    elif isinstance(expression, NegatedExpression):
        return expression.__class__(
            resolve_anaphora(expression.term, trail + [expression])
        )

    elif isinstance(expression, nltk.sem.drt.DrtConcatenation):
        if expression.consequent:
            consequent = resolve_anaphora(expression.consequent, trail + [expression])
        else:
            consequent = None
        return expression.__class__(
            resolve_anaphora(expression.first, trail + [expression]),
            resolve_anaphora(expression.second, trail + [expression]),
            consequent,
        )

    elif isinstance(expression, BinaryExpression):
        return expression.__class__(
            resolve_anaphora(expression.first, trail + [expression]),
            resolve_anaphora(expression.second, trail + [expression]),
        )

    elif isinstance(expression, LambdaExpression):
        return expression.__class__(
            expression.variable, resolve_anaphora(expression.term, trail + [expression])
        )



class RulLamGlueReadingCommand(nltk.inference.discourse.ReadingCommand):
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

        web_result = web_udpipe_process_text_conllu(sentence)
        depgraph = DependencyGraph(web_result)
        return [depgraph]
