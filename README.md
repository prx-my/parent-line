# Parent Line

Digital-arrest scammers win by isolation. They keep an older parent on a video call for hours, forbid them to tell anyone, and walk them through sending their savings to "clear their name". The bank's confirmation call doesn't help: it reaches the one person the scammer controls, who has been told what to say.

Parent Line tells the family instead. When the parent's bank SMS looks like a scam, an alarm lands in the family's Telegram group, and the family and two AI agents work it together. Someone calls the parent, someone reports it, someone calls the bank, and the paperwork is done before the bank's reporting deadline.

It runs on [Switch](https://github.com/sandbox-quantum/switch), which makes the family's Telegram group a room where family members, AI agents and a small bank-SMS service all work together.

## How it works

1. **Bank watch reads the parent's bank SMS.** It fires on scam patterns: a large debit, a new payee, an FD broken early, a loan, several debits close together, a debit late at night. The rules are plain code, not an AI judgement, so they are predictable and tested. Ordinary spending goes nowhere; the family sees only alarms.
2. **The alarm lands in the family group**, addressed to the Guardian agent. The parent never has to spot the scam themselves.
3. **The family and the Guardian respond together.** Someone calls the parent on a normal call, which breaks the video call's hold. Someone reports on 1930 or cybercrime.gov.in. Someone calls the bank. The Guardian tracks who has which job, chases the jobs nobody took, and closes the alarm when the parent is safe.
4. **The Clerk handles the paperwork.** The Guardian hands it the case. It keeps a case file as a Switch room document, writes the 1930 complaint and the letter to the bank, and tracks RBI's reporting deadline: 3 working days for an unauthorised debit, with a reminder on the last day. When a bank, ride app or railway doesn't answer, it drafts a public post on X tagging the company. The post goes out only after a family member approves it on Switch's approval card, and never carries names, phone numbers or account numbers.
5. **Ride watch: a check-in for a ride alone at night.** Before an Ola, Uber, Rapido or auto ride, anyone in the group writes `@ride-watch 25 min` and pastes the app's share-trip message. If they haven't said `reached` 10 minutes after that time, Ride watch asks. With no answer in 5 more minutes, it raises the alarm for the Guardian with the vehicle and trip link they shared, and the family gets three jobs: call them, check the trip link, call 112. A code word (`@ride-watch pizza`) raises it at once, for when they can't talk freely. It runs only when someone starts it. Nobody is tracked otherwise.
6. **Optional: Line, the parent's help line.** An agent in the parent's WhatsApp or SMS chat helps with phone questions one step at a time, in Hindi, English or Hinglish. When a request is really a scam ("install AnyDesk", "tell me the OTP"), it refuses and raises the alarm in the family group. This part needs Switch's WhatsApp or SMS adapter, both still open pull requests; everything above runs on official Switch.

The full design is in [docs/design.md](docs/design.md).

## What the family sees

Bank watch posts:

> 🚨 **Bank alarm: Mom** · 23:40
> **₹4,80,000** left the account to **RAKESH KUMAR**.
>
> **Why it looks wrong**
> • Over the ₹50,000 limit
> • Sent to a payee never paid before
> • Late at night (23:40)
>
> **Bank SMS**
> _Dear UPI user A/C X1234 debited by 480000.00 on date 06Nov26 trf to RAKESH KUMAR Refno 431234567890. -SBI_
>
> **Report to the bank by Tue 10 Nov.** If Mom didn't make this payment, reporting by then means Mom shouldn't bear the loss (RBI rules).
>
> @guardian over to you.

The Guardian answers within seconds:

> 🚨 **₹4,80,000 left Mom's SBI account at 23:40**
> To RAKESH KUMAR · ref 431234567890
> Looks like a digital-arrest scam: big amount, new payee, late at night.
>
> 1. **Call Mom now**, normal call, not WhatsApp
> 2. **Report** on 1930 or cybercrime.gov.in
> 3. **Call SBI** on 1800 111 109 (from their SMS)
>
> Reply @guardian with the number of the job you're taking.
> **Report to SBI by Tue 10 Nov.**

Then, as the family replies:

> 1 ⏳ Riya calling Mom
> 2 ❌ nobody yet
> 3 ✅ Arjun, SBI blocked transfers
> Arjun, can you take 2? @clerk is writing the complaint.

The Clerk opens the case file and writes the complaint, ready to paste:

> 📁 Case file opened: case-2026-11-06-sbi-480000

On the last day to report, Bank watch reminds the Clerk:

> ⏰ **Report Mom's debit to the bank by Tue 10 Nov**
> ₹4,80,000 to RAKESH KUMAR at 23:40 on Fri 6 Nov
> If Mom didn't make this payment, reporting it by then means Mom shouldn't bear the loss (RBI rules).
> If they were tricked into paying, report anyway: fast reports are how money gets frozen.
>
> @clerk has it been reported? Post the bank's complaint number.

In a live test on Telegram, the Guardian answered 5 seconds after the alarm and the Clerk updated the case file 28 seconds after it. With no job taken, the Guardian chased the family at 3 minutes ("Call Mom first"). A reply of `@guardian I'll take 1` got the updated job list 2 seconds later.

## The problem

- **It is large.** The Ministry of Home Affairs told the Supreme Court of 21,900+ digital-arrest complaints involving ₹647 crore+ from January to August 2026. Complaints are falling, from 1.24 lakh in 2024 to 58,239 in 2025, but the numbers are still big. ([Hindustan Times, 23 Oct 2026](https://www.hindustantimes.com/india-news/21900-digital-arrest-complaints-registered-till-sept-mha-to-sc-101792697131006.html))
- **It works through isolation.** Victims are kept on video calls "for hours or even days" and told they "must not communicate with anyone else". ([Indian Express, 30 Oct 2026](https://indianexpress.com/article/explained/digital-arrest-scams-supreme-court-rbi-bank-liability-explained-10943089/))
- **It targets the elderly, and the official fix looks like ours.** The NHRC says cybercrimes "mostly affect elderly persons" and recommends "trusted-person authentication" alerts. ([PIB, 9 Jun 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2270875&lang=1&reg=3))

## Family members stop these scams

A family member stepping in has ended real scams:

- A daughter in Lucknow saved her 86-year-old father ₹60 lakh. ([Amar Ujala](https://www.amarujala.com/lucknow/up-digital-arrest-daughter-saves-86-year-old-father-from-being-duped-2026-04-22))
- A daughter in Rajkot stopped ₹41 lakh more from leaving her parents' account. ([India Today](https://www.indiatoday.in/cities/other-cities/story/digital-arrest-scam-rajkot-elderly-couple-duped-rs-55-5-lakh-fake-mumbai-crime-branch-officers-2981908-2026-08-28))
- An 8-year-old in Bareilly ended a 10-hour scam call on his parents. ([India Today](https://www.indiatoday.in/india/story/digital-arrest-cyber-scam-bareilly-8-year-old-boy-saves-parents-2894121-2026-04-10))

These are single stories. We found no study measuring how often family help stops these scams.

## How Switch is used

Switch connects every part. Without it, nothing reaches anyone.

| Part | What it is | How it uses Switch |
|---|---|---|
| **Family group** | A Telegram group | Switch's Telegram bridge makes it a Switch room. Family messages reach the Guardian, and its replies appear in Telegram. |
| **Guardian** | An AI agent (Claude Code, started by Switch Console) | Connected to the family room as its assigned agent. Its behaviour is the room's instructions: [guardian/family-room-instructions.md](guardian/family-room-instructions.md). |
| **Clerk** | An AI agent (Claude Code), working in [clerk/](clerk/) | In the family room beside the Guardian. The Guardian hands it the case (`@clerk please open a case`), an agent-to-agent handoff through Switch. It keeps the case file as a Switch room document (`create_room_document`). Its public posts run `clerk/xpost.py`, which [clerk/.claude/settings.json](clerk/.claude/settings.json) makes wait for approval, so Switch puts an approval card in the family's chat. |
| **Bank watch** | A small Python service: [bankwatch/](bankwatch/) | A Switch agent identity with no AI session. When a rule fires, it posts the alarm into the family room through Switch's agent API (`POST /agents/{id}/message`) and @-mentions the Guardian, and Switch delivers that mention. It also reminds the Clerk on the last day to report a debit to the bank. `setup` uses its agent key to set the room's instructions (`update_room`). |
| **Ride watch** | A small Python service: [ridewatch/](ridewatch/) | Another Switch agent identity with no AI session. It reads the messages addressed to it through Switch's agent event stream (`GET /agents/{id}/events`, a long poll), keeps the clock that the AI agents can't, and posts the check-in and the alarm through the same API as Bank watch. The alarm @-mentions the Guardian. |
| **Line** (optional) | The parent's help line: an AI agent in their WhatsApp or SMS chat | Switch's WhatsApp or SMS bridge makes the chat a room. Line helps the parent there, then hops to the family room (`connect_to_room`) to post a help case or raise an alarm. Its behaviour is the room's instructions: [guardian/line-instructions.md](guardian/line-instructions.md). Those adapters are open pull requests to Switch; see Optional extras below. |

## What's in this repo

| Path | What it is |
|---|---|
| [bankwatch/](bankwatch/) | Bank watch: SMS parser (`parse.py`), rules and alarm text (`rules.py`), the Switch client (`switch.py`), room setup (`setup.py`), and the `simulate`, `serve`, `setup` and `remind` commands (`__main__.py`). Python standard library only |
| [ridewatch/](ridewatch/) | Ride watch: reading the arrival time, the check-in and the alarm (`rides.py`), and the `serve` loop (`__main__.py`). It reuses Bank watch's config and Switch client |
| [guardian/family-room-instructions.md](guardian/family-room-instructions.md) | The family room's instructions: the Guardian's and the Clerk's parts, their message layouts, and the family details `setup` fills in |
| [clerk/](clerk/) | The Clerk's working directory: `xpost.py` checks and posts X drafts, and `.claude/settings.json` makes every post wait for approval |
| [guardian/line-instructions.md](guardian/line-instructions.md) | Line's instructions, for the optional WhatsApp or SMS help line |
| [family.example.toml](family.example.toml) | The template for `family.toml`: room, family details, alarm thresholds, optional X keys |
| [tests/](tests/) | Tests for Bank watch, Ride watch and `xpost.py` |
| [docs/design.md](docs/design.md) | The design: why the bank's check isn't enough, the response, use cases, what's out of scope |

## Run it

About 20 minutes. You need no phone and no bank: one Telegram group and a simulated bank SMS show the whole alarm flow.

**You need**

- Python 3.11 or newer (`python3 --version`). Bank watch has no other dependencies.
- [Switch Console](https://docs.switchagents.ai/), with Claude Code set up as an agent provider (Switch docs: *Set up agent providers*).
- A Telegram account.

### 1. A Switch server and a Telegram bot

1. In Switch Console: **Add a server** → **Run a server on this computer**.
2. In Telegram, message [@BotFather](https://t.me/BotFather): `/newbot`, and keep the token it gives you.
3. **Turn Group Privacy off now, before adding the bot to any group**: `/mybots` → your bot → **Bot Settings** → **Group Privacy** → **Turn off**. If you skip this, the bot never sees the family's messages.
4. In Switch Console: the server's **Home** → **Messaging apps** → **Connect** → **Telegram**. Paste the bot token and username.

### 2. The family group and the three agents

1. Make a Telegram group (this is the family group), add your bot, and send `hi`. The room appears in Switch Console. Copy its room id.
2. In Switch Console, create three agents:
   - `guardian`: Claude Code, working directory `guardian/` inside this repo. Under **Who can talk to your agent**, choose **Anyone**, so the family and Bank watch can address it.
   - `clerk`: Claude Code, working directory `clerk/` inside this repo, **Who can talk to your agent** set to **Anyone**, and **Auto mode turned off**. In auto mode, Claude Code's own safety review can let the post command run without asking. With it off, the settings in `clerk/.claude/settings.json` let the Clerk use its Switch tools and check drafts freely, but every public post waits for a family member to approve it.
   - `bank-watch`: working directory `bank-watch/` inside this repo (`mkdir -p bank-watch` first). Switch Console writes its credentials there, git-ignored. It never runs an AI session.
3. In the Telegram group, send:

   ```
   !invite-agent @guardian
   !invite-agent @clerk
   !invite-agent @bank-watch
   ```

### 3. Configure and check

```bash
cp family.example.toml family.toml
```

In `family.toml`, set `room_id` to the id you copied, and fill in `[family]`: the parent's phone, the family members as the group shows them, a neighbour as backup, and the bank. Then:

```bash
python3 -m bankwatch setup
```

`setup` checks that Bank watch can reach the room and that the Guardian is in it. It then sets the Guardian's instructions, [guardian/family-room-instructions.md](guardian/family-room-instructions.md) with your family filled in, as the room's instructions. Nothing is pasted by hand. You should see:

```
✓ Bank watch can reach the family room: …
✓ @guardian is in the room
✓ @clerk is in the room
✓ Set the Guardian's instructions (… characters) with the family details
```

### 4. Fire an alarm

```bash
python3 -m bankwatch simulate "Dear UPI user A/C X1234 debited by 480000.00 on date 06Nov26 trf to RAKESH KUMAR Refno 431234567890. -SBI" --at 23:40
```

The alarm appears in the Telegram group, and the Guardian answers with three jobs. Reply as a family member, for example `@guardian I'll take 1`. The Guardian tracks it, chases the jobs nobody took, and hands the case to the Clerk, which opens the case file and writes the complaint.

Then try the rest of the Clerk:

- **The deadline reminder.** Bank watch posts it on the last day to report. To see it now, pretend it's that day:

  ```bash
  python3 -m bankwatch remind --at "2026-11-10 09:00"
  ```

  Use the "report to the bank by" date from your alarm.
- **A public post.** In the group: `@clerk the bank hasn't replied, draft a post for X`. The Clerk shows a draft, and you reply `@clerk post it`. Switch then shows an approval card in the group, and the post runs only when you approve it. The card shows the exact text. Answer **Allow once**: **Allow for this session** lets the Clerk post again without asking until its session ends. Without X keys it stops at "NOT POSTED"; see the extras below.

Add `--dry-run` to see an alarm without posting it. The same SMS counts as a duplicate for an hour; delete `bankwatch-state.json` to fire it again. Don't change the Refno to get round it: the agents then treat it as a second debit, and the Clerk asks whether there were one or two.

### 5. Watch a ride

1. In Switch Console, create a fourth agent, `ride-watch`, with working directory `ride-watch/` inside this repo (`mkdir -p ride-watch` first). Like Bank watch, it never runs an AI session.
2. In the Telegram group, send `!invite-agent @ride-watch`.
3. Check `[ride]` in `family.toml` (copy it from `family.example.toml` if your file is older). To demo without waiting, set `grace_minutes = 0` and `answer_minutes = 1`.
4. Run it and leave it running:

   ```bash
   python3 -m ridewatch serve
   ```

5. In the group, as the rider: `@ride-watch 1 min` followed by a pasted share-trip message, or a line like `Uber, white Dzire KA 20 AB 1234, to home`. Ride watch answers 👀 with the time it will check. Don't reply. A minute later it asks if you reached, and a minute after that it posts the 🚨 Ride alarm and the Guardian hands out the jobs. Send `@ride-watch reached` to close it.

The time can be `25 min`, `1 hr`, `23:40` or `11:40 pm`. Put it before the pasted message, because a share-trip message can carry its own times ("driver 3 mins away"). `@ride-watch pizza` (the `code_word`) raises the alarm at once. A family member can close someone's ride by name: `@ride-watch Riya reached`.

### If you get stuck

| What you see | Fix |
|---|---|
| The group never appears in Switch Console | Group Privacy was on when the bot joined. Turn it off, remove the bot from the group, and add it again |
| `setup`: `credentials file … does not exist` | `bank-watch`'s working directory must be `bank-watch/` in this repo. Or set `SWITCH_API_ENDPOINT`, `SWITCH_API_TOKEN` and `SWITCH_AGENT_ID` |
| `setup`: `HTTP 403` | Bank watch isn't in the room. Send `!invite-agent @bank-watch` in the group |
| `✗ @guardian isn't in the room` | Send `!invite-agent @guardian` in the group, then run `setup` again |
| The alarm arrives but the Guardian stays silent | Set the Guardian's **Who can talk to your agent** to **Anyone**, and check that Claude Code is set up in Switch Console |
| A family reply gets no answer | Start it with `@guardian`. See "Follow the conversation" below |
| The Clerk publishes, or says NOT POSTED, without an approval card appearing | Turn **Auto mode** off for the `clerk` agent in Switch Console |
| The Clerk posts nothing when you approve a public post | Check the Clerk's working directory is `clerk/` in this repo, so its approval settings and `xpost.py` are found |
| Ride watch never answers 👀 | Check it is running and was invited (`!invite-agent @ride-watch`). If its log says `Ignoring a message from room …`, set `room_id` in `family.toml` to that room |
| `simulate` says `No alarm` the second time | It's a duplicate within the hour. Delete `bankwatch-state.json` |
| Every agent message in Telegram ends with a list of the tools it called | That's the Telegram connection's tool-call display. An open pull request ([sandbox-quantum/switch#1585](https://github.com/sandbox-quantum/switch/pull/1585)) adds a **Show tool calls** box to **Connect** → **Telegram**; untick it when you connect. An existing connection can't be changed from Switch Console or the web dashboard. Leave it on there: disconnecting removes the family room with its instructions and the Clerk's case files, and you would have to set everything up again |

### Optional extras

- **Follow the conversation.** On a server you run yourself, add `follow_the_conversation` to `FEATURE_FLAGS_ENABLED` in its `.env` and restart it, then send `!assign-agent @guardian` in the group. Family replies then reach the Guardian without `@guardian`.
- **Publishing on X.** Create an X developer app with Read and Write permission. Put its four OAuth 1.0a keys in `family.toml` under `[x]` (see `family.example.toml`), or in `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN` and `X_ACCESS_SECRET`. X charges about $0.01 a post on its pay-per-use API. Before anything is posted, `xpost.py` refuses drafts with phone numbers, email addresses, long account-style numbers, or more than 280 characters.
- **Real bank SMS.** Run `python3 -m bankwatch serve`, expose port 8787 with a tunnel (for example `cloudflared tunnel --url http://localhost:8787`), and point an SMS-forwarder app on the parent's Android phone at `https://<tunnel>/sms?key=<webhook_secret>`. It accepts JSON (`text`, `message`, `body`, `msg` or `sms`) or plain text. `serve` also posts the Clerk's deadline reminders, checking every 15 minutes.
- **The parent's help line (Line) on WhatsApp or SMS.** The adapters are open pull requests to Switch: [sandbox-quantum/switch#1166](https://github.com/sandbox-quantum/switch/pull/1166) for WhatsApp and [sandbox-quantum/switch#1244](https://github.com/sandbox-quantum/switch/pull/1244) for SMS through Twilio. They conflict with each other, so one server runs one or the other.
  1. Run switch-core from that pull request's branch, and expose port 8000 over https with a tunnel (`cloudflared tunnel --url http://localhost:8000`, or ngrok).
  2. Set `MESSAGING_PUBLIC_URL` in the server's `.env` to the tunnel's URL and restart it.
  3. In Switch Console: **Connect** → **WhatsApp** (or **SMS**), then point the platform's webhook at the address Console shows. For WhatsApp, Meta's free test number is enough: add up to five recipients on the app's **API Setup** page.
  4. Create an agent named `line`, put it in the parent's chat room and the family room, and set [guardian/line-instructions.md](guardian/line-instructions.md) as the parent's chat room's instructions.

### Tests

```bash
python3 -m unittest discover -s tests
```

## Limits

- Bank watch reads SMS text. A bank whose SMS it can't read raises no alarm, and payee names are read only when the bank writes them in capitals.
- If the parent's phone is off, or the bank sends no SMS, nothing reaches Bank watch.
- The "report to the bank by" date counts every day but Sunday as a working day. Bank holidays only make the real deadline later, so the date shown is never too late, but it can be a day or two early.
- `xpost.py` catches phone numbers, emails and long account-style numbers by pattern, not names or addresses. That is why a family member reads and approves every post.
- Parent Line can't stop a transfer. Only the bank can, which is why "call the bank" is one of the three jobs.
- Ride watch knows only that the rider hasn't said they reached, not where they are. Ola, Uber and Rapido offer no API for a trip, so the location is the share-trip link a person opens, and Switch's Telegram bridge doesn't pass on Telegram's live location.
- Ride watch only watches rides someone starts. It doesn't replace 112 or the ride app's SOS button; it makes sure the family notices and acts.
- The ride alarm appears in the family group, which is on the rider's phone too. Someone reading their screen after the code word will see it.
