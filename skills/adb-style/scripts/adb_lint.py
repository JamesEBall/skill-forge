#!/usr/bin/env python3
"""Flag candidate violations of the ADB Handbook of Style and Usage (2024).

Usage:
    python3 adb_lint.py FILE [FILE ...]
    cat draft.md | python3 adb_lint.py -
    python3 adb_lint.py --board FILE      # also flag first person (Board documents)

Reads plain text or Markdown and prints one line per hit:

    file:line:col  [rule]  "matched text"  ->  advice

Every hit is a candidate, not a verdict. The checks are regular expressions and
cannot tell a quotation, a publication title, or an organization's official
name from running text. A clean run does not mean the text complies: the rules
that need counting or judgment (three-uses rule for abbreviations, first-mention
spell-outs, parallel lists, active voice) are not checked here.

Standard library only. Exit status is 0 whether or not there are hits.
"""

import re
import sys

I = re.IGNORECASE
MONTHS = (
    r"(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)"
)
SMALL = r"(?:ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)"

# (rule id, compiled pattern, advice)
RULES = [
    # --- ADB and member names -------------------------------------------------
    ("adb-name", r"\b[Tt]he Bank\b", 'use "ADB" or "the bank"'),
    ("adb-name", r"\b[Tt]he ADB\b(?!['’]s\b)(?= (?:is|was|has|had|will|should|would|can|may|must|and|or|to|in|on|for|with|approved|provided|supports?|plans?)\b)", '"ADB" takes no article'),
    ("members", r"\bADB member countries\b", 'use "ADB members"'),
    ("members", r"\bPDMCs?\b", 'use "Pacific DMCs" or "Pacific developing member countries"'),
    ("members", r"\b(?:the )?Asia[- ]Pacific\b(?! Economic Cooperation)", 'use "Asia and the Pacific"'),
    ("members", r"(?<!Republic of )(?<!Hong Kong, )(?<!Taipei,)(?<!South )(?<!East )\bChina\b(?! Sea)(?!,? People)", 'use "the People\'s Republic of China" or "the PRC"'),
    ("members", r"\bHong Kong\b(?!, China| dollar| Special Administrative| and Shanghai)", 'use "Hong Kong, China"'),
    ("members", r"\bTaiwan\b|\bTaipei, China\b|\bChinese Taipei\b", 'use "Taipei,China" (no space after the comma)'),
    ("members", r"\b(?:South Korea|Korea Republic)\b|(?<!Republic of )(?<!Bank of )\bKorea\b(?!, Republic)", 'use "the Republic of Korea" or "the ROK"'),
    ("members", r"\bLaos\b|\bLao P\.D\.R\.", 'use "the Lao People\'s Democratic Republic" or "the Lao PDR"'),
    ("members", r"\bVietnam(?:ese)?\b", 'use "Viet Nam" (two words)'),
    ("members", r"\bKyrgyzstan\b", 'use "the Kyrgyz Republic"'),
    ("members", r"(?<!States of )\bMicronesia\b(?!, Federated)", 'use "the Federated States of Micronesia" or "the FSM"'),
    ("members", r"\bBrunei\b(?! Darussalam| dollar)", 'use "Brunei Darussalam"'),
    ("members", r"\bTurkey\b", 'use "Türkiye"'),
    ("members", r"\bNauru\b", 'Appendix 1 gives "Naoero"; check the online handbook'),
    ("members", r"\b(?:East Timor|Burma)\b", 'use "Timor-Leste" / "Myanmar"'),
    ("members", r"\bthe (?:Solomon Islands|Maldives)\b", "no definite article"),
    ("members", r"\bThird World\b|\bSouth[–-]South\b", "say developing countries / among developing members"),
    # --- capitalization -------------------------------------------------------
    ("caps", r"\bthe Government\b(?! of)", 'lowercase "the government" unless the full formal name follows'),
    ("caps", r"\((?:the |“|\")*(?:Project|Program|Government|Bank|Borrower)(?:”|\")?\)", "do not define a capitalized short form in parentheses"),
    ("caps", r"(?<=[a-z,;] )the (?:Project|Program|Ministry|Mission|Act|Bill|Borrower|Executing Agency|Implementing Agency)\b(?! (?:for|of|on|to) [A-Z])", "lowercase the short form"),
    ("caps", r"\b(?:Component|Output|Tranche|Subprogram|Subproject|Tier) \d\b", "lowercase unless part of a formal title"),
    ("caps", r"\b(?:Executing|Implementing) Agenc(?:y|ies)\b|\bTechnical Assistance\b(?! (?:Special Fund|Completion Report|Report|to|for)\b)|\bCountry Partnership Strategy\b(?!:)|\bResident Mission\b(?<![A-Z][a-z] Resident Mission)", "lowercase generic ADB terms"),
    ("caps", r"\bInternet\b|\bIntranet\b", 'lowercase "internet", "intranet"'),
    ("caps", r"\b(?:Mr|Mrs|Ms|Dr|Prof)\.? (?=[A-Z])", "no honorific titles"),
    ("caps", r"\bHeadquarters\b", 'lowercase "headquarters"'),
    # --- abbreviations --------------------------------------------------------
    ("abbr", r"\b(?:Ph\.D\.?|(?:[A-Z]\.){2,})", "no periods in abbreviations"),
    ("abbr", r"\b(?:MoF|MoU|MoA|SoE|MoH|MoE|NGOs?')\b", "abbreviations in all capitals; no apostrophe plurals"),
    ("abbr", r"\b[A-Z]{2,}'s\b(?= (?:are|were|have)\b)", "no apostrophe in plural abbreviations"),
    ("abbr", r"\bTAs\b|\b(?:a|an|each|every|one|two|three|four|five|several|many) TA\b(?! (?:project|grant|report|loan|facility|cluster|program|team|completion|consultant|resources?|funds?|number)s?\b)", '"TA" is uncountable: "a TA project", "four TA projects"'),
    ("abbr", r"\b(?:e\.g|i\.e)\.(?!,)|\b(?:eg|ie)\b[.,]?(?= )|\betc\b(?!\.)", '"e.g.," and "i.e.," with periods and a following comma'),
    ("abbr", r"\b(?:GOB|GOI|GOP|GON|GOSL|GOV|RGC|GoB|GoI|GoP|GoN|GoSL)\b", 'do not abbreviate national governments; use "the government"'),
    ("abbr", r"\b(?:ATM machine|PIN number|World Wide Web|PCs?\b)", "ATM, PIN, web, computer"),
    ("abbr", r"(?<![A-Z])&(?![A-Z]\b)|\b(?![EMORS]&[SAEMDP]\b)[A-Za-z]+ & [A-Za-z]+", 'spell out "and" (ampersands only in E&S, M&A, M&E, O&M, R&D, S&P)'),
    ("abbr", r"\bsmall and medium(?:-sized| sized)? enterprises\b(?<!medium-sized enterprises)|\bnon-?governmental organi[sz]ations?\b|\boperations? (?:and|&) maintenance\b(?<!operation and maintenance)|\binformation and communications technolog", "check exact expansion in references/abbreviations.md"),
    # --- spelling and word forms ---------------------------------------------
    ("spelling", r"\b\w+(?:isation|ise[ds]?|ising)\b(?<!\bpromise)(?<!\bpremise)(?<!\bpremises)(?<!\bexpertise)(?<!\bexercise)(?<!\bexercises)(?<!\bexercised)(?<!\bexercising)(?<!\bpromised)(?<!\bpromises)(?<!\bpromising)(?<!\bcomprise)(?<!\bcomprises)(?<!\bcomprised)(?<!\bcomprising)(?<!\braise)(?<!\braised)(?<!\braises)(?<!\braising)(?<!\barise)(?<!\barises)(?<!\barising)(?<!\bsurprise)(?<!\bsurprised)(?<!\bsurprising)(?<!\benterprise)(?<!\benterprises)(?<!\bsupervise)(?<!\bsupervised)(?<!\bsupervises)(?<!\bsupervising)(?<!\badvise)(?<!\badvised)(?<!\badvises)(?<!\badvising)(?<!\brevise)(?<!\brevised)(?<!\brevises)(?<!\brevising)(?<!\bcompromise)(?<!\bcompromised)(?<!\bdevise)(?<!\bdevised)(?<!\bprecise)(?<!\bconcise)(?<!\botherwise)(?<!\blikewise)(?<!\bwise)(?<!\bfranchise)(?<!\bmerchandise)(?<!\badvertise)(?<!\badvertised)(?<!\badvertising)(?<!\bdisguise)(?<!\bdisguised)(?<!\bnoise)(?<!\bpraise)(?<!\bpraised)(?<!\bappraise)(?<!\bappraised)(?<!\bapprise)(?<!\bapprised)(?<!\bexcise)(?<!\bparadise)(?<!\btreatise)(?<!\bcruise)(?<!\bimprovise)(?<!\btelevise)(?<!\btelevised)(?<!\bdemise)", "American spelling (-ize, -ization) unless an official name or title"),
    ("spelling", r"\b(?:programmes?|labour|colou?red|colours?|centres?|favou?rable|behaviour|neighbour\w*|harbours?|metres?|kilometres?|litres?|tonnes?|defence|licence|ageing|judgement|fulfil|enrol(?:ment)?|travell(?:ed|ing)|modell(?:ed|ing)|labell(?:ed|ing)|cancell(?:ed|ing)|analys(?:e|ed|ing)|catalogue|dialog\b|grey|cheques?|whilst|amongst|towards)\b", "American spelling (Merriam-Webster main entry) unless an official name or title"),
    ("spelling", r"\b(?:multi)?sectoral\b|\b(?:agricultural|educational|financial|industrial) (?:sub)?sector\b", '"sector"/"multisector"; agriculture, education, finance, industry sector'),
    ("spelling", r"\b(?:e-mail|on-line|off-shore|co-financ\w+|sub-projects?|sub-regions?|sub-programs?|multi-tranche|multi-sector\w*|non-government\w*|non-sovereign|non-performing|non-revenue|non-tariff|non-bank|socio-economic|macro-economic|micro-finance|inter-agency|mid-term|pre-qualification|re-allocat\w+|semi-annual|cross-cutting|ground-water|land-locked|stake-holders?|on-lend\w*|re-lend\w*|anti-corruption|web site|data base)\b", "ADB closes this compound"),
    ("spelling", r"\b(?:formulae|fora|symposiums|focuses(?= of| on which)|minima|appendices|indices(?! of refraction))\b", "plural form: formulas, forums, symposia, foci, minimums, appendixes"),
    ("spelling", r"[®™]", "omit trademark symbols"),
    ("spelling", r"\banticorruption\b(?! [a-z])", '"anticorruption" is an adjective; add a noun'),
    # --- clear writing --------------------------------------------------------
    ("wordy", r"\b(?:in order to|due to the fact that|despite the fact that|in spite of the fact that|on account of the fact that|for the purpose of|for the reason that|in the event that|by means of|as a means of|as to whether|at this (?:particular )?point in time|in the field of|in the majority of instances|inasmuch as|a (?:large|certain) (?:proportion|amount|number) of|an adequate number of|has the capability to|in conjunction with|in reference to|attached herewith|few in number|fully understand|during the time that|afford an opportunity|in view of the foregoing)\b", "wordy; see references/word-lists.md"),
    ("wordy", r"\b(?:whether or not|each and every|a total of|end result|future prospects|past experience|new innovations?|revert(?:ed|s)? back|recur(?:s|red)? again|collaborat\w+ together|blend\w* together|close proximity|general public|completely destroyed|consensus of opinion|exact same|advance reservations?|forward planning|time period|during the (?:course|period) of|during the period|in the process of|the months? of|critically important|current incumbent|specific details|each individual|main focus|dates? back to|slow(?:ed|s)? down|small in size|temporary reprieve|foreign imports|knowledgeable experts?|all things being equal|basically)\b", "redundant wording"),
    ("wordy", r"\bat the (?:\w+ )?level\b|\b(?:implementation|design|planning|construction) (?:stage|phase)\b|\b(?:private|public|transport|energy|health|education) sector (?:companies|workers|firms|employees)\b", 'drop "level", "stage", "phase", "sector" where they add nothing'),
    ("cliche", r"\b(?:going forward|level playing field|on the ground|hit the ground running|silver bullet|low-hanging fruit|piggy-?backed|knowledge products?|game[- ]changer|paradigm shift)\b", "cliché or jargon"),
    ("latin", r"\b(?:inter alia|vis-[aà]-vis|ex[- ]ante|ex[- ]post|de facto|de jure|ceteris paribus|sine qua non|sui generis|ibid\.?|op\.? ?cit\.?)\b", "use plain English; cross-refer by footnote number, not ibid./op. cit."),
    ("lists", r"\brespectively\b|\bnamely\b|\bthe former\b.{0,80}\bthe latter\b", "restate the pairs; delete namely"),
    ("gender", r"\b(?:chairm[ae]n|chairwom[ae]n|chairpersons?|businessm[ae]n|fisherm[ae]n|forem[ae]n|mankind|man-made|manmade|manpower|man-(?:hour|day|month|year)s?|middlem[ae]n|workmanship|his/her|his or her|he/she|he or she|s/he|sister (?:company|organization)s?)\b|\b(?:two|three|four|five|six)-man\b", "gender-neutral wording; see references/word-lists.md"),
    ("health", r"\bHIV/AIDS\b|\bHIV and AIDS\b|\b(?:TB|bird flu)\b", "say HIV or AIDS, whichever is meant; spell out disease names"),
    ("xref", r"\(\s*(?:see|refer to|details? (?:are|can be found) in)\b|\bsee (?:Table|Figure|Appendix|Annex|Box|Map|para|footnote|section|chapter)\b|\b(?:Table|Figure|Section|section|paragraph|para\.?)s? (?:[\dIVXA.]+ )?(?:above|below)\b|\b(?:mentioned|referred to|discussed|described|noted) (?:above|below)\b", 'no "see", "above", "below"; give the paragraph, table, or appendix number'),
    ("sources", r"\bStaff estimates\b|\bwikipedia\b", 'use "Asian Development Bank estimates"; Wikipedia is not a source'),
    # --- numbers --------------------------------------------------------------
    ("numbers", r"\bper ?cent(?:age)?\b(?<!percentage)", 'use "%"'),
    ("numbers", r"\d ?(?:bn|mn|m|b)\b(?!\d)(?<!\d m)|\b\d[\d,.]* (?:mln|bln|mio)\b", 'spell out "million", "billion"'),
    ("numbers", r"\b(?:lakhs?|crores?)\b", "convert to thousands or millions"),
    ("numbers", r"(?:(?<=[.!?] )|^)(?:[$€£¥₱₹]?\d)", "do not start a sentence with a numeral; recast"),
    ("numbers", r"(?:(?<=[.!?] )|^)(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty|Thirty|Forty|Fifty|Sixty|Seventy|Eighty|Ninety)(?:-\w+)? (?:percent|hundred|thousand|million|\w+s\b)", "number at the start of a sentence: recast so a numeral can be used"),
    ("numbers", r"(?<![\d.])\.\d", "leading zero before the decimal point"),
    ("numbers", r"\b\d{1,3},\d{1,2}\b(?!,)(?=\s?%)", "decimal point, not comma"),
    ("numbers", r"(?<![\d,.$–-])\b[1-9]\d{4,}\b(?![\d,.]*\d)(?!-)", "comma every three digits above 999"),
    ("numbers", r"\b(?:[1-9])(?:st|nd|rd|th)\b", "spell out ordinals first to ninth"),
    ("numbers", r"\b(?:twentieth|twenty-first|nineteenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|twenty-\w+th)\b", "numerals for ordinals 10th and above (20th century)"),
    ("numbers", r"(?<![A-Z-])\b" + SMALL + r"(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?\b(?! percent)", "numerals for 10 and above (unless starting a sentence; then recast)"),
    ("numbers", r"\b(?:one|two|three|four|five|six|seven|eight|nine) (?:percent|per cent|%|million|billion|trillion|years?|months?|weeks?|days?|hours?|decades?|person-months?|kilometers?|km|hectares?|ha|meters?|kg|tons?|MW|kV)\b", "numerals with units, time, percentages, and million/billion"),
    ("numbers", r"\b(?:dipped|fell|rose|increased|decreased|declined|grew|dropped|cut|up|down) (?:by )?\d+(?:\.\d+)?%[ ,—–-]{1,3}(?:from|to) \d", "difference between percentages: percentage points or basis points"),
    # --- currencies -----------------------------------------------------------
    ("currency", r"\b(?:USD|US\$|U\.S\.\$|AUD|EUR|GBP|JPY|INR|PHP|IDR|VND|PKR|BDT|NPR|LKR|THB|MYR|SGD|KRW|NZD|CAD|CHF)\s?\d", "ADB currency symbol, closed up ($, A$, €, £, ¥, ₹, ₱, Rp, D, PRs, Tk, NRs, SLRs, B, RM, S$, W, NZ$, Can$, SwF)"),
    ("currency", r"(?:[$€£¥₱₹]|\b(?:Rp|Tk|PRs|NRs|SLRs|Rs|SDR|RM|Nu|KR|KN|MK|Vt)) \d", "no space between currency symbol and amount"),
    ("currency", r"\b\d+ (?:cents?|pence|paise)\b", "express as a decimal of the main unit ($0.40)"),
    ("currency", r"\b(?:Dollars?|Rupees?|Rupiah|Taka|Pesos?|Yuan|Renminbi|Baht|Dong|Kip|Riels?|Ringgit|Euros?|Yen|Won|Special Drawing Rights)\b(?<![A-Z][a-z]{2}\. Dollar)", "currency names are lowercase"),
    ("currency", r"\b\d[\d,.]* (?:million|billion|thousand)? ?(?:US |U\.S\. )?dollars\b", 'use "$" with the amount'),
    # --- dates and time -------------------------------------------------------
    ("dates", MONTHS + r" \d{1,2}(?:st|nd|rd|th)?,? \d{4}", "day month year: 26 January 2022"),
    ("dates", r"\b\d{1,2}(?:st|nd|rd|th)(?: of)? " + MONTHS, "no ordinals in dates"),
    ("dates", r"\b0\d " + MONTHS, "no leading zero in dates"),
    ("dates", r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", "write dates as 5 July 2024"),
    ("dates", r"\b(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.", "three-letter month without a period (tables only)"),
    ("dates", r"\b(?:last|next|this|the (?:past|previous|coming)) (?:year|month|quarter|decade|week)\b|\b(?:over|in|during|for) the (?:past|last|next) (?:\w+ )?(?:years?|months?|decades?)\b|\b\w+ (?:years?|months?) ago\b|\b(?:recently|currently|at present|nowadays|to date)\b", "give the actual date or period"),
    ("dates", r"\b(?:start|end|mid|early|late)[- ]\d{4}\b|\b(?:end|start|beginning)-(?:of-)?(?:year|quarter|period)\b", '"the end of 2024", not shorthand'),
    ("dates", r"\bFY ?\d{2}\b(?!\d)|\bFY \d{4}\b|\bfiscal year \d{4}\b", '"FY2024", defined at first use'),
    ("dates", r"['’]\d0s\b|\b\d{3}0['’]s\b|\b(?:twenties|thirties|forties|fifties|sixties|seventies|eighties|nineties)\b", "decades as 1990s"),
    ("dates", r"\b(?:early|mid-?|late) ?20[01]0s\b|\bthe 20[01]0s\b", "for the first two decades of a century give the year range (2000–2009)"),
    ("dates", r"\b(?:first|second|third|fourth|1st|2nd|3rd|4th) quarter\b(?= of \d{4}).*\b(?:first|second|third|fourth) quarter\b.*\bquarter\b", "three or more quarter references: use Q1, Q2"),
    ("time", r"\b\d{1,2}[:.]\d{2} ?(?:hrs?|H)\b|\b\d{4} ?(?:hrs?|H)\b|\b(?:1[3-9]|2[0-3])[:.]\d{2}\b|\b0\d:\d{2}\b", "12-hour clock: 6:30 p.m."),
    ("time", r"\b\d{1,2}(?:[:.]\d{2})? ?(?:am|pm|AM|PM|A\.M\.|P\.M\.)(?![a-z])|\b12(?::00)? ?(?:a\.m\.|p\.m\.|noon|midnight)|\b\d{1,2}:00 ?[ap]\.m\.", '"9 a.m.", "6:30 p.m.", "noon", "midnight"'),
    # --- ranges and dashes ----------------------------------------------------
    ("ranges", r"(?<![\w/.-])\d[\d,.]*%?-\d[\d,.]*(?![\w-])(?!\.\d)", "en dash for number ranges"),
    ("ranges", r"\d–\d[\d,.]*%|\d–\d[\d,.]* ?%", "repeat the % sign: 12%–14%"),
    ("ranges", r"[$€£¥₱₹]\d[\d,.]*[–-]\d[\d,.]* (?:million|billion|trillion)|[$€£¥₱₹]\d[\d,.]*[–-]\d", "repeat symbol and magnitude: $8 million–$9 million"),
    ("ranges", r"\bfrom [$€£¥₱₹]?\d[\d,.]*%?(?: \w+)?[–-]|\bbetween [$€£¥₱₹]?\d[\d,.]*%?(?: \w+)?[–-]", 'do not mix "from"/"between" with a dash'),
    ("ranges", r"\bbetween \d{4} and \d{4}\b", '"from 2000 to 2016" or "during 2000–2016"'),
    ("ranges", r"\b\d+ ?(?:kWh|MW|km|kg|ha|kV|GWh|MWh|m|t)[–-]\d+ ?(?:kWh|MW|km|kg|ha|kV|GWh|MWh|m|t)\b", "unit once, after the second number: 15–20 kWh"),
    ("ranges", r"\b(?:ranging|range[sd]?|everything) from\b", '"from ... to" only for a true continuum'),
    ("dashes", r"\w ?-- ?\w| – | — |(?<=\S) - (?=\S)", "em dash with no spaces for a break in thought"),
    ("dashes", r"\b(?:public-private|cost-benefit|debt-equity|demand-supply|equity-loan|reserve-loan)\b", "en dash between equal elements: public–private, cost–benefit"),
    ("dashes", r"(?<![\w–-])-\d", "en dash for negative numbers in text"),
    # --- units ----------------------------------------------------------------
    ("units", r"\b\d[\d,.]* ?(?:kgs|kms|hrs|has|mts|MWs|kVs|lbs)\b|\b\d[\d,.]* ?(?:ha|kg|km|cm|mm|kV|kW|MW)\.(?= [a-z])", "units: singular, no period"),
    ("units", r"\b\d[\d,.]*-(?:kV|kW|MW|km|ha|kg|m|MVA|kWh|GWh)\b", "no hyphen with an abbreviated unit: 11 kV line"),
    ("units", r"\b\d[\d,.]* (?:kilovolt|kilometer|hectare|megawatt|kilogram|meter|year|month|day)(?= (?:line|road|field|plant|plan|project|period|term|bridge|pipeline|canal)\b)", "hyphenate a spelled-out unit used as an adjective: 11-kilovolt line"),
    ("units", r"\b\d[\d,.]* ?(?:miles?|acres?|feet|inch(?:es)?|yards?|pounds? (?=of)|gallons?|°F)\b", "ADB uses the metric system"),
    # --- punctuation ----------------------------------------------------------
    ("punct", r"\b(?!Kong, China)\w+, \w+(?:[ -]\w+)? (?:and|or) \w+(?<!and and)", "check for the serial (Oxford) comma"),
    ("punct", r"(?<=[.!?])  +(?=\S)", "one space after a sentence"),
    ("punct", r"[A-Za-z]{3,}/[A-Za-z]{3,}(?<!and/or)(?<!HIV/AIDS)(?![\w.]*\.(?:org|com|net|int|gov|pdf|html?))", 'replace the slash with "and", "or", or "and/or"'),
    ("punct", r"\([^()]*\([^()]*\)[^()]*\)", "avoid parentheses within parentheses"),
    ("punct", r"(?<![\w.])‘[^’]{2,80}’(?![a-z])|(?<![\w.])'[^'\n]{2,80}'(?![a-z])", "double quotation marks (single only inside a quotation)"),
    ("punct", r"[”\"][.,](?!\d)", "periods and commas go inside the closing quotation mark"),
    ("footnotes", r"\w(?:\[\^?\d+\]|\^\d+\^?)[.,;:]", "footnote number after the punctuation mark"),
]

BOARD_RULES = [
    ("person", r"\b(?:[Ww]e|[Oo]urs?|us)\b", "third person in Board documents: ADB, the team, the government"),
    ("lists", r"^\s*[-*•] ", "no bullets in the text of Board documents; use (i), (ii), (iii)"),
]


def compile_rules(rules):
    out = []
    for rule_id, pattern, advice in rules:
        flags = re.MULTILINE
        # Name and capitalization rules are case-sensitive; the rest are not.
        if rule_id in {"wordy", "cliche", "latin", "lists", "gender", "xref", "sources"}:
            flags |= I
        out.append((rule_id, re.compile(pattern, flags), advice))
    return out


URL = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+")


def lint(name, text, rules):
    hits = 0
    in_code = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        # Blank out URLs and email addresses so they do not trip the checks.
        scan = URL.sub(lambda m: " " * len(m.group()), line)
        for rule_id, pattern, advice in rules:
            for m in pattern.finditer(scan):
                if not m.group().strip():
                    continue
                hits += 1
                shown = m.group().strip()
                if len(shown) > 60:
                    shown = shown[:57] + "..."
                print(f'{name}:{lineno}:{m.start() + 1}  [{rule_id}]  "{shown}"  ->  {advice}')
    return hits


def main(argv):
    args = [a for a in argv[1:] if a != "--board"]
    board = "--board" in argv[1:]
    if not args or args[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    rules = compile_rules(RULES + (BOARD_RULES if board else []))
    total = 0
    for path in args:
        if path == "-":
            name, text = "<stdin>", sys.stdin.read()
        else:
            name = path
            with open(path, encoding="utf-8") as f:
                text = f.read()
        total += lint(name, text, rules)
    print(f"\n{total} candidate(s). Each is a question, not a verdict; "
          "a clean run does not prove compliance.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
