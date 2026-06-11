# Module: <MODULE NAME>

- Source files used:
  - <relative/path/to/file.pdf> (size: <bytes>, last-modified: <ISO timestamp>)
- Extraction status:
  - status: draft | in-progress | verified | needs-supply | unreadable
  - extraction_date: YYYY-MM-DD
  - extractor: <tool or person>

## Module summary
A concise 3–6 sentence faithful summary of the module's core focus. Use direct quotes for wording that must be preserved.

## Chapter-by-chapter notes
- Chapter 1: <Chapter Title>
  - Source location: <file.pdf> (page X)
  - Key points:
    - Bullet 1 (verbatim or faithful short paraphrase)
    - Bullet 2
  - Direct quotes (verbatim, short):
    > "..."

- Chapter 2: <Chapter Title>
  - Source location: ...
  - Key points:
    - ...

## Key principles
- Principle 1: <verbatim or faithful paraphrase>. [Source: file.pdf (page X)]
- Principle 2: <...> [Source: ...]

## Deterministic rules candidates
- Rule 1: <If X then Y / threshold form> — exact wording where present. [Source: file.pdf (page X)]
- Rule 2: <Threshold rules e.g., ROE > 12%> — [Source: ...]

## Risk principles
- Risk principle A: <text> — [Source: ...]
- Risk principle B: <text> — [Source: ...]

## Psychology principles
- Behavioral guidance: <quote or short faithful paraphrase> — mark as `explanation-only` if subjective. [Source: ...]

## Formulas and measurable logic
- Formula 1: <math expression exactly as in source>
  - Variables: define variable names and units
  - Usage notes: when to apply
  - Source: <file.pdf> (page X)
- Formula 2: ...

## Items suitable for automation
- Candidate 1: <deterministic rule> — required inputs: [data fields]; output: [flag/metric]; source: [file.pdf (page X)]
- Candidate 2: ...

## Items not suitable for automation
- Item 1: <subjective / qualitative> — reason: <why it's not automatable> — mark as `explanation-only`.
- Item 2: ...

## Engine mapping candidates
- Universe engine:
  - Candidate: <liquidity threshold, universe filters> — Source: ... — Status: direct for v1 / optional later / not suitable
- Fundamental engine:
  - Candidate: <ROE, margin thresholds> — Source: ... — Status: ...
- Technical engine:
  - Candidate: <candle classification, volume confirmation> — Source: ... — Status: ...
- Event engine:
  - Candidate: <management-change flag> — Source: ... — Status: ...
- Risk engine:
  - Candidate: <position-size formula, drawdown halt> — Source: ... — Status: ...
- Decision engine:
  - Candidate: <entry/exit thresholds> — Source: ... — Status: ...
- Explanation engine:
  - Candidate: <audit fields, reason templates> — Source: ... — Status: ...

## V1 inclusion candidates
- Item: <deterministic, measurable, low-data-requirement features> — source: ...

## V1 exclusion candidates
- Item: <high-data or subjective features excluded from v1> — reason & source

## Open questions
- Q1: <e.g., missing page / ambiguous threshold / missing module 12> — Action: request re-supply or clarify.
- Q2: <...>
