---
name: adb-style
description: Review a draft against the Asian Development Bank (ADB) Handbook of Style and Usage (2024 edition) and rewrite it to comply. Covers clear writing, abbreviations, ADB member names, capitalization, currencies, dates, numbers, ranges, punctuation, lists, footnote references, tables, figures, and nondiscriminatory language. Use when asked to check, edit, copyedit, or "ADB-style" a document, or when drafting anything for ADB - Board documents (RRPs, TA reports, CPS, concept papers), publications, working papers, consultant reports, briefs, web or social media text.
---

# ADB Style

Source: ADB, *Handbook of Style and Usage*, 2024 edition (online version updated 13 October 2026), <https://www.adb.org/sites/default/files/institutional-document/31385/hsu-2024.pdf>. Where the handbook is silent, ADB follows *The Chicago Manual of Style* (17th ed.) for style and Merriam-Webster Online for spelling (main entry, not the variant). Member names and currencies change; if a name looks out of date, check the online handbook.

The job has two halves: review the content, then change it. Do both. A list of problems without a corrected text is half the work.

## Procedure

1. **Fix the scope.** Work out what kind of document it is: Board document (RRP, TA report, CPS, concept paper, completion report), publication (book, report, working paper), web page, social media post, or something else. Text rules apply to all of them. The layout rules (heading numbering, paragraph numbering, font sizes, page numbers, table format) are mandatory only for Board documents; publications may follow them. If the type is unclear and it matters, assume a Board document's text rules and leave the layout alone.
2. **Read the whole text once before changing anything.** While reading, build three inventories:
   - every abbreviation, with how often it appears in each part (front matter, main text, each appendix, each table, figure, and box);
   - every ADB member, country, organization, project, and currency named;
   - every date, year range, number with a unit, and citation.
3. **Run the linter on long texts** (optional, plain text or Markdown): `python3 scripts/adb_lint.py FILE`. It prints candidate violations by line. It cannot see context, so treat each hit as a question, and do not treat a clean run as a pass.
4. **Review.** Go through the checklist below section by section and note each violation with its location.
5. **Revise.** Apply the fixes in this order, because earlier passes remove text that later passes would otherwise polish: clear writing, then names and terminology, then abbreviations, then mechanics (numbers, dates, currencies, ranges, punctuation, capitalization), then lists, cross-references, footnotes, tables, and figures.
6. **Recheck the result.** Abbreviations are the usual casualty of editing: after cuts, recount each one against the three-uses rule and make sure the first appearance in each part is still the spelled-out one.
7. **Deliver** three things: the revised text in the same format it arrived in; a short change summary grouped by rule (not line by line, unless asked); and a list of queries for the author covering anything in "Flag, do not guess".

When the input is a file (.docx, .md, .tex), edit the file and keep its structure, numbering, and markup. When asked only to review, stop after step 4 and report findings with the proposed fix for each.

## Do not change

- Quoted material. Keep its spelling, capitalization, and wording. Insert "[sic]" only if asked.
- Titles of cited documents and publications. Keep the original spelling.
- Official names of organizations, even when they use non-American spelling (International Labour Organization, United Nations Development Programme, Organisation for Economic Co-operation and Development).
- Formal names of laws, plans, and projects, including numbering already in use (National Highway Sector II Project).
- Data. Never alter a figure to make a table sum; raise it.
- Legal documents, minutes, chair's summaries, and annual-meeting texts, which have their own capitalization and honorific conventions.
- Established publications (*Asian Development Outlook*, *Key Indicators*) that present negative numbers their own way.

## Flag, do not guess

Put these in the author queries instead of inventing an answer:

- Relative time ("last year", "recently", "3 years ago", "the early 2000s") where the actual date or year range is not in the text.
- An abbreviation whose spelled-out form you do not know for certain.
- A table, figure, or quotation with no source; a quotation with no page number.
- Numbers in text that disagree with a table, or a table that does not sum.
- A fiscal year used without its end date defined.
- "The region" where it is unclear which region is meant.
- A footnote reference missing author, year, or title.
- A project cited only by loan or TA number, or a company or project given only in short form on first mention.
- Cuts that would remove substance rather than padding.

## Checklist

### 1. Clear writing

- Cut. Almost every ADB document can lose 10% with no loss of meaning. Remove repetition, tangents, and "This paper is organized as follows" paragraphs.
- Active voice with a named actor. "Surveys were carried out in 2023" becomes "The council carried out surveys in 2023". If the actor is unknown, query it.
- Third person in Board documents. "We project" becomes "ADB projects"; "our guidelines" becomes "ADB guidelines".
- No clichés: level playing field, on the ground, hit the ground running, silver bullet, going forward.
- No jargon or ADB slang: piggybacked TA (attached TA), knowledge products (say what they are), South–South (among developing members).
- Drop filler nouns: "at the city level" becomes "in cities"; "during the implementation stage" becomes "during implementation"; "transport sector workers" becomes "transport workers"; "private sector companies" becomes "private companies".
- Replace wordy phrases and redundancies (in order to, due to the fact that, a total of, existing, each and every, whether or not). Full lists in `references/word-lists.md`.
- Vary overused verbs: address, develop, enhance, facilitate, identify, improve, appropriate, capacity development. Use the precise word.
- Short paragraphs.
- Web: half the words, meaningful headings, bulleted lists, one idea per paragraph, conclusion first. Social media: short and plain, abbreviations need not be spelled out, member-name rules still apply.

### 2. ADB, members, and places

- "ADB" or "the bank". Never "the ADB" or "the Bank".
- "ADB members", not "ADB member countries". Use "member" or "economy", not "country" or "nation", for members that are not independent political entities (Hong Kong, China; Taipei,China).
- Use the short names in `references/members-and-currencies.md`. The ones most often wrong: the People's Republic of China or the PRC (not China); the Republic of Korea or the ROK (not South Korea or Korea); the Lao People's Democratic Republic or the Lao PDR (not Laos); Viet Nam (two words); Hong Kong, China; Taipei,China (no space after the comma); the Kyrgyz Republic; the Federated States of Micronesia or the FSM; Brunei Darussalam; Türkiye; Timor-Leste; Naoero.
- Never use member codes (CAM, LAO, VIE) in text, tables, figures, or boxes, except inside a loan or TA number.
- List members alphabetically unless there is a reason the reader can see ("in that order"). The PRC sorts under C, the Republic of Korea under K, the Federated States of Micronesia under M.
- Plural member names take a singular verb: the Philippines is, Solomon Islands is, the Netherlands is.
- "Asia and the Pacific", never "the Asia-Pacific". "Pacific developing member countries" or "Pacific DMCs", never "PDMCs". "Pacific island countries" when non-members are included.
- "The former Soviet Union" only for the area after December 1991; "the Soviet Union" for earlier events. Non-members bordering members: Democratic People's Republic of Korea; Russian Federation or Russia. "Euro area".
- Lowercase "region" and "subregion" unless part of a formal name (Greater Mekong Subregion).
- Do not use "West", "South", or "Third World" for stages of development; say industrialized or developing countries.
- Give the country for an agency whose name does not show it: Germany's KfW Development Bank.

### 3. Abbreviations

- Introduce one only if the term has at least three words and appears at least three times in that part of the document. Exception: abbreviations better known than the full form (UNICEF) may be given even once.
- Spelled-out form first, abbreviation in parentheses, abbreviation only from then on. Do this afresh in the front matter, the main text, each appendix, each table, figure, and box, and each chapter of a book. Consider spelling out again after five pages without use.
- No two-letter abbreviations (RM, RP, AP); use a short form such as "the resident mission", "the plan". Allowed: AI, AO, EU, FY, OP, TA, UK, UN, US, and units.
- Do not abbreviate national governments (no "GOB"), resident missions, project or program names (no "RUIDP"; say "the Rajasthan project"), or "Five-Year Plan" (then "the plan").
- Never spell out or list: AIDS, ATM, C, CCTV, COVID-19, e.g., et al., F, FAQ, HIV, HTML, i.e., ISBN, IT, LED, no., p., para., PDF, PIN, SMS, URL, USB. Organizations known by their abbreviation need no expansion: Danida, HSBC, KfW, WWF.
- All capitals, no periods: MOF, MOU, SOE, PhD, US, IMF, Washington, DC. Keep an organization's own casing (AfDB, Sida, Norad) and the institutional ones (DEfR, MfDR, VaR). Periods only in a.m., p.m., e.g., i.e., p., para., no.
- Plural with lowercase s and no apostrophe: DMCs, PPPs. The abbreviations list gives the singular, except SMEs, MSMEs, IRRs.
- Avoid possessives at first mention: "the goal of the Asian Development Bank (ADB)", not "the Asian Development Bank's (ADB's) goal".
- Not in headings or in titles of documents, tables, figures, and boxes, even if already defined, and never add "(ABC)" there. Exceptions: ADB and ADF. Run-in heads may use an abbreviation already introduced.
- Articles: initialisms usually take "the" (the IMF, the EU, the OECD, the SDGs, the UN); acronyms do not (ASEAN, CAREC, UNICEF, JICA). No article: ADB, IBRD, IFC, UNDP, USAID, WHO. "An FAO publication".
- "TA" is uncountable: "the TA", "a TA project", "four TA projects"; never "a TA" or "TAs".
- Non-English names: English translation first, then the abbreviation based on the original name: Ministry of National Development Planning/National Development Planning Agency (Bappenas).
- Ampersands only in established abbreviations: E&S, M&A, M&E, O&M, R&D, S&P. Never in tables or figures otherwise.
- Footnotes: use an abbreviation already introduced in the text. One introduced in a footnote must be spelled out again when it first appears in the text.
- Common abbreviations and their exact expansions: `references/abbreviations.md`.

### 4. Capitalization

ADB uses a down style: capitalize sparingly.

- Capitalize full formal names; lowercase the short form and generic references. Government of the Philippines, then "the government". Ministry of Finance, then "the ministry". Madhya Pradesh State Roads Sector Project, then "the project". Immigration Act, then "the act". Never add "(the Government)" or "(the Project)".
- Capitalize the ADB Board of Governors, Board of Directors, Management, Staff (the whole body; "staff positions" and "ADB staff acting as resource persons" stay lowercase), the names of ADB departments, offices, and resident missions, and "Board document". Lowercase headquarters.
- Titles: capitalize when directly before a name (Vice-President Moorthi), and always for heads of state and government and the ADB President. Lowercase the rest (the director general, the minister for trade). No honorifics: D. Erdenebileg, not Mr. D. Erdenebileg.
- Lowercase: component 1, output 2, tranche 3, subprogram 1, phase 2, subproject 3, category A, group B, tier 1, executing agency, implementing agency, borrower, fact-finding mission, loan agreement, country partnership strategy (unless in a document title), technical assistance, ordinary capital resources, special drawing rights, multitranche financing facility, working groups, steering committees, pending bills.
- Capitalize: Strategy 2030, Sustainable Development Goals, Paris Agreement, Asian Development Fund, Technical Assistance Special Fund, Special Funds resources, Accountability Mechanism, Indigenous Peoples, One ADB, Congress, Parliament, Senate, House of Representatives, named constitutions, ethnic groups, political parties, religions.
- Geography: capitalize the generic term only when it is part of the name (Mekong River, Sichuan Province, Central Java Province). Lowercase when descriptive or plural: the city of Phnom Penh, northeast India, the Cagayan and Pampanga rivers.
- Parts of a document: capitalize Table 2, Figure 3, Appendix 1, Annex 6, Box 2, Map 4, Chapter 3. Lowercase para. 15, section III, footnote 34.
- Treasury: capital for the department and its securities (US Treasuries, Treasury bills at a government auction); lowercase for general use (ADB's treasury portfolio).
- Diseases lowercase unless they contain a proper noun; spell them out (tuberculosis, not TB; avian influenza, not bird flu). Say HIV or AIDS, whichever is meant, not "HIV/AIDS" by reflex.
- Headings and titles in title case. In hyphenated compounds capitalize both elements unless the second is an article or coordinating conjunction; capitalize prepositions of five letters or more (Through, Toward, Across).
- Publication titles in title case and italics. ADB ratings and classifications in italics: rated *less than successful*, categorized *effective gender mainstreaming*.
- Longer term list: `references/word-lists.md`.

### 5. Spelling, hyphens, and word forms

- American spelling (program, labor, center, organization, analyze).
- Close most prefixed words: cofinance, interagency, macroeconomic, midterm, multitranche, nongovernment, online, prequalification, semiannual, socioeconomic, subproject, subregion. Hyphenate before a capital or numeral (non-European, pre-1950), with self- and e- (e-procurement; but email), and to prevent misreading (non-oil, pro-poor, re-lent, multi-industry).
- Hyphenate a phrasal adjective before a noun only if it could be misread: community-based organization, income-generating activities, second-largest city. No hyphen when clear: private sector financing, capacity development plans, climate change policies. None after an -ly adverb (newly built facility) or after the noun (the program is well designed), except cost-effective, risk-averse, short-lived, time-sensitive.
- Suspended hyphens: short- and medium-term, 5- and 10-year plans.
- Rewrite ugly compounds: "countries that have a high prevalence of tuberculosis", "households headed by women".
- Nouns used as adjectives are singular: safeguard framework, stakeholder groups. Exceptions: human resources, skills training, results framework, needs assessment.
- "Sector" and "multisector" as adjectives, never sectoral or multisectoral. Agriculture sector, education sector, finance sector, industry sector (not agricultural, educational, financial, industrial sector).
- "Anticorruption" is an adjective: anticorruption initiatives.
- Computer terms: email, internet, intranet, web, computer (not PC), Excel spreadsheet.
- Plurals: formulas, forums, symposia, foci, minimums, appendixes.
- Non-English terms: avoid if English will do. Otherwise italics, with a translation in parentheses or a footnote at first use in each part. Three or more: add a glossary. No italics for proper nouns or for words in Merriam-Webster (ad hoc, per capita). Replace Latin: inter alia (among other things), vis-à-vis (in relation to), ex ante (in advance), ex post (after), de facto (actual), ceteris paribus (other things being equal). Never ibid. or op. cit.
- Gender-neutral and unbiased language: chair, fishers, staffing or workforce, person-months, artificial, humanity; "their" for "his/her". List in `references/word-lists.md`.
- No trademark symbols.
- Problem pairs (affect/effect, ensure/insure, comprise/compose, relend/onlend, sewage/sewerage, that/which): `references/word-lists.md`.

### 6. Numbers

- Spell out one to nine; numerals for 10 and above. Always numerals for currencies, percentages, decimals, ratios, units of time (2 years, 9 person-months), units of measurement, earnings multiples, parts of a book, parts of a whole (component 1), figures and tables, and every number in a series where at least one item takes a numeral ("27 villages, 11 towns, and 4 cities").
- Do not start a sentence with a numeral or a percentage; recast it ("The project covered 27 villages").
- Ordinals: first to ninth spelled out; 10th and above in numerals with no superscript; 20th century.
- "%" in text and tables. Differences between percentages are in percentage points or basis points.
- Commas in numbers above 999, except years, page numbers, and serial numbers.
- Decimals with a period and a leading zero (0.6); two places at most; same number of places for numbers being compared (2.3, 3.0, and 5.2). Round 5 and above up.
- Spell out and hyphenate simple fractions: two-thirds majority, three-quarters of the people.
- Negative numbers: en dash in text (–6.9%); parentheses in tables, defined below the table as "( ) = negative."
- "5 million", "$2.5 billion"; never m, mn, b, or bn in text. Billion is a thousand million. No lakh or crore: ₹500,000, ₹50 million.
- Fewer for countable things, less for amounts, time, and money.
- "The number of loans has"; "a number of studies have". Percentages take the number of their noun: 20% of the population lives; 80% of the children have. Only exactly 1 is singular: 1 person-month, 0.7 person-months.

### 7. Currencies

- Symbol before the number, no space: $390 million, Tk100,000, ¥5 million, SDR36,000, ₱698.3 billion. Use ADB symbols from `references/members-and-currencies.md`, not ISO codes (not USD390 million), except in bond-market documents that use ISO codes throughout.
- "$" means US dollars once a note at the front says so; other dollars carry their prefix (A$, NZ$, S$).
- Currency names lowercase and spelled out when no amount follows: the rupiah, the taka, special drawing rights.
- Small amounts as a decimal of the main unit: $0.40, not 40 cents.
- If the document gives an exchange rate at the front, do not add dollar equivalents in the text. Historical conversions go in parentheses or a footnote with the date of the rate.
- Exchange rates: "the US dollar–won exchange rate" (en dash); "€1.00 = $1.05".
- An amount takes a singular verb: "The NRs10 million was used".
- "SDR" as a symbol is not spelled out at first use but goes in the abbreviations list.

### 8. Dates and time

- 26 January 2022. No comma, no ordinal, no leading zero. Months spelled out in text; Jan, Feb, Mar (no period) only where space is tight.
- Ranges with an en dash: 12–28 February 2024; 4 June–10 August 2021.
- Give the actual date or period, not a relative one: "in 2023", "since 2022".
- "The start of 2024", "the end of 2024"; not "start 2024", "end-2024".
- FY2024, no space; define the fiscal year in a note at the front or at first mention: "fiscal year (FY) 2022 (ended 30 June 2022)". SY2023/24 for school years. Use 2023/24 only when nothing clearer exists, and define it.
- 2023–2024 is two full calendar years. 2000–2010 is 11 years.
- Decades: the 1990s; not the nineties, '90s, or 1990's. For the first two decades of a century give the years: 2000–2004, not "the early 2000s".
- Quarters: spell out, or with three or more references use Q1, Q2: "the first quarter (Q1) of 2023 ... Q2 2023".
- Time: 9 a.m., 6:30 p.m., noon, midnight. No 24-hour clock, no leading zero.

### 9. Ranges, rates, and ratios

- En dash, no spaces, for inclusive ranges: paras. 3–7, 48–50 kilometers, pp. 11–35.
- Repeat a symbol that is closed up to the number: 12%–14%, $125,000–$150,000, $8 million–$9 million. A spaced unit goes once, after the second number: 15–20 kWh.
- Never mix words and dash: "from 17 to 18 October" or "17–18 October"; "24–36 months", not "between 24–36 months".
- Avoid "between ... and" where precision matters: "from 2000 to 2016" or "during 2000–2016".
- "From ... to" only for a real continuum. "Sectors as varied as agriculture and tourism", not "ranging from agriculture to tourism".
- Year ranges in strategy and plan titles: "country partnership strategy (CPS), 2023–2026 for Viet Nam"; "the Pacific Approach, 2021–2025 incorporates" (comma before the years, none after).
- Ratios with a colon, no spaces: 78:22. En dash in compound terms: debt–equity ratio, cost–benefit analysis, public–private partnership, ADB–OECD study.
- Rates: a slash may stand for "per" (m3/day, km/h); be consistent.
- Maternal mortality ratio; infant mortality rate.
- Rates rise and fall; growth and inflation accelerate and decelerate. "The inflation rate fell to 2.5%" or "inflation decelerated to 2.5%".
- Credit ratings as the agency writes them: AAA, not triple-A; "the bonds, rated BBB–, were priced". Full agency name first: Fitch Ratings, Moody's Ratings, S&P Global Ratings.

### 10. Punctuation

- Serial (Oxford) comma. Semicolons between items when any item contains a comma.
- Em dash with no spaces for a break or emphasis. En dash for ranges, relationships between equals, and negative numbers. Hyphen for compounds only.
- Double quotation marks; single for a quotation inside a quotation. Periods and commas inside the closing mark; colons, semicolons, and em dashes outside; question marks inside only if part of the quotation.
- Before a quotation: comma after an incomplete lead-in (The President said, "..."), colon after a complete sentence, nothing after "that".
- Quotation marks for a word referred to as a word, and at first use of a word in an unusual sense, with a definition.
- Long quotations: indented block, no quotation marks, no italics. Every quotation needs a footnoted source with a page number.
- No slashes between words: write "and", "or", or "and/or". Allowed: and/or, HIV/AIDS, rates, PRe/PRs-style currency forms, table column heads, copublishers, organization names.
- Avoid nested parentheses; recast with commas or em dashes, or use square brackets inside.
- e.g., and i.e., always with periods and a following comma, and not confused with each other.
- No comma after a title that contains one unless the sentence needs it: "The Companies Act, 1956 was amended in 2008."
- One space after a sentence.
- Apostrophes never make plurals. Joint possession: "SEC and SPD's memo"; separate: "ADB's and the World Bank's frameworks".
- Reported speech moves one tense back: will to would, can to could, may to might, must to had to.

### 11. Lists

- Parallel wording and grammar in every item.
- Colon before a list only if the lead-in is a complete sentence. No punctuation if the lead-in runs into the list ("The program will produce (i) ..., (ii) ..., and (iii) ...").
- Number run-in items with (i), (ii), (iii) only when they are long or need emphasis. Short lists take no numbers. Second level: (a), (b), (c).
- Vertical lists of fragments: lowercase first word, commas or semicolons, "and" or "or" after the penultimate item, period at the end. Vertical lists of full sentences: capital, period, no "and".
- Do not mix sentences and fragments. No bullets in the text of Board documents.
- If one item has a bold run-in head, all do.
- Remove "respectively", "the former ... the latter", and "namely"; restate the pairs: "GDP grew 8% in 2018, 14% in 2019".

### 12. Cross-references and footnotes

- No "see", "above", or "below": "(Annex 3)", "(Table)", "(Appendix 1, Table A1.1)". Prefer paragraph numbers to sections: "paras. 66–74". Place at the end of the sentence.
- Footnote numbers are superscript Arabic numerals after the punctuation at the end of the sentence. Not in headings. No double footnotes: merge them or move one.
- Do not repeat a footnote; write "(footnote 8)". If a page number is needed, use a new footnote: "Footnote 8, pp. 19–25."
- No footnotes, tables, or figures in an executive summary. It should run 1–2 pages, never more than 10% of the document, with no new terms and no pasted text.
- Reference format: `Author. Year. Title in Italics. Publisher. page.` Full models for ADB documents, books, journals, and online sources in `references/citations.md`. A bare URL is not a reference. Access dates only for databases. No Wikipedia. No bibliography in Board documents.
- Cite a project by its full title at first mention with a footnote to the project page; never by loan or TA number in the text. "Second" before a follow-on project name, not "II" after it, and never "First" for the original.

### 13. Tables, figures, boxes, headings, appendixes, units

Read `references/tables-and-layout.md` before editing any of these. The points that are wrong most often:

- Every table, figure, and box is mentioned in the text and placed after the paragraph that first mentions it. One item only: title with no number.
- Title: "Table 3: Financial Performance, FY2022" in title case, abbreviations spelled out (except ADB, ADF), years last after a comma. Unit on the next line in parentheses, lowercase, singular, without "in": ($ million), ($'000), (%).
- Below the table or figure, in this order: abbreviations (alphabetical, "ADB = Asian Development Bank, GDP = gross domestic product."), Note(s), lettered footnotes (superscript a, b, c), Source(s). Each must be self-contained, with a documentary source rather than just an organization's name.
- In table cells: "..." for data not available, 0 for zero, blank where not applicable, negatives in parentheses. Same decimal places down a column. Add "Note: Numbers may not sum precisely because of rounding." where it applies.
- Headings: at most four levels (I., A., 1., a.), never a single subheading at any level, no abbreviations, no footnotes.
- Metric units. Spell out a unit at first use with its abbreviation, then abbreviate: "15 kilometers (km) ... 32 km". Abbreviated units have no plural, no period, and no hyphen (22 kg, 5,960 ha, 11 kV line); spelled-out units are hyphenated as adjectives (11-kilovolt line).
- "Appendix" for material that depends on the main text; "annex" for a stand-alone document. Appendixes restart abbreviations and footnote numbering.

## Output format

Unless the user asks for something else:

```
## Revised text
<the full corrected text>

## Changes
- Abbreviations: <what changed, with one example>
- Member names: ...
- Numbers and dates: ...
(only the groups that had changes)

## Queries for the author
1. <location>: <what is missing or ambiguous, and what is needed>
```

For a review-only request, replace "Revised text" with a findings table: location, original, rule, proposed fix.

## Reference files

- `references/word-lists.md`: wordy phrases, redundancies, clichés, overused words, gender-neutral terms, Latin, capitalization and spelling term lists, problem word pairs.
- `references/members-and-currencies.md`: all 69 member names, text and table forms, government names, currency names, symbols, ISO codes.
- `references/abbreviations.md`: common ADB abbreviations with exact expansions, article usage, units of measurement.
- `references/citations.md`: footnote reference models for every source type.
- `references/tables-and-layout.md`: tables, figures, boxes, headings, appendixes, glossary, page numbers, photo captions.
- `scripts/adb_lint.py`: regex linter for mechanical checks.
