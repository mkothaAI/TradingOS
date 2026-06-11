# AI Responsibilities and Boundaries

## Allowed AI Responsibilities
- **Summarize article text**: Provide concise summaries of news articles or textual data.
- **Classify event type**: Identify and categorize the type of event described in the text (e.g., merger, earnings report, regulatory change).
- **Extract affected company and date**: Identify the company involved and the date associated with the event from the text.
- **Support explanatory follow-up**: Rephrase deterministic verdicts, evidence, and rule traces without introducing new policy or authority.

## Forbidden AI Responsibilities
- **Inventing prices**: Do not generate or suggest stock prices, as this could lead to misleading information.
- **Inventing indicators**: Avoid creating or recommending technical indicators or financial metrics without proper data support.
- **Policy by prose**: AI must not turn a narrative recommendation, explanation, or follow-up answer into policy, an override, or a decision rule.
- **Override authority**: AI must not override the symbolic/verdict layer, deterministic rules, or backend-authored policy state.
- **Final verdict**: AI must not make or replace the final symbolic verdict; only the deterministic system may do so.
- **UI inference**: AI must not infer trading logic, eligibility, or risk conclusions from browser/UI presentation alone.
- **Labeling discipline**: AI and the UI must explicitly distinguish real-time, delayed, stale, and snapshot data when describing evidence or market state.