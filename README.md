# RuLAM: <ins>Ru</ins>ssian Natural Language to <ins>Lam</ins>bda Expressions
![coverage](https://img.shields.io/badge/coverage-27%25-yellowgreen)

The main goal of the **RuLam** project is to build a universal parser capable of converting arbitrary Russian text into [lambda calculus](https://en.wikipedia.org/wiki/Lambda_calculus) expressions and, as result, creating DRS from the given text <sup>[[1]](https://plato.stanford.edu/entries/discourse-representation-theory/) [[2]](https://en.wikipedia.org/wiki/Discourse_representation_theory) [[3]](https://www.nltk.org/book/ch10.html)</sup>.

Discourse representation structures (DRS)<sup>[[4]](https://plato.stanford.edu/entries/discourse-representation-theory/#DRSLanSynSemAcc)</sup> are used in DRT<sup>[[2]](https://en.wikipedia.org/wiki/Discourse_representation_theory)</sup> (Discourse representation theory) to represent a hearer's mental representation of a discourse as it unfolds over time. A very important advantage of modelling text with the DRT is the ability to resolve anaphora within the whole text and solve various problems involving coreference. This means that we, for example, can determine exactly which pronouns correspond to the previously mentioned objects and subjects, and which do not.

For the Russian language, as far as we know, there is no DRT parser yet. This project aims to realize this possibility.

* Useful papers and stuff on Zotero RuLAM Group: https://www.zotero.org/groups/4913575/rulam/
* Trello board: https://trello.com/w/rulam1

## Installation
While the project is still in its very first steps and has not been published to PyPI, so to install the project and play around, you can clone the repository:

```
git clone https://github.com/sfedia/RuLAM
```

After that, proceed to the local repo directory and install the necessary modules on which the project depends:

```
cd RuLAM
pip3 install -r requirements.txt
```

It's best to first make sure that nothing is broken and everything works:

```
python3 -m pytest --cov-report term --cov=rulam
```

If everything works, then you can try to run the parser in some way.

## Usage
Since the project is still at the very initial stage, for the demo you can run it while in the repo directory. If you feel like it, you can tinker around and create a setup.py for the project yourself. And it will be cool if you then PR it! Anyway, I'll add setup.py here soon.

You can parse, for example, two Russian sentences, like this:
```python3
import rulam
parser = rulam.parser.get_parser(["Заяц бежит", "Он серый"])
parser.readings(show_thread_readings=True, filter=True)
```
This will produce a ready-made DRS for you and, as you can see, the anaphora between the pronoun `он` and the previously mentioned noun `заяц` is resolved.
```
d0: ['s0-r0', 's1-r0'] :
([z1,z2],[zajats(z1), MALE(z1), bezhat(z1), (z2 = z1), seryj(z2), MALE(z2)])
```

## How the project works
The RuLAM project is designed as a pipeline.
* Syntax & morphology parsing stage: First, RuLAM sends the text to the morphological and syntactic parser UDPipe.
* Symbolization stage: Then, receiving data in the CoNLL-U format, looking at the data about the syntax of the text and the morphology of words, RuLAM based on the rules generates predicates.
* Tree to lambda conversion stage: Using the principles of [Glue Semantics](https://en.wikipedia.org/wiki/Glue_semantics), RuLam converts syntax trees to DRS.
* DRS concatenation stage: NLTK provides an excellent set of tools for dealing with DRS, and with their help, RuLAM concatenates DRS structures and resolves anaphoras.

## Current state and future challenges
1. At the moment, very few rules for conversion have been written, so not all sentences can be successfully parsed
2. Only part of the code is covered by tests, and in some places there is already something to fix
3. Processing of morphology is only at the initial stage, e.g., work on achieving the support of quantifiers has not yet begun
4. The symbolizer needs to be taught to translate the names of predicates into English, not transliterated Russian
5. UDPipe now connects through the web interface, which makes parsing slower, it would be cool to connect it locally
6. Anaphora resolution should be precise
7. Integrate with [sfedia/nltk-drt](https://github.com/sfedia/nltk-drt) to support tense and presupposition resolution in Russian

And other things to do...
