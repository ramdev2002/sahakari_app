# Sahakari App — Test Credentials

Credentials for every identity (role) seeded into the database by the
`seed_demo` management command. Share this sheet with the QA/testing team.

## How to load the test data

From the backend project root:

```bash
python manage.py seed_demo
```

- Creates all role groups, the chart of accounts, seed capital (1,000,000),
  savings & loan products, **one login per role** (table below), and a demo
  member with a savings account and a requested loan.
- The command is **idempotent** — safe to re-run; it refreshes the demo
  passwords and re-links records.
- Use `python manage.py seed_demo --no-demo` to seed only roles and reference
  data (no users, no demo member).

## Environment

| Item       | Value                          |
|------------|--------------------------------|
| API base   | `http://localhost:8000/api/`   |
| WEB UI     | `http://localhost:3000`        |
| API docs   | `http://localhost:8000/api/docs/` |
| Login      | `POST /api/auth/token/` `{email, password}` |

> Passwords are seeded fresh on every run of `seed_demo`, so these credentials
> are always valid after (re)seeding.

## Credentials (one per identity type)

| # | Role                  | Email                     | Password    |
|---|-----------------------|---------------------------|-------------|
| 1 | System Administrator  | `demo@jharlang.local`     | `Demo@12345` |
| 2 | Administrative Officer| `admin.officer@jharlang.local` | `Demo@12345` |
| 3 | Branch Manager        | `branch.manager@jharlang.local` | `Demo@12345` |
| 4 | Account Officer       | `account.officer@jharlang.local` | `Demo@12345` |
| 5 | Loan Officer          | `loan.officer@jharlang.local`    | `Demo@12345` |
| 6 | Cashier               | `cashier@jharlang.local`         | `Demo@12345` |
| 7 | Auditor               | `auditor@jharlang.local`         | `Demo@12345` |
| 8 | Member                | `member@jharlang.local`          | `Demo@12345` |

## What each role can do

| Role                   | Can view members / savings / loans / transactions | Can create / update members | Open savings | Loans (create/approve/disburse/repay/cancel) | Deposit / Withdraw | Transfer | Users (list/manage) | Reports | Audit logs | Approvals | Products / Accounts / Org |
|------------------------|:-------------:|:-------------:|:-----:|:------------------------------:|:---------:|:--------:|:---------:|:-------:|:----------:|:---------:|:--:|
| System Administrator   | Yes           | Yes           | Yes   | Yes                            | Yes       | Yes      | Yes       | Yes     | Yes        | Yes       | Yes |
| Administrative Officer | Yes           | Yes           | Yes   | Yes                            | Yes       | Yes      | Yes       | Yes     | Yes        | Yes       | Yes |
| Branch Manager         | Yes           | Yes           | Yes   | Yes                            | Yes       | Yes      | Yes (list) | Yes     | Yes        | Yes (decide) | —  |
| Account Officer        | Yes           | Yes           | Yes   | — (no approve)                 | Yes       | Yes      | Yes (list) | Yes     | —          | —         | —  |
| Loan Officer           | Yes (view)    | —             | —     | Yes                            | —         | —        | Yes (list) | —       | —          | Yes (view) | —  |
| Cashier                | Yes (view)    | —             | —     | —                              | Yes       | —        | —          | —       | —          | —         | —  |
| Auditor                | Yes (view)    | —             | —     | —                              | —         | —        | Yes (list) | Yes     | Yes        | Yes (view) | —  |
| Member                 | **own records only** | —      | —     | —                              | —         | —        | —          | —       | —          | —         | —  |

Legend: `—` = no access (request returns `403 Forbidden`).

## What each role sees in the frontend

The web UI (`http://localhost:3000`) is role-aware. The sidebar menu and the
action buttons are filtered to the logged-in user's capabilities, so a role
never sees a page or action the backend would reject.

### Sidebar pages visible by role

| Page               | Sys Admin / Admin Officer | Branch Manager | Loan Officer | Account Officer | Cashier | Auditor | Member |
|--------------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Dashboard          | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   |
| Members            | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   | ✔ (own only) |
| Savings            | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   | ✔ (own only) |
| Loans              | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   | ✔ (own only) |
| EMI Calculator     | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   |
| Repayments         | ✔   | ✔   | ✔   | —   | —   | —   | —   |
| Transactions       | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   | —   |
| Approvals          | ✔   | ✔   | ✔   | —   | —   | ✔   | —   |
| Reports            | ✔   | ✔   | —   | ✔   | —   | ✔   | —   |
| User Management    | ✔   | ✔   | ✔   | ✔   | —   | ✔   | —   |
| Settings           | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   |
| Profile            | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   | ✔   |

> A Member whose record is not linked yet sees empty lists; once linked (as the
> seeded Demo Member is), the lists show only their own records.

### Action buttons visible by role

"Members" page actions:

| Action     | Sys Admin / Admin Officer | Branch Manager | Account Officer | Others |
|------------|:---:|:---:|:---:|:---:|
| New Member | ✔   | ✔   | ✔   | — |
| Edit       | ✔   | ✔   | ✔   | — |
| Delete     | ✔   | ✔   | ✔   | — |

"Savings" page actions:

| Action       | Sys Admin / Admin Officer | Branch Manager | Account Officer | Cashier | Others |
|--------------|:---:|:---:|:---:|:---:|:---:|
| Open Account | ✔   | ✔   | ✔   | —   | — |
| Deposit      | ✔   | ✔   | ✔   | ✔   | — |
| Withdraw     | ✔   | ✔   | ✔   | ✔   | — |

"Loans" page actions:

| Action   | Sys Admin / Admin Officer | Branch Manager | Loan Officer | Others |
|----------|:---:|:---:|:---:|:---:|
| New Loan | ✔   | ✔   | ✔   | — |
| Approve  | ✔   | ✔   | ✔   | — |
| Disburse | ✔   | ✔   | ✔   | — |
| Cancel   | ✔   | ✔   | ✔   | — |
| Repay    | ✔   | ✔   | ✔   | — |

(Repayments page — "New Repayment"/"Repay" — shows only for the same roles
that can repay loans: Sys Admin, Admin Officer, Branch Manager, Loan Officer.)

"Transactions" page actions:

| Action         | Sys Admin / Admin Officer | Branch Manager | Account Officer | Auditor / Loan Officer | Cashier |
|----------------|:---:|:---:|:---:|:---:|:---:|
| New Transaction| ✔   | ✔   | ✔   | —   | ✔   |
| Reverse        | ✔   | ✔   | —   | —   | —   |

"Approvals" page actions:

| Action  | Sys Admin / Admin Officer | Branch Manager | Loan Officer / Auditor |
|---------|:---:|:---:|:---:|
| Approve | ✔   | ✔   | — (view only) |
| Reject  | ✔   | ✔   | — (view only) |

"User Management" page actions:

| Action   | Sys Admin / Admin Officer | Branch Manager / Account Officer / Loan Officer / Auditor |
|----------|:---:|:---:|
| New User | ✔   | — |
| Edit     | ✔   | — |
| Delete   | ✔   | — |

> The Dashboard adapts to the role: it only loads sections the role can
> access. For example, a Cashier sees the stat cards and notifications but no
> Recent Transactions list, and a Member sees only their own totals.

## Notes for the testing team

- The **Member** login only ever sees its own linked member record, savings
  account and loans (linked to the seeded `Demo Member`).
- The **System Administrator** login is a superuser; **Administrative
  Officer** carries the same full administrative powers via its role group.
- Loan workflows: a loan must be **requested → approved → disbursed** before
  repayments are allowed. Approvals of approval requests can be decided by
  Branch Manager and higher roles.
- After seeding, money basics: seed capital 1,000,000; the demo member opened
  savings with 1,000 and a requested GENERAL loan of 50,000.