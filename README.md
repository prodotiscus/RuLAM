# RuLAM: <ins>Ru</ins>ssian Natural Language to <ins>Lam</ins>bda Expressions
The main goal of the **RuLam** project is to build a universal parser capable of converting arbitrary Russian text into lambda calculus expressions and, as result, creating DRS from the given text.

Discourse representation structures (DRS) are used in DRT (Discourse representation theory) to represent a hearer's mental representation of a discourse as it unfolds over time. A very important advantage of modelling text with the DRT is the ability to resolve anaphora within a sentence and solve various problems involving coreference within a text. This means that we, for example, can determine exactly which pronouns correspond to the previously mentioned objects and subjects, and which do not.

For the Russian language, as far as we know, there is no DRT parser yet. This project aims to realize this possibility.

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
python3 -m pytest
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
d0: ['s0-r0', 's1-r0'] : ([z1,z2],[zajats(z1), MALE(z1), bezhat(z1), (z2 = z1), seryj(z2), MALE(z2)])
```
