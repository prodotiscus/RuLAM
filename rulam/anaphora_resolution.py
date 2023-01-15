import nltk
from nltk.sem.logic import (
    AbstractVariableExpression,
    Expression,
    LambdaExpression,
    ApplicationExpression,
    BinaryExpression,
    EqualityExpression,
    LambdaExpression,
    NegatedExpression
)


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
