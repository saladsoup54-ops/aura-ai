# ukft_relations.py — AURA Relation Extraction (V5 R1)
# ==================================================
# The first piece of the reasoning layer.  Aura holds a lot of prose;
# reasoning needs typed FACTS.  This lobe pattern-mines the vault for
# high-precision surface forms and writes canonical relation lines to
# extracted_relations.txt with confidence scores.  NOTHING consumes
# the output yet (R2 builds the knowledge graph); until the Architect's
# sample audit passes (Gate R-A), the file is an audit artifact, not a
# knowledge source.
#
#   - Read-only over the vault: iter_anchors, never append_anchor.
#   - One relation per sentence (begat/fathered chains excepted), first
#     matching family wins — families are ordered so overlapping surface
#     forms resolve to the precise one ("is a part of" is part_of, not
#     is_a; "is a form of" is is_a with the noun dropped).
#   - Precision-first: args containing digits, pronouns, qualifiers or
#     no content word are dropped; long args are rejected outright
#     rather than carried at low confidence — the audit (Gate R-A)
#     measures precision, so recall is deliberately sacrificed.
#   - Deduplicated on (type, x, y); best confidence kept.
#   - Genealogies hide behind verse numbers ("19 hezron fathered ram")
#     and ages ("cainan lived 130 years and fathered shelah") that the
#     strict sentence splitter amputates.  A second, looser pass mines
#     only kin names and possessive "had" from those sentences — is_a
#     on unlocked poetry would need a metaphor gate that does not
#     exist yet, so it is deliberately NOT run there.
# ==================================================

import collections
import re
import sys
import time

from aura_bus import write as bus_write
from aura_constants import EXTRACTED_RELATIONS, VAULT_FILE
from aura_vault_io import iter_anchors, repair_hyphenation

# Pronouns and demonstratives never serve as relation arguments; neither
# do free-standing qualifiers ("dark matter is a very mysterious thing"
# is hedge, not taxonomy) nor question words ("how are resources shared"
# is a question, not a class statement).
REL_STOP = {
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their", "mine",
    "yours", "hers", "ours", "theirs", "myself", "yourself", "himself",
    "herself", "itself", "themselves", "ourselves", "this", "that",
    "these", "those", "there", "here", "who", "whom", "whose", "what",
    "which", "one", "very", "really", "much", "many", "more", "most",
    "some", "such", "not", "any", "all", "only", "also", "just", "even",
    "about", "each", "every", "own", "both", "where", "when", "why",
    "how", "following",
}

# Function words: never the content of a named argument.  Names and
# subjects are content phrases — "coming of" and "is ahiezer" are
# sentence debris, not kin X-arguments.
FUNCTION_WORDS = {
    "of", "and", "in", "to", "with", "by", "from", "the", "a", "an",
    "is", "was", "were", "are", "be", "been", "am", "had", "has",
    "have", "do", "does", "did", "will", "would", "can", "could",
    "may", "might", "shall", "should", "must", "for", "on", "at",
    "or", "as", "if", "than", "that", "this", "these", "those",
    "not", "no", "so", "but", "also", "now", "then",
}

# Two-letter function words that may legitimately sit INSIDE an
# otherwise-good noun phrase ("speed of light"); anything else that
# short is an OCR syllable ("rev o lu tion ary") and kills the arg.
SHORT_FUNC = {"of", "to", "in", "on", "at", "by", "or", "an", "as",
              "it", "is", "be", "we", "he", "me", "my", "so", "no",
              "do", "go", "up", "if"}

# Words that start a qualifier clause inside an is_a Y — everything
# after them describes the class, it is not the class ("a directory
# within a directory" is is_a(directory), not is_a(directory within a
# directory)).  Participles that hang off the noun phrase ("a program
# designed to run inside...") are cut here; participles that merely
# attach the qualifier ("used for tracking changes") are TRAIL-stripped
# instead, so hyphenated modifiers ("widely-used") can't fake a cut.
IS_A_Y_CUT = {"and", "or", "but", "that", "which", "who", "whom",
              "within", "with", "in", "on", "at", "by", "to", "from",
              "for", "against", "toward", "as", "consisting",
              "containing", "involving", "using", "studying",
              "describing", "built", "made", "formed", "composed",
              "responsible", "designed", "meant", "intended", "focused",
              "called", "known", "referred", "defined", "introduced",
              "located", "found", "performed", "written", "provided",
              "developed", "released", "maintained"}

# Trailing words stripped off an is_a Y / has_property Y after the cut:
# function words plus the participles/adverbs that attach qualifiers.
TRAIL_WORDS = FUNCTION_WORDS | {
    "used", "created", "meaning", "primarily", "mostly", "mainly",
    "generally", "typically", "essentially", "fundamentally",
    "celebrated", "born", "provided", "described", "defined", "called",
    "known", "based", "fundamental", "essential", "sometimes", "often",
    "usually", "normally", "terminated", "purposed", "intended",
    "designed", "meant", "focused", "developed", "released",
}

# DeterminER openings: possessive "has" only counts when the property
# is a noun phrase ("a strong symbol has a unique memory location").
# Present-perfect verbs ("the lord has spoken") fail this gate.
DETERMINER_RE = re.compile(
    r"^(?:a|an|the|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|many|several|different|various|few|numerous|some)\b"
)

# Rhetorical epithets: Bible/prose insults that must never become
# taxonomy ("the prophet is a fool" is poetry, not an is_a edge).
# Curated and small by design — the Architect can extend it.
EPITHET_STOP = {"fool", "liar", "idiot", "hypocrite", "adulterer",
                "murderer", "thief", "coward"}

MIN_REL_CONF = 0.55   # below this, relations are noise, not knowledge

# Rhetorical appraisals that are never a class ("java is a popular
# choice for..." praises java; it does not classify it).
EVAL_CHOICE = {"great choice", "good choice", "popular choice",
               "natural choice", "common choice", "ideal choice",
               "perfect choice", "obvious choice", "reasonable choice",
               "excellent choice"}

# Bare generic persons are narrative placeholders, not entities: "a
# man had two sons" (a parable character) and "the man was a valiant
# warrior" (Naaman) must not become class-level assertions that R3's
# inheritance would spread to every is_a instance ("obadiah had two
# sons").  Class-level facts about people use other surface forms
# ("a wise man is..."); the Y-side ("obadiah was a man") is unaffected.
NARRATIVE_SUBJECTS = {"man", "woman"}

# Class-noun skeletons: "X is a (modifiers) way|means|method of Y" —
# the modifiers are properties, the class is "way of Y".  Handled
# before the generic is_a row so the conjunction cut can't amputate
# "a secure and transparent way" down to "secure".  Modifiers are
# optional ("a way of building software").
WAY_RE = re.compile(
    r"^(.*?)\s+(?:is|was)\s+an?\s+(?:(.*?)\s+)?(way|means|method)\s+"
    r"(of|to|for)\s+(.*)$"
)
# "X is an example of Y" — X is an instance of class Y; "divide and
# conquer" stays whole because conjunctions are not cut here.
EXAMPLE_RE = re.compile(
    r"^(.*?)\s+(?:is|was)\s+an?\s+(?:(.*?)\s+)?example of\s+(.*)$"
)

# (type, subrel, regex, base_confidence, swap_xy, max_y_words)
# Order matters: part_of precedes generic is_a so "is a part of" never
# reads as is_a; kin precedes is_a so "is the son of" stays kin.  The
# plural "X are Y" form is deliberately ABSENT: passives ("eyes are
# opened"), adjectives ("farmers are ashamed") and questions dominate
# it, and the R1 spec lists is_a as "X is a Y" — precision over recall.
PATTERNS = [
    ("part_of", "", r"^(.*?)\s+(?:is|are)\s+(?:a\s+)?part of\s+(.*)$", 0.85, False, 6),
    ("part_of", "", r"^(.*?)\s+consists of\s+(.*)$", 0.80, True, 6),
    ("kin", "son_of", r"^(.*?)\s+(?:(?:is|was)\s+the\s+|the\s+)?son of\s+(.*)$", 0.90, False, 2),
    ("kin", "daughter_of", r"^(.*?)\s+(?:(?:is|was)\s+the\s+|the\s+)?daughter of\s+(.*)$", 0.90, False, 2),
    ("kin", "father_of", r"^(.*?)\s+(?:(?:is|was)\s+the\s+|the\s+)?father of\s+(.*)$", 0.90, False, 2),
    ("compare", "greater_than", r"^(.*?)\s+is\s+greater than\s+(.*)$", 0.90, False, 6),
    ("compare", "less_than", r"^(.*?)\s+is\s+less than\s+(.*)$", 0.90, False, 6),
    ("compare", "larger_than", r"^(.*?)\s+is\s+larger than\s+(.*)$", 0.90, False, 6),
    ("compare", "smaller_than", r"^(.*?)\s+is\s+smaller than\s+(.*)$", 0.90, False, 6),
    ("compare", "heavier_than", r"^(.*?)\s+is\s+heavier than\s+(.*)$", 0.90, False, 6),
    ("compare", "lighter_than", r"^(.*?)\s+is\s+lighter than\s+(.*)$", 0.90, False, 6),
    ("compare", "faster_than", r"^(.*?)\s+is\s+faster than\s+(.*)$", 0.90, False, 6),
    ("compare", "slower_than", r"^(.*?)\s+is\s+slower than\s+(.*)$", 0.90, False, 6),
    ("compare", "more_massive_than", r"^(.*?)\s+is\s+more massive than\s+(.*)$", 0.90, False, 6),
    ("compare", "equal_to", r"^(.*?)\s+is equal to\s+(.*)$", 0.80, False, 6),
    ("is_a", "", r"^(.*?)\s+(?:is|was)\s+an?\s+(?:kind|form|type|sort|instance) of\s+(.*)$", 0.90, False, 6),
    ("is_a", "", r"^(.*?)\s+(?:is|was)\s+an?\s+(.*)$", 0.85, False, 6),
    ("causes", "", r"^(.*?)\s+(?:causes|caused|leads to|led to|results in|resulted in)\s+(.*)$", 0.85, False, 6),
    ("causes", "", r"^if\s+(.*?)\s+then\s+(.*)$", 0.70, False, 6),
    ("located_in", "", r"^(.*?)\s+(?:is located in|is situated in|lies in)\s+(.*)$", 0.85, False, 6),
    ("has_property", "lacks", r"^(.*?)\s+has no\s+(.*)$", 0.85, False, 6),
    ("has_property", "has", r"^(.*?)\s+ha(?:s|ve|d)\s+(.*)$", 0.65, False, 6),
]

# Bible genealogies: "Adam fathered Seth, Seth fathered Enosh..." —
# every NAME-fathered-NAME pair in a sentence is a father_of relation.
# The CSB translation uses "fathered"; "begat/begot" is kept for any
# legacy corpus.  The verbs are matched as whole tokens: the old
# bega[tn] spelling also matched "began", minting father_of(bang,
# only) from "the big bang began only recently".
FATHERED_VERBS = {"begat", "begot", "fathered"}

# "X, son of Y" and "X son of Y" chains: the name neighbours of every
# "son of"/"daughter of" marker.  A single verse can chain a whole
# genealogy ("ethan, son of zimmah, son of shimei") and OCR splits the
# names ("ma a cah", "abish a lom"), so both sides are rejoined with
# the attested vocabulary before the gates run.
KIN_RE = re.compile(r"\b(?:(the)\s+)?(son|daughter)\s+of\b")
TOKEN_RE = re.compile(r"[a-z][a-z'-]*")

# Titles, ordinals and generic relatives are never the CHILD side of a
# kin edge ("the youngest son of jerubbaal" is a description, not a
# name; "healing a daughter of abraham" is a scene, not a person), and
# "man"/"god" are titles on the PARENT side ("son of man").
KIN_X_STOP = {
    "youngest", "oldest", "first", "second", "third", "fourth", "fifth",
    "sixth", "seventh", "eighth", "ninth", "tenth", "firstborn", "eldest",
    "younger", "older", "greatest", "least", "princess", "prince", "queen",
    "king", "prophet", "prophetess", "priest", "leader", "commander",
    "scribe", "servant", "official", "woman", "man", "child", "wife",
    "husband", "mother", "father", "brother", "sister", "daughter", "son",
    "grandmother", "grandfather", "uncle", "aunt", "nephew", "niece",
    "married", "healing", "prisoners", "singer", "aloud", "nile", "lord",
    "observe", "translated", "twice", "omit", "other", "seen",
    # Reflexives are never names ("i myself bore the loss" is
    # endurance, not motherhood).
    "self", "selves", "oneself",
}
KIN_Y_STOP = {"man", "god", "other"}

# OCR syllable tails observed in the live audit: they never stand alone
# as names, they survive only as the tail of a split word ("Abish a
# lom", "jahze iah", "ben-ha dad", "shal lum").  Curated and small by
# design — the Architect can extend it.
KIN_FRAGMENT_STOP = {
    "abish", "aphi", "ber", "bod", "dab", "dad", "har", "hil", "iah",
    "jaare", "kam", "lal", "lum", "mat", "nim", "pha", "rath", "riah",
    "shal", "sheth", "shub", "ter", "tik", "tok", "vah", "zar", "zebe",
}
KIN_Y_TITLES = {"king", "queen", "prince", "princess", "prophet",
                "prophetess", "priest", "servant", "commander", "leader",
                "official", "scribe", "judge"}

# "Japheth's sons: Gomer, Magog..." / "These are the sons of Esau" /
# "Shem's sons were Elam..." — colon- and verb-bounded name lists.
# The strict splitter cuts at colons, so these tails survive only in
# the loose pass.  "Children of X" is deliberately ABSENT ("children
# of Israel" is an ethnonym, not a family); daughters ride along.
SON_LIST_HEAD_RES = (
    (r"^(.*?)\s+s\s+sons?\b\s*(.+)$", "son_of"),
    (r"^(.*?)\s+s\s+daughters?\b\s*(.+)$", "daughter_of"),
    (r"^(?:these are )?the sons? of\s+(.+?)\s*[:;,]\s*(.+)$", "son_of"),
    (r"^(?:these are )?the daughters? of\s+(.+?)\s*[:;,]\s*(.+)$",
     "daughter_of"),
)
LIST_SPLIT_RE = re.compile(r"\s*(?:,|;|\band\b)\s*")
MAX_LIST_NAMES = 12
LIST_NAME_TITLES = KIN_Y_TITLES | {"chief", "elder", "duke", "king"}

# Ordinal and number tails are verse furniture ("Jahaziel third",
# "Anani seven"), never name parts.
ORDINAL_TAIL = {
    "first", "second", "third", "fourth", "fifth", "sixth",
    "seventh", "eighth", "ninth", "tenth", "firstborn", "last",
    "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve",
}

# Bare generics are never names ("the daughter of Tyre, the wealthy
# people" must not mint daughter_of(wealthy people, tyre)).
GENERIC_NOUNS = {
    "people", "peoples", "children", "men", "women", "sons",
    "daughters", "multitude", "nations", "tribes", "army", "crowd",
}

# A relative clause bounds the list ("Tubal-cain, who made iron
# tools" names one son, not "iron tools").
LIST_CLAUSE_CUT = re.compile(
    r",\s*(?:who|which|whom)\b|\s+(?:who|which|whom)\b")

# "Naarah bore Ahuzzam" / "X was the mother of Y" / "Jael, the
# wife of Heber" — maternal and marital appositions.  X is always
# a single name (precision over "joyful mother" poetry); Y takes
# the leading content run ("Heber the Kenite" -> heber).
MATE_RES = (
    (r"^(.*?),\s*the (wife|husband|mother) of\s+(.*)$", None),
    (r"^(.*?)\s+(?:was|is)\s+the (wife|husband|mother) of\s+(.*)$",
     None),
    (r"^(.*?)\s+(?:bore|gave birth to)\s+(.*)$", "mother_of"),
)

# "Jada, brother of Shammai" — independent pairs, never chained:
# a brother marker followed by a son marker is two facts, not a
# chain ("A brother of B, son of C" must not mint son_of(B, C)).
SIB_RE = re.compile(r"\b(brother|sister)\s+of\b")

# "X refers to Y" is a definition surface form; "the divide refers to
# the uneven and unequal access..." must not become is_a(divide,
# uneven), so a cut that lands on "and" (an adjective list) is refused.
REFERS_RE = re.compile(r"^(.*?)\s+refers to\s+(.*)$")

# The possessive form, shared by the strict row and the loose pass.
HAS_RE = re.compile(r"^(.*?)\s+ha(?:s|ve|d)\s+(.*)$")

MAX_X_WORDS = 4
EVID_CAP = 160


def _sentences(data):
    """
    Clean chunk text down to candidate sentences (lowercased), with
    chunk-boundary and genre gates: a record that STARTS mid-sentence
    (lowercase first letter) has lost its subject in the previous
    chunk, and a record that ENDS without terminal punctuation has
    lost its tail — both poison arguments, so those edge sentences are
    skipped.  Quiz option letters ("d. A linker is a register...")
    mark distractor answers, never definitions; leading single letters
    are footnote markers ("n Ab i gail") to be stripped, not glued.
    """
    raw_first = re.sub(r"^[^a-zA-Z]+", "", data)
    starts_lower = bool(raw_first) and raw_first[0].islower()
    text = repair_hyphenation(data).lower()
    text = re.sub(r"[^\x20-\x7e]", " ", text)   # OCR junk -> spaces
    text = re.sub(r"\s+", " ", text).strip()
    ends_terminal = bool(re.search(r"[.!?]$", text))
    sentences = [s.strip(" .,!?\"'()")
                 for s in re.split(r"(?<=[.!?])\s+", text)]
    for i, sentence in enumerate(sentences):
        if i == 0 and starts_lower:
            continue
        # A record that ends without terminal punctuation has lost its
        # tail — but only skip the last sentence when no colon/verse
        # marker bounds the relation first ("ja cob had twelve sons: 23
        # leah's sons..." — the pre-colon fact is complete even though
        # the record's tail continues in the next chunk).
        if (i == len(sentences) - 1 and not ends_terminal
                and not re.search(r"[:;]|\s\d", sentence)):
            continue
        # A bare option letter ("a", "b", "c", "d") marks the NEXT
        # sentence as a multiple-choice answer — a distractor unless
        # the source says otherwise.  Never mine those.
        if i > 0 and re.fullmatch(r"[a-f]", sentences[i - 1]):
            continue
        # Verse numbers and footnotes: cut at colons/semicolons and at
        # any digit run ("adam begat seth: 2 and seth lived...")
        sentence = re.split(r"[:;]|\s\d", sentence)[0].strip(" .,!?\"'()")
        if not sentence or sentence[0].isdigit():
            continue
        # Footnote marker glued to the sentence start ("n Ab i gail"):
        # strip it so the fragment joiner cannot weld it into a name.
        sentence = re.sub(r"^[a-z]\s+", "", sentence)
        if not sentence:
            continue
        yield sentence


def _kin_sentences(data):
    """
    The strict splitter amputates everything after a digit ("cainan
    lived 130 years and fathered shelah") and drops sentences that
    begin with a verse number ("19 hezron fathered ram, 20 amminadab
    fathered nahshon") — exactly the biblical genealogy forms.  Kin
    mining therefore gets its own splitter: the chunk-boundary and
    quiz gates stay (they protect argument quality), but digits never
    cut a sentence and a leading verse number is skipped, not
    discarded.
    """
    raw_first = re.sub(r"^[^a-zA-Z]+", "", data)
    starts_lower = bool(raw_first) and raw_first[0].islower()
    text = repair_hyphenation(data).lower()
    text = re.sub(r"[^\x20-\x7e]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    ends_terminal = bool(re.search(r"[.!?]$", text))
    sentences = [s.strip(" .,!?\"'()")
                 for s in re.split(r"(?<=[.!?])\s+", text)]
    for i, sentence in enumerate(sentences):
        if i == 0 and starts_lower:
            continue
        if (i == len(sentences) - 1 and not ends_terminal
                and not re.search(r"[:;]|\s\d", sentence)):
            continue
        if i > 0 and re.fullmatch(r"[a-f]", sentences[i - 1]):
            continue
        sentence = re.sub(r"^[a-z]\s+", "", sentence)
        sentence = re.sub(r"^\d+\s+", "", sentence).strip(" .,!?\"'()")
        # Possessives normalize to the OCR form the list scans
        # read ("Japheth's" -> "japheth s", as pypdf renders it).
        sentence = re.sub(r"'s\b", " s", sentence)
        if not sentence:
            continue
        yield sentence


def _evid(sentence, x=None, y=None):
    """
    Evidence strings cap at a word boundary, never mid-word.  On a long
    uncut genealogy verse the window opens around the relation so the
    audit sees the fact, not the chunk header.
    """
    if x and len(sentence) > EVID_CAP:
        pos = sentence.find(x)
        if pos < 0 and y:
            pos = sentence.find(y)
        if pos > 0:
            start = max(0, pos - 50)
            window = sentence[start:start + EVID_CAP]
            cut = window.rfind(" ")
            if cut > 60:
                window = window[:cut]
            return ("... " if start else "") + window + " ..."
    if len(sentence) <= EVID_CAP:
        return sentence
    cut = sentence[:EVID_CAP].rfind(" ")
    if cut < 60:
        cut = EVID_CAP
    return sentence[:cut] + " ..."


def _clean_arg(arg):
    arg = arg.strip(" ,;:.\"'")
    arg = re.sub(r"^(?:the|a|an)\s+", "", arg)
    arg = re.sub(r"^(?:and|but|or|so|nor|for)\s+", "", arg)
    return arg.strip(" ,;:.\"'")


def _valid_arg(arg):
    arg = _clean_arg(arg)
    if not arg or re.search(r"\d", arg):
        return False
    if re.search(r"[^a-z ,'-]", arg):
        return False
    if "," in arg:
        return False
    words = re.findall(r"[a-z]+", arg)
    if any(w in REL_STOP for w in words):
        return False
    if any(len(w) <= 2 and w not in SHORT_FUNC for w in words):
        return False
    content = [w for w in words if len(w) >= 3 and re.search(r"[aeiou]", w)]
    return bool(content)


def _content_phrase(arg):
    """A named thing: every word is a content word, no function debris."""
    words = re.findall(r"[a-z]+", arg)
    if not words:
        return False
    for w in words:
        if len(w) < 3 or not re.search(r"[aeiou]", w) or w in FUNCTION_WORDS:
            return False
    return True


def _strip_trailing_func(arg):
    while True:
        words = re.findall(r"[a-z]+", arg)
        if words and words[-1] in TRAIL_WORDS:
            arg = arg[: arg.rfind(words[-1])].strip()
        else:
            return arg


def _has_dup_words(arg):
    words = re.findall(r"[a-z]+", arg)
    return any(words[i] == words[i + 1] for i in range(len(words) - 1))


def _cut_is_a_y(arg, keep=()):
    """Trim qualifier clauses off an is_a class phrase."""
    words = re.findall(r"[a-z]+", arg)
    for i, w in enumerate(words):
        if w in IS_A_Y_CUT and w not in keep:
            return " ".join(words[:i])
    return arg


def _word_count(arg):
    return len(re.findall(r"[a-z]+", arg))


def _confidence(base, x, y):
    conf = base
    extra = _word_count(x) + _word_count(y) - 4
    if extra > 0:
        conf -= 0.05 * min(extra, 3)
    for arg in (x, y):
        if re.search(r"\band\b|,", arg):
            conf -= 0.05
    return round(max(0.10, min(1.00, conf)), 2)


class RelationExtractor:
    """Pattern-mine typed relations out of vault prose."""

    def __init__(self, vault_path=VAULT_FILE, out_path=EXTRACTED_RELATIONS,
                 attested=None):
        self.vault_path = vault_path
        self.out_path = out_path
        self.relations = {}   # (type, sub, x, y) -> (conf, evid, src)
        self._vocab = attested   # None -> lazy whole-corpus build
        self._suffixes = None    # lazy: short suffixes of attested words

    def _get_attested(self):
        """
        Whole-corpus word counts, used to rejoin OCR syllable splits
        ("ja cob" -> "jacob").  Reuses the trigram engine's attestation
        pass — read-only, one scan, cached.
        """
        if self._vocab is None:
            try:
                from ukft_trigram import TrigramEngine
                engine = TrigramEngine(vault_path=self.vault_path)
                engine.rebuild_attested()
                self._vocab = engine._whole
            except Exception:
                self._vocab = {}
        return self._vocab

    def _get_suffixes(self):
        """Every 3-5 char suffix of a well-attested corpus word."""
        if self._suffixes is None:
            suffixes = set()
            for longer, count in self._get_attested().items():
                if count >= 5 and len(longer) >= 5:
                    for k in range(3, min(6, len(longer) - 1)):
                        suffixes.add(longer[-k:])
            self._suffixes = suffixes
        return self._suffixes

    def _has_fragment_word(self, arg):
        """
        A short arg word that is the tail of a common corpus word but
        almost never stands alone is an OCR syllable, not a concept
        ("gry" of "angry", "igail" of "abigail").  Own-count floor
        spares real words that happen to be suffixes ("bit", "order").
        """
        vocab = self._get_attested()
        if not vocab:
            return False
        suffixes = self._get_suffixes()
        for w in re.findall(r"[a-z]+", arg):
            if 3 <= len(w) <= 5 and vocab.get(w, 0) < 2 and w in suffixes:
                return True
        return False

    def _prepare_arg(self, arg):
        """
        Strip articles/conjunctions, then rejoin attested OCR splits.
        Joined fragments make better facts than rejected ones ("ja cob
        had twelve sons" is about jacob); unjoinable debris dies later
        in the content/function-word gates.
        """
        arg = _clean_arg(arg)
        vocab = self._get_attested()
        if not vocab:
            return arg
        tokens = re.findall(r"[a-z]+", arg)
        if len(tokens) < 2:
            return arg
        try:
            from ukft_trigram import _join_fragments
            joined = _join_fragments(tokens, vocab)
        except Exception:
            joined = tokens
        return " ".join(joined) if joined != tokens else arg

    # ── KIN NAME JOINING ────────────────────────────────────────
    def _join_left(self, tokens, vocab):
        """
        The name ending at the token before a kin marker, with OCR
        syllables rejoined ("ma a cah" -> maacah).  The immediate
        token must stand on its own or be the tail of an attested
        join; a function word there means the marker has no subject
        ("the son of man", "and fathered").
        """
        tokens = list(tokens)
        while tokens and tokens[-1] in ("the", "a", "an"):
            tokens.pop()
        if not tokens:
            return None
        if tokens[-1] in FUNCTION_WORDS or tokens[-1] in REL_STOP:
            return None
        for k in range(min(4, len(tokens)), 1, -1):
            group = tokens[-k:]
            if len(group[0]) < 2:
                continue
            if any(t in FUNCTION_WORDS and len(t) > 2 for t in group[:-1]):
                continue
            cand = "".join(group)
            if cand in vocab:
                return cand
        return tokens[-1]

    def _join_right(self, tokens, vocab):
        """
        The name after a kin marker, joined forward ("abish a lom").
        Returns (name, tokens_consumed) so callers can look past it —
        a title between verb and name ("fathered king david") is
        skipped, not minted as the child.
        """
        tokens = list(tokens)
        skipped = 0
        while tokens and tokens[0] in KIN_Y_TITLES and len(tokens) > 1:
            tokens.pop(0)
            skipped += 1
        if not tokens:
            return None, 0
        if tokens[0] in FUNCTION_WORDS or tokens[0] in REL_STOP:
            return None, 0
        for k in range(min(4, len(tokens)), 1, -1):
            group = tokens[:k]
            if len(group[-1]) < 2:
                continue
            if any(t in FUNCTION_WORDS and len(t) > 2 for t in group[1:]):
                continue
            cand = "".join(group)
            if cand in vocab:
                return cand, k + skipped
        return tokens[0], 1 + skipped

    # ── MATCHING ────────────────────────────────────────────────
    def _fathered_pairs(self, sentence):
        """
        Every "X fathered Y" pair in the sentence (begat/begot kept for
        legacy corpora).  Handles the forms the strict splitter used to
        amputate: "cainan lived 130 years and fathered shelah" (the
        father is the subject before "lived"), "jesse fathered king
        david" (a title sits between verb and name), and "reaiah son of
        shobal fathered jahath" (the father is reaiah; shobal is the
        grandfather).  Names are rejoined from OCR splits.
        """
        vocab = self._get_attested()
        words = [m.group(0) for m in TOKEN_RE.finditer(sentence)]
        found = []
        for i, word in enumerate(words):
            if word not in FATHERED_VERBS:
                continue
            if i == 0 or i + 1 >= len(words):
                continue
            # "X son of Y fathered Z": the father is X, and X is the son
            # of Y.  The name before "fathered" is the grandfather.
            if (i >= 3 and words[i - 3] == "son" and words[i - 2] == "of"
                    and words[i - 1] not in REL_STOP):
                child = self._join_left(words[:i - 3], vocab)
                if child and _content_phrase(child):
                    found.append(("kin", "son_of", _clean_arg(child),
                                  _clean_arg(words[i - 1]),
                                  _confidence(0.90, child, words[i - 1])))
                    x = child
                else:
                    # The father's name could not be read; minting the
                    # grandfather as the father would be a wrong edge.
                    continue
            else:
                x = self._join_left(words[:i], vocab)
                # "cainan lived 130 years and fathered shelah": the verb
                # is conjoined, the subject sits before "lived".
                if (x is None and words[i - 1] == "and" and i >= 4
                        and words[i - 2] == "years"
                        and words[i - 3] == "lived"):
                    x = self._join_left(words[:i - 3], vocab)
            if (x is None or x in REL_STOP or x in KIN_X_STOP
                    or x in KIN_FRAGMENT_STOP or not _content_phrase(x)):
                continue
            y, _consumed = self._join_right(words[i + 1:], vocab)
            if (y is None or y in REL_STOP or y in KIN_Y_STOP
                    or y in KIN_FRAGMENT_STOP or not _content_phrase(y)):
                continue
            if _has_dup_words(x) or _has_dup_words(y):
                continue
            if self._has_fragment_word(x) or self._has_fragment_word(y):
                continue
            found.append(("kin", "father_of", _clean_arg(x), _clean_arg(y),
                          _confidence(0.92, x, y)))
        return found

    def _kin_scan(self, sentence):
        """
        Every "X ... son/daughter of Y" name pair in the sentence.  A
        verse can chain a whole genealogy; titles, vocatives, possessive
        fragments and OCR syllables are refused so only clean name
        pairs become kin edges.
        """
        vocab = self._get_attested()
        tokens = [(m.group(0), m.start(), m.end())
                  for m in TOKEN_RE.finditer(sentence)]
        found = []
        prev_y = None
        for m in KIN_RE.finditer(sentence):
            rel = m.group(2)
            left = [t for t, _s, e in tokens if e <= m.start()]
            right = [t for t, s, _e in tokens if s >= m.end()]
            x = self._join_left(left, vocab)
            y, consumed = self._join_right(right, vocab)
            if x is None or y is None:
                continue
            # "Jesus Christ, the son of David, the son of Abraham": the
            # article marks BOTH phrases as appositions of the same
            # subject — chaining them would mint father_of(david,
            # abraham).  A chain without articles ("Ethan, son of
            # Zimmah, son of Shimei") still links every name.
            if m.group(1) and x == prev_y:
                continue
            if x in KIN_X_STOP or y in KIN_Y_STOP:
                continue
            if x in KIN_FRAGMENT_STOP or y in KIN_FRAGMENT_STOP:
                continue
            if not (_content_phrase(x) and _content_phrase(y)):
                continue
            # "per son of any skill": x+rel is a whole word — the marker
            # is a syllable split, not a kin phrase.
            if x + rel in vocab:
                continue
            if _has_dup_words(x) or _has_dup_words(y):
                continue
            if self._has_fragment_word(x) or self._has_fragment_word(y):
                continue
            # "son of saul s uncle": the possessive shows the name after
            # "of" is not the parent.
            if consumed < len(right) and right[consumed] == "s":
                continue
            # A two-letter syllable right after the name ("pha nu el",
            # "jer ub besheth") means the name itself is an OCR split
            # that never appears whole in the corpus — refuse it.
            if (consumed < len(right) and len(right[consumed]) <= 2
                    and right[consumed] not in FUNCTION_WORDS):
                continue
            sub = "son_of" if rel == "son" else "daughter_of"
            found.append(("kin", sub, _clean_arg(x), _clean_arg(y),
                          _confidence(0.88, x, y)))
            prev_y = y
        return found

    # ── LIST / MATE / SIBLING SCANS (recall expansion) ──────────
    def _strip_list_title(self, name):
        """'chief Teman' -> 'teman': offices are not names."""
        words = [w for w in re.findall(r"[a-z]+", name)
                 if w not in LIST_NAME_TITLES]
        return " ".join(words)

    def _clean_list_name(self, raw):
        """
        One name out of a genealogy list.  Two-letter names must
        stand attested in the corpus ("uz"); anything shorter is
        an OCR syllable or footnote marker.  Ordinal tails
        ("Jahaziel third") are verse furniture, not names.
        """
        name = self._strip_list_title(self._prepare_arg(raw))
        name = _strip_trailing_func(name)
        # "Johanan was the firstborn": the census words trail the
        # name — strip was+ordinal/number before the gates run.
        name = re.sub(r"\s+was\s+(?:the\s+)?(?:" + "|".join(sorted(
            ORDINAL_TAIL)) + r")\s*$", "", name)
        # Parenthetical asides ride the chunk ("edom), ...") — the
        # token stream hides them, so the raw text is checked.
        if "(" in raw or ")" in raw:
            return None
        words = re.findall(r"[a-z]+", name)
        while words and words[-1] in ORDINAL_TAIL:
            words.pop()
        if not words:
            return None
        name = " ".join(words)
        if "," in name:
            return None
        if re.search(r"\d", name) or re.search(r"[^a-z ,'-]", name):
            return None
        words = re.findall(r"[a-z]+", name)
        if not words or len(words) > 3:
            return None
        if any(w in REL_STOP or w in GENERIC_NOUNS for w in words):
            return None
        for w in words:
            if (w in FUNCTION_WORDS or len(w) < 2
                    or not re.search(r"[aeiou]", w)):
                return None
            if len(w) == 2 and self._get_attested().get(w, 0) < 2:
                return None
        if name in KIN_X_STOP or name in KIN_FRAGMENT_STOP:
            return None
        if _has_dup_words(name) or self._has_fragment_word(name):
            return None
        return _clean_arg(name)

    def _clean_list_head(self, raw):
        """The parent a list belongs to ("japheth s" -> japheth)."""
        head = re.sub(r"\s*\(.*$", "", _clean_arg(raw))
        head = re.sub(r"\s+s$", "", head)
        head = self._prepare_arg(head)
        if not head or _word_count(head) > 2:
            return None
        if any(w in GENERIC_NOUNS
               for w in re.findall(r"[a-z]+", head)):
            return None
        if not _content_phrase(head) or not _valid_arg(head):
            return None
        if head in KIN_X_STOP or head in KIN_FRAGMENT_STOP:
            return None
        if _has_dup_words(head) or self._has_fragment_word(head):
            return None
        return _clean_arg(head)

    def _split_names(self, tail):
        """
        A verse tail into clean names: verse numbers, sentence ends,
        relative clauses and "to him/her" tails bound the list first.
        """
        tail = re.split(r"\s\d|[.!?;]", tail)[0]
        tail = LIST_CLAUSE_CUT.split(tail)[0]
        tail = re.sub(r"\s+to (him|her|them)\s*$", "", tail)
        tail = re.sub(r"^[\s:,]+", "", tail)
        tail = re.sub(r"^(?:were|are)\b\s+", "", tail)
        names = []
        for raw in LIST_SPLIT_RE.split(tail):
            name = self._clean_list_name(raw)
            if name:
                names.append(name)
                if len(names) >= MAX_LIST_NAMES:
                    break
        return names

    def _son_lists(self, sentence):
        """
        "Japheth's sons: Gomer, Magog..." / "These are the sons of
        Esau..." / "Shem's sons were Elam...".  First head shape
        wins; a tail with no clean names yields nothing.
        """
        for i, (head_rx, sub) in enumerate(SON_LIST_HEAD_RES):
            m = re.match(head_rx, sentence)
            if not m:
                continue
            head = self._clean_list_head(m.group(1))
            if not head:
                continue
            tail_raw = m.group(2)
            # Possessive heads ("Jacob's sons answered...") need a
            # list-bound tail: a colon/semicolon, or were/are into
            # names.  A bare comma never bounds ("Aaron's sons, the
            # priests are to arrange..." is a job description), and
            # "are to <verb>" is a verb phrase, not a census ("were
            # the Asshurim" stays — articles pass to the name gates).
            if i < 2 and not re.search(
                    r"[:;]|\b(?:were|are)\b(?!\s+to\b)", tail_raw):
                continue
            names = self._split_names(tail_raw)
            if not names:
                continue
            return [("kin", sub, n, head, _confidence(0.80, n, head))
                    for n in names]
        return []

    def _trailing_name(self, raw):
        """
        The name an apposition belongs to.  After the last "of"
        ("the tent of Jael") it is the single word there; otherwise
        the last word ("concubine Maacah").  Anything else is a
        clause with no mintable subject — downstream gates still
        apply (titles, pronouns, fragments all refuse).
        """
        seg = re.split(r"[,;:]", raw)[-1]
        toks = re.findall(r"[a-z]+", seg)
        if "of" in toks:
            toks = toks[len(toks) - 1 - toks[::-1].index("of") + 1:]
        if len(toks) != 1:
            tail = toks[-1:] if toks else []
            if not tail:
                return None
            if len(toks) > 1:
                # "concubine Maacah": leading descriptors fall away
                # only when every one is scaffolding.
                if any(w not in FUNCTION_WORDS and w not in REL_STOP
                       and w not in KIN_Y_TITLES
                       and w not in LIST_NAME_TITLES
                       and w != "concubine" and len(w) >= 3
                       for w in toks[:-1]):
                    return None
            toks = tail
        w = toks[0]
        if (len(w) < 3 or not re.search(r"[aeiou]", w)
                or w in FUNCTION_WORDS or w in REL_STOP):
            return None
        return w

    def _clean_mate_x(self, raw):
        """One named spouse/parent — never poetry ("joyful mother")."""
        x = self._trailing_name(raw) or ""
        x = self._prepare_arg(x)
        if not x or _word_count(x) != 1:
            return None
        if x in GENERIC_NOUNS:
            return None
        if not _content_phrase(x) or not _valid_arg(x):
            return None
        if x in KIN_X_STOP or x in KIN_FRAGMENT_STOP:
            return None
        if _has_dup_words(x) or self._has_fragment_word(x):
            return None
        return _clean_arg(x)

    def _clean_mate_y(self, raw):
        """Leading content run ("Heber the Kenite" -> heber)."""
        y = re.sub(r"\(.*$", "", raw)
        y = self._prepare_arg(y)
        run = []
        for w in re.findall(r"[a-z]+", y):
            if (len(w) < 3 or not re.search(r"[aeiou]", w)
                    or w in FUNCTION_WORDS or w in KIN_Y_TITLES):
                break
            run.append(w)
        if not run or len(run) > 2:
            return None
        y = " ".join(run)
        if any(w in GENERIC_NOUNS for w in run):
            return None
        if not _valid_arg(y):
            return None
        if y in KIN_Y_STOP or y in KIN_FRAGMENT_STOP:
            return None
        if _has_dup_words(y) or self._has_fragment_word(y):
            return None
        return _clean_arg(y)

    def _mate_scan(self, sentence):
        """
        "Jael, the wife of Heber" / "Maacah was the mother of
        Sheber" / "Naarah bore Ahuzzam, Hepher..." (lists ride
        the shared splitter).  "Wife of his bosom" dies on the
        X-side stops; "joyful mother of children" on the
        single-name rule.
        """
        for rx, fixed in MATE_RES:
            m = re.match(rx, sentence)
            if not m:
                continue
            if fixed is not None:
                x = self._clean_mate_x(m.group(1))
                if not x:
                    continue
                names = self._split_names(m.group(2))
                if not names:
                    continue
                return [("kin", fixed, x, n, _confidence(0.85, x, n))
                        for n in names]
            x = self._clean_mate_x(m.group(1))
            y = self._clean_mate_y(m.group(3))
            if not x or not y:
                continue
            sub = {"wife": "wife_of", "husband": "husband_of",
                   "mother": "mother_of"}[m.group(2)]
            return [("kin", sub, x, y, _confidence(0.85, x, y))]
        return []

    def _sibling_scan(self, sentence):
        """
        "Jada, brother of Shammai" — independent pairs with the
        kin-scan gates but no chaining: a brother marker followed
        by a son marker is two facts, never a chain.
        """
        vocab = self._get_attested()
        toks = [(w.group(0), w.start(), w.end())
                for w in TOKEN_RE.finditer(sentence)]
        found = []
        for m in SIB_RE.finditer(sentence):
            left = [t for t, _s, e in toks if e <= m.start()]
            right = [t for t, s, _e in toks if s >= m.end()]
            x = self._join_left(left, vocab)
            y, consumed = self._join_right(right, vocab)
            if x is None or y is None:
                continue
            if x in GENERIC_NOUNS or y in GENERIC_NOUNS:
                continue
            if x in KIN_X_STOP or y in KIN_Y_STOP:
                continue
            if x in KIN_FRAGMENT_STOP or y in KIN_FRAGMENT_STOP:
                continue
            if not (_content_phrase(x) and _content_phrase(y)):
                continue
            if _has_dup_words(x) or _has_dup_words(y):
                continue
            if self._has_fragment_word(x) or self._has_fragment_word(y):
                continue
            if consumed < len(right) and right[consumed] == "s":
                continue
            sub = "brother_of" if m.group(1) == "brother" \
                else "sister_of"
            found.append(("kin", sub, _clean_arg(x), _clean_arg(y),
                          _confidence(0.85, x, y)))
        return found

    def _loose_has(self, sentence):
        """
        The possessive form on a digit-unlocked sentence ("eber had two
        sons").  Same gates as the strict row, plus the speech-comma
        guard ("jesus said, have the people sit down" is an imperative,
        not a possession).
        """
        m = HAS_RE.match(sentence)
        if not m:
            return []
        raw_x, raw_y = m.group(1), m.group(2)
        if raw_x.rstrip().endswith(","):
            return []
        if not DETERMINER_RE.match(raw_y.strip()):
            return []
        x, y = self._prepare_arg(raw_x), self._prepare_arg(raw_y)
        y = _strip_trailing_func(y)
        if x in NARRATIVE_SUBJECTS or not _content_phrase(x):
            return []
        if (not _valid_arg(x) or not _valid_arg(y)
                or _word_count(x) > MAX_X_WORDS or _word_count(y) > 6
                or _has_dup_words(x) or _has_dup_words(y)
                or self._has_fragment_word(x) or self._has_fragment_word(y)):
            return []
        return [("has_property", "has", _clean_arg(x), _clean_arg(y),
                 _confidence(0.65, x, y))]

    def _gate_is_a(self, raw_x, raw_y, base, keep_conj=()):
        """
        The full is_a gate chain, shared by every is_a surface form:
        arg preparation, qualifier cuts, and the semantic rejections
        (stop-word rhetoric, inverted taxonomy, epithets, gerund
        headings, rhetorical appraisals, debris).
        """
        x, y = self._prepare_arg(raw_x), self._prepare_arg(raw_y)
        cut_y = _cut_is_a_y(y, keep=keep_conj)
        # Stop words in the pre-strip class phrase ("a great example
        # of this") are rhetorical, not taxonomy — trailing-strip must
        # not launder them away.
        if any(w in REL_STOP
               for w in re.findall(r"[a-z]+", cut_y)):
            return None
        y = _strip_trailing_func(cut_y)
        # Inverted taxonomy: a truncated chunk can yield "computer is
        # a neuromorphic computer" — the superset landed on the wrong
        # side.  Reject when the class is the subject plus extra words.
        if y.endswith(x) and len(y) > len(x):
            return None
        if _word_count(y) == 1 and y in EPITHET_STOP:
            return None
        # "the word public is a keyword" — the subject is "public";
        # the mention word is metalinguistic scaffolding.
        if x.startswith("word "):
            x = x[len("word "):]
            if not _content_phrase(x):
                return None
        # Gerund-headed subjects with a one-word class are section
        # headings, not definitions ("creating business solutions is
        # a multifaceted [process]").
        first = re.findall(r"[a-z]+", x)
        if (_word_count(y) == 1 and first
                and re.match(r"^[a-z]+ing$", first[0])):
            return None
        if _word_count(y) == 2 and y in EVAL_CHOICE:
            return None
        if x in NARRATIVE_SUBJECTS:
            return None
        if not _content_phrase(x):
            return None
        if (not _valid_arg(x) or not _valid_arg(y)
                or _word_count(x) > MAX_X_WORDS
                or _word_count(y) > 6
                or _has_dup_words(x) or _has_dup_words(y)
                or self._has_fragment_word(x)
                or self._has_fragment_word(y)):
            return None
        x, y = _clean_arg(x), _clean_arg(y)
        return [("is_a", "", x, y, _confidence(base, x, y))]

    def _match(self, sentence):
        """
        Return the relations a sentence yields.  Begat/fathered chains
        can yield several; anything else yields at most one — the first
        family whose pattern fits, with family-specific argument gates.
        """
        found = self._fathered_pairs(sentence)
        if found:
            return found
        m = WAY_RE.match(sentence)
        if m:
            return self._gate_is_a(
                m.group(1), f"{m.group(3)} {m.group(4)} {m.group(5)}", 0.85)
        m = EXAMPLE_RE.match(sentence)
        if m:
            return self._gate_is_a(
                m.group(1), m.group(3), 0.85, keep_conj=("and", "or"))
        m = REFERS_RE.match(sentence)
        if m:
            # A cut that lands on "and" leaves an adjective list
            # ("the divide refers to the uneven and unequal access"),
            # not a class — refuse that family member.
            words = re.findall(r"[a-z]+", self._prepare_arg(m.group(2)))
            first_cut = next((w for w in words if w in IS_A_Y_CUT), None)
            if first_cut == "and":
                return None
            return self._gate_is_a(m.group(1), m.group(2), 0.85)
        for typ, sub, regex, base, swap, max_y in PATTERNS:
            m = re.match(regex, sentence)
            if not m:
                continue
            raw_x, raw_y = m.group(1), m.group(2)
            if swap:
                raw_x, raw_y = raw_y, raw_x
            if sub == "has" and (not DETERMINER_RE.match(raw_y.strip())
                                 or raw_x.rstrip().endswith(",")):
                # "jesus said, have the people sit down" is an
                # imperative after a speech comma, not a possession.
                break
            # Apposition debris: "prophesy, son of man" is not kin —
            # the comma shows X is a title fragment, not a name.  The
            # chain scan below still gets a clean read on such verses.
            if typ == "kin" and "," in raw_x:
                break
            if typ == "is_a":
                return self._gate_is_a(raw_x, raw_y, base)
            x, y = self._prepare_arg(raw_x), self._prepare_arg(raw_y)
            if typ == "part_of":
                # A whole that still carries a mid-phrase article is a
                # mangled chunk ("operands an assembly language
                # program"), not a clean part/whole pair.
                if (re.search(r"\s(?:a|an|the)\s", x)
                        or re.search(r"\s(?:a|an|the)\s", y)):
                    break
            elif sub == "has":
                y = _strip_trailing_func(y)
            if typ == "kin":
                if not (_content_phrase(x) and _content_phrase(y)):
                    break
                if _word_count(x) > 3 or _word_count(y) > max_y:
                    break
            elif typ in ("causes", "located_in", "has_property"):
                if not _content_phrase(x):
                    break
                if typ == "has_property" and x in NARRATIVE_SUBJECTS:
                    break
            if (not _valid_arg(x) or not _valid_arg(y)
                    or _word_count(x) > MAX_X_WORDS
                    or _word_count(y) > max_y
                    or _has_dup_words(x) or _has_dup_words(y)
                    or self._has_fragment_word(x)
                    or self._has_fragment_word(y)):
                break
            x, y = _clean_arg(x), _clean_arg(y)
            return [(typ, sub, x, y, _confidence(base, x, y))]
        # No simple family fit: a genealogy chain can still live in the
        # sentence ("ethan, son of zimmah, son of shimei").
        return self._kin_scan(sentence) or None

    def _record(self, typ, sub, x, y, conf, sentence, concept):
        key = (typ, sub, x, y)
        entry = (conf, _evid(sentence, x, y), concept[:60])
        if key not in self.relations or conf > self.relations[key][0]:
            self.relations[key] = entry

    def extract(self):
        """Read every vault anchor (read-only) and mine it for relations."""
        for concept, data, _source in iter_anchors(self.vault_path):
            for sentence in _sentences(data):
                for typ, sub, x, y, conf in self._match(sentence) or []:
                    self._record(typ, sub, x, y, conf, sentence, concept)
            # Genealogies hide behind verse numbers and ages; the loose
            # splitter keeps those sentences whole.  Only kin names and
            # possessive "had" are mined from them — is_a on unlocked
            # poetry would need a metaphor gate that does not exist.
            for sentence in _kin_sentences(data):
                pairs = (self._fathered_pairs(sentence)
                         + self._kin_scan(sentence)
                         + self._son_lists(sentence)
                         + self._mate_scan(sentence)
                         + self._sibling_scan(sentence)
                         + self._loose_has(sentence))
                for typ, sub, x, y, conf in pairs:
                    self._record(typ, sub, x, y, conf, sentence, concept)
        self._resolve_comparisons()
        return self

    def _resolve_comparisons(self):
        """
        Opposite comparators on one (x, y) pair cannot both stand
        ("hashing is faster AND slower than binary search") — the lower
        confidence goes; exact ties drop both.  COMPATIBLE comparators
        ("greater" + "faster") are different facts and all survive.
        """
        opposites = {"greater_than": "less_than", "less_than": "greater_than",
                     "larger_than": "smaller_than", "smaller_than": "larger_than",
                     "heavier_than": "lighter_than", "lighter_than": "heavier_than",
                     "faster_than": "slower_than", "slower_than": "faster_than",
                     "more_massive_than": "less_massive_than",
                     "less_massive_than": "more_massive_than"}
        by_pair = {}
        for key in [k for k in self.relations if k[0] == "compare"]:
            by_pair.setdefault((key[0], key[2], key[3]), []).append(key)
        for pk, keys in by_pair.items():
            for i, ka in enumerate(keys):
                for kb in keys[i + 1:]:
                    sa, sb = ka[1], kb[1]
                    if opposites.get(sa) != sb:
                        continue
                    if ka not in self.relations or kb not in self.relations:
                        continue
                    ca, cb = (self.relations[k][0] for k in (ka, kb))
                    if ca > cb:
                        del self.relations[kb]
                    elif cb > ca:
                        del self.relations[ka]
                    else:
                        del self.relations[ka]
                        del self.relations[kb]

    # ── PERSISTENCE ─────────────────────────────────────────────
    def save(self):
        lines = [
            kv for kv in self.relations.items() if kv[1][0] >= MIN_REL_CONF
        ]
        lines.sort(
            key=lambda kv: (-kv[1][0], kv[0][0], kv[0][1], kv[0][2], kv[0][3]),
        )
        out = [f"--- AURA EXTRACTED RELATIONS (V5 R1) | KNOWN: {len(lines)} "
               f"| TS: {int(time.time())} ---"]
        for (typ, sub, x, y), (conf, evid, src) in lines:
            name = f"{typ}:{sub}" if sub else typ
            # The vault's own chunk markers are pipes — an evidence
            # string carrying one would corrupt this file's delimiter
            # format.  Sanitize on write.
            safe_evid = evid.replace("|", "/")
            safe_src = src.replace("|", "/")
            out.append(f"REL: {name} | X: {x} | Y: {y} | CONF: {conf:.2f} "
                       f"| EVID: {safe_evid} | SRC: {safe_src}")
        bus_write(self.out_path, "\n".join(out) + "\n")
        return len(lines)

    def load(self):
        """Read back a saved relations file (tests + future R2 consumer)."""
        try:
            with open(self.out_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.startswith("REL: "):
                        continue
                    name, _sep, rest = line[len("REL: "):].rstrip("\n").partition(" | ")
                    parts = dict(
                        p.split(": ", 1) for p in rest.split(" | ") if ": " in p
                    )
                    if not name or "X" not in parts or "Y" not in parts:
                        continue
                    typ, _, sub = name.partition(":")
                    try:
                        conf = float(parts.get("CONF", "0.0"))
                    except (ValueError, TypeError):
                        # One corrupt line skips itself — it must never
                        # abort the loop and drop every line after it.
                        continue
                    evid = parts.get("EVID", "")
                    src = parts.get("SRC", "")
                    key = (typ, sub, parts["X"], parts["Y"])
                    if (key not in self.relations
                            or conf > self.relations[key][0]):
                        self.relations[key] = (conf, evid, src)
        except OSError:
            pass
        return self

    def summary(self):
        return collections.Counter(k[0] for k in self.relations)


def run_extraction(vault_path=VAULT_FILE, out_path=EXTRACTED_RELATIONS):
    engine = RelationExtractor(vault_path, out_path).extract()
    written = engine.save()
    written_by_type = collections.Counter(
        k[0] for k, v in engine.relations.items() if v[0] >= MIN_REL_CONF
    )
    print(f"[R1] vault scanned (read-only): {vault_path}")
    print(f"[R1] relations written: {written} -> {out_path}")
    for typ, count in sorted(written_by_type.items()):
        print(f"      {typ:14s} {count}")
    return engine


if __name__ == "__main__":
    vault = sys.argv[1] if len(sys.argv) > 1 else VAULT_FILE
    out = sys.argv[2] if len(sys.argv) > 2 else EXTRACTED_RELATIONS
    run_extraction(vault, out)
