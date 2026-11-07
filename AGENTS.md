# AGENTS.md: Parent Line

This file is for AI assistants and for people (hackathon judges included) who want the whole project in one read: what it does, the evidence behind it, how far the idea goes, and how to run it from a fresh clone. [README.md](README.md) has the same run steps in more detail, with the messages you should see and a troubleshooting table.

## In one paragraph

Parent Line is a family safety net for older parents in India, built on [Switch](https://github.com/sandbox-quantum/switch). Switch turns the family's Telegram group into a room shared by the family, two Claude Code agents (the **Guardian** and the **Clerk**) and three small Python services (**Bank watch**, **Ride watch** and **Call watch**). When something goes wrong for the parent, a service posts an alarm in the group. The Guardian splits the response into jobs ("call Mom", "report on 1930", "call the bank") and tracks who took each one. The Clerk does the paperwork against the deadline. The parent needs no new app, and the family uses the Telegram group it already has.

Links: [demo video](https://youtu.be/VWSH7CKUek0) · [website](https://web-jet-three-69.vercel.app/) · [design document](docs/design.md) · [roadmap](docs/roadmap.md)

## What it does, part by part

| Part | Kind | What it does | Code or instructions |
|---|---|---|---|
| Bank watch | Python service (no AI) | Reads the parent's bank SMS. Raises an alarm on scam patterns: a large debit, a new payee, an FD broken early, a loan, several debits close together, a debit late at night. The rules are plain, tested code, so alarms are predictable. It also reminds the Clerk on the last day to report a debit to the bank. | [bankwatch/](bankwatch/) |
| Guardian | AI agent (Claude Code, started by Switch Console) | Answers each alarm with numbered jobs, tracks who took which job, chases jobs nobody has taken, and hands the case to the Clerk. | [guardian/family-room-instructions.md](guardian/family-room-instructions.md) |
| Clerk | AI agent (Claude Code) | Keeps the case file as a Switch room document, writes the 1930 complaint and the letter to the bank, and tracks RBI's 3-working-day reporting deadline. If a company doesn't respond, it drafts a post on X. A family member reviews the draft and presses Post themselves, so no agent publishes anything. | [clerk/](clerk/) |
| Ride watch | Python service (no AI) | Check-in timer for a ride alone at night: `@ride-watch 25 min`. If nobody says `reached` in time, it raises an alarm with the driver and vehicle details. A code word raises the alarm at once. | [ridewatch/](ridewatch/) |
| Call watch | Python service (no AI) | The parent gives the family's Twilio number a missed call. Call watch rejects the call, so the parent isn't charged, and posts an SOS to the group. | [callwatch/](callwatch/) |
| Line (optional) | AI agent | A help line for the parent on WhatsApp or SMS, in Hindi, English or Hinglish. It refuses scam requests such as "install AnyDesk" and alerts the family. It needs the Switch adapters in open PRs, so it is not part of the main demo. | [guardian/line-instructions.md](guardian/line-instructions.md) |

How Switch is used: the Telegram bridge makes the group a room. The services post through the agent API (`POST /agents/{id}/message`), and Ride watch also reads the agent event stream (`GET /agents/{id}/events`). Agents hand work to each other with @-mentions. Room instructions (`update_room`) define each agent's role, and the case file is a room document (`create_room_document`). The README's "How Switch is used" table has the details.

## The design document and the evidence

The design document is [docs/design.md](docs/design.md). It explains why the bank's own confirmation call fails here (it reaches the person the scammer controls), who does what, how an alarm starts, and what is out of scope.

The problem, from sources published in 2026:

- **Scale.** The Ministry of Home Affairs told the Supreme Court of 21,900+ digital-arrest complaints involving ₹647 crore+ from January to August 2026. Complaints fell from 1.24 lakh in 2024 to 58,239 in 2025. ([Hindustan Times, 23 Oct 2026](https://www.hindustantimes.com/india-news/21900-digital-arrest-complaints-registered-till-sept-mha-to-sc-101792697131006.html))
- **Isolation is how the scam works.** Victims are kept on video calls "for hours or even days" and told not to contact anyone. ([Indian Express, 30 Oct 2026](https://indianexpress.com/article/explained/digital-arrest-scams-supreme-court-rbi-bank-liability-explained-10943089/))
- **Older people are the main targets, and the official recommendation matches this design.** The NHRC says these cybercrimes mostly affect elderly people and recommends "trusted-person authentication" alerts. ([PIB, 9 Jun 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2270875&lang=1&reg=3))
- **Family members have stopped these scams.** A daughter in Lucknow saved her father ₹60 lakh ([Amar Ujala](https://www.amarujala.com/lucknow/up-digital-arrest-daughter-saves-86-year-old-father-from-being-duped-2026-04-22)). A daughter in Rajkot stopped ₹41 lakh more from leaving ([India Today](https://www.indiatoday.in/cities/other-cities/story/digital-arrest-scam-rajkot-elderly-couple-duped-rs-55-5-lakh-fake-mumbai-crime-branch-officers-2981908-2026-08-28)). An 8-year-old in Bareilly ended a 10-hour scam call ([India Today](https://www.indiatoday.in/india/story/digital-arrest-cyber-scam-bareilly-8-year-old-boy-saves-parents-2894121-2026-04-10)). These are individual stories. We found no study that measures how often family help stops these scams.

## Digital arrest is the first example, not the limit

Digital arrest is the sharpest case, so it came first. The pattern underneath is general:

1. **A watcher in plain code notices something** that the person in trouble can't or won't report: a bank SMS, a missed check-in, a missed call.
2. **It posts an alarm in a shared room**, where people and AI agents work together.
3. **An agent turns the alarm into jobs** and makes sure each one has an owner.
4. **Another agent does the paperwork** against whatever deadline applies.
5. **People do what only people can**: make the call, decide, and press Post.

Ride watch (a ride alone at night) and Call watch (a parent who can't type) already use this pattern for problems that aren't scams. Other uses would need only a new watcher and new room instructions, not a new system. These aren't built:

- An older parent living alone who misses a daily check-in or a medicine reminder.
- A SIM-swap or new-device alert from a phone carrier.
- Deadlines that a parent can't manage alone: a pension life certificate, KYC renewal, an insurance claim, a refund complaint.
- Anyone in a group who needs several people to act at once: a student far from home, or a relative in hospital.

[docs/roadmap.md](docs/roadmap.md) lists what is planned next.

## Run it from a fresh clone

### 0. Requirements

| Need | Version | Why |
|---|---|---|
| Python | **3.11 or newer** | Config is read with `tomllib`, which is in the standard library from 3.11. Nothing else needs installing: there is no `pip install` and no `requirements.txt`. |
| Git | any | to clone the repo |
| Switch Console | current release ([docs.switchagents.ai](https://docs.switchagents.ai/)) | runs a local Switch server and starts the agents (only for the Telegram demo) |
| Claude Code | current release | the Guardian and the Clerk run on it (only for the Telegram demo) |
| Telegram account | | the family group (only for the Telegram demo) |
| Twilio, cloudflared | | only for the missed-call SOS (step 6 in the README) |
| Node.js | | only to build the website in `web/`. Not needed to run Parent Line |

If `python3 --version` shows something older than 3.11, install a newer Python and use it by name for every command, for example `python3.12`:

- macOS: `brew install python@3.12`
- Windows: `py install 3.12`, or the installer from python.org
- Any OS, with uv: `uv python install 3.12`

On an older Python, Parent Line stops with a message saying which version to install. It doesn't crash with an import error.

### 1. Check this machine (2 minutes, no Switch needed)

```bash
git clone https://github.com/prx-my/parent-line
cd parent-line
python3 check.py
```

`check.py` checks five things:

- the Python version, with the install command if it is too old;
- that all the repo files are there;
- that `family.toml` exists and parses (it is created from `family.example.toml` if missing);
- that the unit tests pass;
- that a sample scam SMS produces the alarm.

It then reports the tools that later steps need: Claude Code, Switch credentials, cloudflared and Node.

Every line reads `OK`, `NOTE` (needed only for a later step) or `FAIL` (with the fix). It exits non-zero if anything required fails. It needs no network and no Switch, and it changes nothing except creating `family.toml` when that file is missing.

To see the alarm the family group would get:

```bash
python3 -m bankwatch simulate "Dear Customer, A/C X1234 debited by Rs.480000.00 on date 06Nov26 by IMPS to RAKESH KUMAR Ref 431234567890. If not u? call 1800111109. -SBI" --at 23:40 --dry-run
```

A dry run posts nothing and records nothing, so you can repeat it.

### 2. Connect Switch and Telegram (about 20 minutes)

These steps follow the README's "Run it" section, step by step. Use the README for the exact clicks and the troubleshooting table.

1. **Server and bot.** In Switch Console, choose **Add a server** → **Run a server on this computer**. Create a Telegram bot with @BotFather, and **turn Group Privacy off before adding the bot to any group**. Then in Console: **Messaging apps** → **Connect** → **Telegram**.
2. **Family group and agents.** Make a Telegram group, add the bot, and send `hi`. Copy the room id from Console. Create these agents in Console:
   - `guardian`: Claude Code, working directory `guardian/`, **Who can talk to your agent** set to **Anyone**.
   - `clerk`: Claude Code, working directory `clerk/`, **Anyone**, with **Auto mode off**.
   - `bank-watch`: working directory `bank-watch/`. Run `mkdir -p bank-watch` first. This agent never runs an AI session.

   In the group, send `!invite-agent @guardian`, `!invite-agent @clerk` and `!invite-agent @bank-watch`.
3. **Configure.** In `family.toml`, set `room_id` and the `[family]` table. Then run `python3 -m bankwatch setup`. It should print a ✓ for each check and set the Guardian's instructions. Run `python3 check.py` again: the credentials line should now read `OK`.
4. **Fire an alarm:** run the `simulate` command above without `--dry-run`. The alarm appears in Telegram, and the Guardian answers with three jobs within seconds. Reply `@guardian I'll take 1` to claim one. Ask `@clerk please open a case` to get a case file.
5. **Optional.** Ride watch: `python3 -m ridewatch serve`, after creating a `ride-watch` agent and pressing **Stop** under **Room watcher**. Missed-call SOS: `python3 -m callwatch serve`, with Twilio and cloudflared. Both are README steps 5 and 6.

### Common problems with a fresh setup

| Symptom | Cause and fix |
|---|---|
| `No module named tomllib`, or "Parent Line needs Python 3.11 or newer" | Python is older than 3.11. Install a newer one (see step 0) and run every command with it. |
| `python3 check.py` fails on tests | Run `python3 -m unittest discover -s tests -v` and read the first failure. The project has no packages to install, so the cause is the Python version or a modified file. |
| The group never appears in Console | Group Privacy was on when the bot joined. Turn it off, then remove the bot from the group and add it again. |
| `setup` says `credentials file … does not exist` | Create the `bank-watch` agent in Console with the repo's `bank-watch/` folder as its working directory. |
| `simulate` says "No alarm … or was already handled in the last hour" | That SMS was already posted in the last hour. Delete `bankwatch-state.json`. |
| The alarm posts but the Guardian is silent | Set the Guardian's **Who can talk to your agent** to **Anyone**, and check that Claude Code is set up as a provider in Console. |

## Repository map

| Path | Contents |
|---|---|
| `check.py` | Check for a fresh machine (step 1) |
| `bankwatch/` | SMS parser, scam rules, alarm text, Switch client, and the `simulate`, `serve`, `setup` and `remind` commands |
| `ridewatch/`, `callwatch/` | Ride check-in, and the missed-call SOS. They reuse Bank watch's config and Switch client |
| `guardian/` | Room instructions for the Guardian and the Clerk (`family-room-instructions.md`) and for Line |
| `clerk/` | The Clerk's working directory. `xpost.py` checks X drafts and builds the link that pre-fills a post |
| `tests/` | Unit tests, standard library `unittest`. They make no network calls |
| `family.example.toml` | Template for `family.toml`, which is git-ignored and holds family details |
| `docs/` | Design document, roadmap, and the WhatsApp template plan |
| `web/` | The project website (Astro). Not needed to run Parent Line |

## Rules for anyone changing this code

- Use only Python's standard library, and keep it working on Python 3.11 or newer. A new dependency would break the "clone and run" promise.
- Decisions about whether to wake the family stay in plain, tested code. AI agents coordinate people and write documents. They never decide whether an alarm fires.
- No agent publishes anything on its own. Public posts go out only when a person presses Post.
- Never commit `family.toml`, `*-state.json` or `.switch/`, because they hold family details and Switch credentials. `.gitignore` covers them.
- Run `python3 check.py` before you push.
