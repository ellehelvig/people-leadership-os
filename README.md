# People Leadership OS

A working example of how a Chief of Staff could run the Office of the Chief People Officer (CPO) on GitHub. Issues are the intake, a project board is the priority view, decision records are the memory, and Copilot drafts the weekly brief from the open issues for a person to review.

Harbor and Meridian Group are fictional. Harbor is a 4,000-person developer-tools subsidiary of Meridian Group. Every person, issue, date, and number here is invented.

**Start here:** read the [weekly brief](briefs/2026-w46-cpo-brief.md), then open any issue it cites to check the claim against its source.

## How the weekly loop works

```mermaid
flowchart LR
    A["Issues: decision requests and signals"] --> B["Project board: priority view"]
    B --> C["People Leadership Team: review and decide"]
    C --> D["Decision records: rationale and owner"]
    A --> E["Copilot drafts the weekly brief"]
    D --> E
    E --> F["Chief of Staff reviews and edits"]
    F --> B
```

1. Anyone on the People Leadership Team opens an issue with one of two forms: a [decision request](.github/ISSUE_TEMPLATE/decision-request.yml) or a [signal](.github/ISSUE_TEMPLATE/signal.yml).
2. Open issues land on the [project board](https://github.com/users/ellehelvig/projects/2).
3. Each week, Copilot drafts the brief from the open issues using the rules in [copilot-instructions.md](.github/copilot-instructions.md). Every claim cites its source issue, and issues with no owner are flagged.
4. The Chief of Staff edits the draft before it goes to the CPO.
5. Decisions that are material or hard to reverse get a decision record.

## What is in here

| Path | What it is |
|---|---|
| [Issues](../../issues) | Twelve open issues: five decision requests and seven signals |
| [briefs/2026-w46-cpo-brief.md](briefs/2026-w46-cpo-brief.md) | The weekly brief: Copilot's draft from those issues, edited down to one page |
| [docs/operating-rhythm.md](docs/operating-rhythm.md) | Weekly, monthly, and quarterly cadence, with who decides what |
| [docs/align-or-diverge.md](docs/align-or-diverge.md) | Five tests for when a subsidiary adopts the parent company's People programs |
| [decisions/0001-ai-enabled-people-operating-model.md](decisions/0001-ai-enabled-people-operating-model.md) | A sample decision record |

## What this does not do

- It does not make decisions or replace the CPO's judgment.
- It does not authorize putting employee data into an AI tool.
- It does not describe any real company's process.

## How this was built

- **GitHub Copilot** drafted the first version of each document and both issue forms, and wrote the weekly brief from the open issues in this repository.
- **Claude** helped shape the concept, ran checks on the files, created the issues and board from Copilot's sample data, and drafted the edits to the brief, the align-or-diverge framework, and the decision record.
- **Elle Helvig** chose the problem, directed the work, supplied the reference reading behind the framework, and approves what is published here.

## Author

[Elle Helvig](https://github.com/ellehelvig)

Licensed under the [MIT License](LICENSE).
