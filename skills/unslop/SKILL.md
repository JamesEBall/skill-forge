---
name: unslop
description: Rewrite text so it stops reading like AI output. Applies a "Naughty List" of rules distilled from Wikipedia's "Signs of AI writing" field guide (puffery, -ing tails, "not just X but Y", rule of three, AI vocabulary, chatbot chatter, hedging disclaimers, markdown tics). Use when asked to un-slop, de-slop, humanize, or "make this sound less like AI", and as a self-check before delivering prose the user will publish or send under their own name (emails, reports, posts, docs, READMEs, commit and PR text).
---

# Unslop

Source: Wikipedia, "Wikipedia:Signs of AI writing" (WikiProject AI Cleanup), read November 2026. That page is a field guide for spotting AI text. This skill turns it around and uses it as an editing checklist.

## The one idea behind every rule

Language models drift toward the statistically average sentence. Specific, odd, checkable facts get replaced by generic, positive, important-sounding ones. The subject ends up louder and blurrier at once: "invented the first train coupling" becomes "a revolutionary titan of industry".

So the fix is almost never a word swap. The fix is to put the specific fact back, or delete the sentence if there was no fact under it. The Wikipedia page warns about this directly: scrubbing the surface signs without fixing the emptiness underneath only hides the problem.

## Procedure

1. Read the whole text. Write down, in one line, what it is supposed to tell the reader. If you can't, the problem is the content, and you should say so before polishing.
2. Pass 1, content (rules C1 to C9). For each flagged sentence ask: what is the concrete claim? Keep the claim, drop the wrapper. If no claim survives, cut the sentence.
3. Pass 2, sentences (rules L1 to L8).
4. Pass 3, formatting and chatter (rules F1 to F7, M1 to M5).
5. Check for overcorrection (section "Do not overcorrect").
6. Re-read against the original. Every fact, number, name, and caveat that mattered must still be there. Do not add facts you can't support. If a sentence needs a specific you don't have, ask for it or leave a visible question for the author; never invent one.
7. Return the rewritten text. Add a change note only if the user asked for one or you cut something they may want back, and keep it to what changed in substance.

When editing someone else's writing, keep their voice, dialect, and deliberate choices. Fix slop, not style.

## The Naughty List

### Content

**C1. No significance inflation.** Don't say a thing is important, pivotal, a turning point, a testament, part of a broader movement, or that it left a mark. State what happened and let the reader judge.
Watch: stands as, serves as a reminder, a testament to, pivotal/crucial/key role or moment, underscores its importance, reflects broader, enduring/lasting legacy, setting the stage for, marks a shift, evolving landscape, indelible mark, deeply rooted, "this distinction matters because".
Also cut: "has sparked debate", "raises questions about", "prompted broader reflection", and the move where you concede something is minor and then explain its importance anyway.

**C2. No analysis tail.** Don't end a sentence with a comma and an -ing phrase that interprets the fact you just gave.
Bad: "The station has six platforms, reflecting its continued relevance to regional transport."
Good: "The station has six platforms."
Watch: highlighting, underscoring, emphasizing, reflecting, symbolizing, showcasing, ensuring, fostering, contributing to, demonstrating, illustrating, "valuable insights", "resonates with", "aligns with".

**C3. Say the relationship.** "Was associated with", "in connection with", "connected to", "linked to" hide what actually happened. Write "was the CEO", "taught violin there", "funded it".

**C4. Name who said it.** No "experts argue", "observers note", "industry reports suggest", "critics say", "is widely regarded", "described in scholarship as". Name the source or drop the claim. Don't turn one source into "several". Don't write "such as" before a list that is in fact complete.

**C5. Don't narrate the sources.** Give what the source says, not the fact that sources exist. Cut "featured in X, Y, and other outlets", "documented across national and regional media", "independent coverage", "his official profile identifies him as", "records list". Write the fact and cite it.

**C6. No hedging disclaimers.** Cut "while specific details are limited", "not widely documented", "based on available information", "in the provided sources", "maintains a low profile". If you don't know, either say so once, plainly, or say nothing. Never follow a gap with "likely" speculation.
Also cut the corrective framings: "should be treated as X rather than Y", "this does not by itself establish", "not to be confused with", unless the reader was really at risk of that mistake.
Also cut didactic nudges: "it's important to note", "it is worth remembering", "it is crucial to distinguish".

**C7. No challenges-and-future formula.** Don't close with "Despite its [strengths], X faces challenges..." followed by "Despite these challenges, X continues to..." or speculation about future potential. If there is a real problem, state it with its specifics where it belongs.

**C8. No summary endings.** No "In summary", "In conclusion", "Overall", "Ultimately", and no last sentence that restates the paragraph. End on the last piece of information.

**C9. No brochure prose.** Cut nestled, in the heart of, boasts, vibrant, rich (heritage, history, tapestry), breathtaking, renowned, groundbreaking, seamless, diverse array, commitment to, "maintains an active presence on social media".

### Language

**L1. AI vocabulary.** These words are measurably overused by models and tend to arrive in clusters. One is nothing; several in a paragraph is the strongest single tell. For each, find the plain thing you meant.
- Older set: additionally (opening a sentence), align with, boasts, bolstered, crucial, deep dive, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate, key (adjective), landscape (abstract), meticulous, pivotal, robust, showcase, tapestry (abstract), testament, underscore (verb), valuable, vibrant.
- 2026 set: challenge, clearer, dependable, echoed, foster, leverage, matters, multifaceted, practical, prioritize, quietly, steady, universally.
Take this list literally. A synonym of a listed word is not suspect, and swapping "crucial" for "vital" fixes nothing. Literal uses are fine (an underscore character, a physical landscape).

**L2. Use "is" and "has".** Models avoid plain copulas. Prefer "is" to serves as, stands as, functions as, represents, marks, holds the distinction of being, refers to. Prefer "has" to boasts, features, offers. Prefer "was a candidate" to "ventured into politics as a candidate".

**L3. No negative parallelism.** Don't define a thing by a claim nobody made.
- "not just X, but Y" / "not only X but also Y" / "doesn't just X; it Y"
- "it's not X, it's Y" / "not X, but Y" / "no X, no Y, just Z"
- "Y rather than X" / "Rather than X, it Y" (the form current models favor)
State Y. Keep the contrast only when someone actually asserted X.

**L4. No reflexive triples.** Don't reach for three adjectives or three short phrases to sound complete ("clarity, flow, and readability"). List what is actually there: one item, two, or five. Same for "X, Y, and other Z".

**L5. Don't rotate synonyms.** If it's "the artists" the first time, it's "the artists" the next time, not "these creators" and then "the non-conformist painters". Repeating a noun is fine.

**L6. Plain verbs.** wrote, not authored. Used, not utilized. Moved, not relocated. Tried, not attempted. Died, not passed away.

**L7. Punctuation tics.** No em dash with spaces around it used to punch up a clause. Use a comma, colon, parentheses, or a second sentence, whichever fits. But vary: text made only of commas and full stops, with every sentence 8 to 20 words long, is the newest tell.

**L8. Allow the human constructions.** Models underuse these, so they are fine and often better: "there is", "it has", flat superlatives when true ("the first", "the only"), intensifiers and qualifiers ("very", "perhaps", "tends to"), and the occasional wordy phrase ("in order to", "the fact that").

### Formatting

**F1.** Headings in sentence case. No "X and Y" headings by habit ("Awards and recognition", "Challenges and future outlook"). No heading on a short piece that doesn't need one.
**F2.** Bold only what a reader must not miss. No bolded phrases scattered through prose.
**F3.** No inline-header bullets (`- **Label**: one sentence`) where a paragraph or a table would carry the content. No bulleting of connected reasoning.
**F4.** No emoji as bullets or heading decoration.
**F5.** Straight quotes and apostrophes, unless the destination's house style says otherwise.
**F6.** No `---` rules between sections, and no markdown at all in a destination that won't render it (email, plain-text fields, commit messages, wikitext).
**F7.** No leftover scaffolding: `[Your Name]`, `[link here]`, `(add URL)`, `2026-XX-XX`, `example.com/source1`, `PASTE_URL_HERE`, citation debris such as `oaicite` or `utm_source=`, "to be supplied".

### Chatter and meta

**M1. No chat residue in the deliverable.** Certainly!, Of course!, Great question, You're absolutely right, Here is a..., I hope this helps, Let me know if..., Would you like me to..., "be sure to verify before publishing".
**M2. No announcing.** Cut "In this section we will discuss". Say the thing.
**M3. No customer-service voice.** "I have carefully reviewed", "I apologize for any inconvenience", "please point out any specific issues and I will address them", "let's work together". Say what you did or what you think.
**M4. Change summaries say what changed.** For commit messages, PR descriptions, edit notes, and changelogs:
- Name the actual change ("added the 2024 results table"), not virtues ("improved clarity, flow, and neutrality").
- Don't claim compliance with guidelines or standards in general terms. Cite the specific rule or say nothing.
- Don't list what you left alone ("while preserving the original meaning", "retained existing structure").
- Don't stress that additions are sourced, verified, or reliable.
- Don't say you are "addressing reviewer feedback" as a virtue; say what you fixed.
**M5. No model self-reference.** "As an AI", knowledge-cutoff notes, "as of my last update".

## Do not overcorrect

- These are tells of emptiness, and each also appears in good human writing. A real contrast, a list that really has three items, one em dash, the word "key" for a key: leave them. Density and reflex are the problem.
- Don't trade a listed word for its nearest synonym. Rewrite the sentence around the fact.
- Don't strip every dash and semicolon. Flat, uniform punctuation is its own tell.
- Don't add fake humanity: no invented anecdotes, typos, slang, or forced informality.
- These are not signs of AI and need no fixing: correct grammar, formal or academic register, a mix of casual and technical tone, an isolated transition word, plain or "bland" prose.
- Technical precision outranks style. Never loosen a number, a caveat that changes what the reader should do, or a term of art to satisfy a rule here.
- Passing this list does not make text good. It still has to be accurate and say something.

## Quick example

Before:
> Founded in 1989, the institute stands as a pivotal force in regional statistics, marking a significant shift toward data-driven governance. It is not just a data provider, but a trusted partner for policymakers, researchers, and citizens alike — underscoring its enduring commitment to transparency.

After:
> The institute was founded in 1989. It publishes the region's census, labour, and price statistics, and since 2011 has released them as open data.

The second version needed facts the first one never had. If you don't have them, ask.
