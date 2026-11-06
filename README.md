# Parent Line

Older parents can call, text and send voice notes, but settings, apps and "how do I…" questions leave them stuck, and their children aren't always free to help. Scammers use exactly that gap: "install AnyDesk", "tell me the OTP", "scan this to get your refund". And digital-arrest scammers win by isolation: they keep an elderly victim on a video call for hours and forbid them to talk to anyone.

Parent Line is a help line for parents, staffed by AI agents and backed by the family. It helps the parent one step at a time on WhatsApp or SMS, refuses and raises the alarm when a request is really a scam, and brings the family in when a person is needed.

It is built on [Switch](https://github.com/sandbox-quantum/switch), which connects the family's Telegram group, the AI agents and, optionally, the parent's WhatsApp.

## How it works

1. **The parent asks Line for help, in Hindi, English or Hinglish.** Line, an agent in the parent's WhatsApp or SMS chat, walks them through it one step per message, reading photos of their screen. If they get stuck, Line posts a help case to the family with everything the caller needs to know: what they want, their phone, where they're stuck. If the request is on Line's danger list (a remote-control app, an OTP, a "police" video call), Line refuses, tells the parent it's a scam, and raises an alarm instead.
2. **An alarm also starts without the parent having to spot the scam.** Bank watch reads the parent's bank SMS and fires on scam patterns: a large debit, a new payee, an FD broken early, a loan, several debits close together, a debit late at night.
3. **The family group gets the alarm.** It lands in the family's Telegram group, addressed to the Guardian agent.
4. **The family and the Guardian respond together.** Someone calls the parent on a normal call. Someone reports on 1930 or cybercrime.gov.in. Someone calls the bank. The Guardian tracks who has which job, chases anyone who hasn't answered, and closes the alarm when the parent is safe.
5. **The Clerk handles the paperwork.** It keeps a case file as a Switch room document, writes the 1930 complaint and the letter to the bank, and tracks RBI's reporting deadline: 3 working days for an unauthorised debit, with a reminder on the last day. When a bank, ride app or railway doesn't answer, it drafts a public post on X tagging the company. The post goes out only after a family member approves it on Switch's approval card, and never carries names, phone numbers or account numbers.

The bank already confirms big transfers, but it confirms them with the parent, who has been told what to say. Parent Line tells someone the scammer isn't controlling. The full design is in [docs/design.md](docs/design.md).

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

Then, as the family replies:

> 1 ⏳ Riya calling Mom
> 2 ❌ nobody yet
> 3 ✅ Arjun, SBI blocked transfers
> Arjun, can you take 2? I'll write the complaint.

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
| **Line** (optional) | The parent's help line: an AI agent in their WhatsApp or SMS chat | Switch's WhatsApp or SMS bridge makes the chat a room. Line helps the parent there, then hops to the family room (`connect_to_room`) to post a help case or raise an alarm. Its behaviour is the room's instructions: [guardian/line-instructions.md](guardian/line-instructions.md). Those bridges are in our fork of Switch and not yet merged; see step 4 below. |

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

### 2. The family group and the two agents

1. Make a Telegram group (this is the family group), add your bot, and send `hi`. The room appears in Switch Console. Copy its room id.
2. In Switch Console, create two agents:
   - `guardian`: Claude Code, any working directory. Under **Who can talk to your agent**, choose **Anyone**, so the family and Bank watch can address it.
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

Add `--dry-run` to see an alarm without posting it. The same SMS counts as a duplicate for an hour; delete `bankwatch-state.json` to fire it again.

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
| `simulate` says `No alarm` the second time | It's a duplicate within the hour. Delete `bankwatch-state.json` |

### Optional extras

- **Follow the conversation.** On a server you run yourself, add `follow_the_conversation` to `FEATURE_FLAGS_ENABLED` in its `.env` and restart it, then send `!assign-agent @guardian` in the group. Family replies then reach the Guardian without `@guardian`.
- **Publishing on X.** Create an X developer app with Read and Write permission. Put its four OAuth 1.0a keys in `family.toml` under `[x]` (see `family.example.toml`), or in `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN` and `X_ACCESS_SECRET`. X charges about $0.01 a post on its pay-per-use API. Before anything is posted, `xpost.py` refuses drafts with phone numbers, email addresses, long account-style numbers, or more than 280 characters.
- **Real bank SMS.** Run `python3 -m bankwatch serve`, expose port 8787 with a tunnel (for example `cloudflared tunnel --url http://localhost:8787`), and point an SMS-forwarder app on the parent's Android phone at `https://<tunnel>/sms?key=<webhook_secret>`. It accepts JSON (`text`, `message`, `body`, `msg` or `sms`) or plain text. `serve` also posts the Clerk's deadline reminders, checking every 15 minutes.
- **The parent's help line (Line) on WhatsApp or SMS.** This needs our fork of Switch, which adds the WhatsApp and SMS adapters ([sandbox-quantum/switch#1166](https://github.com/sandbox-quantum/switch/pull/1166), not merged), plus your own Meta app or SMS number. Create an agent named `line`, put it in the parent's chat room and the family room, and set [guardian/line-instructions.md](guardian/line-instructions.md) as the parent's chat room's instructions.

### Tests

```bash
python3 -m unittest discover -s tests
```

## Limits

- Bank watch reads SMS text. A bank whose SMS it can't read raises no alarm, and payee names are read only when the bank writes them in capitals.
- If the parent's phone is off, or the bank sends no SMS, nothing reaches Bank watch.
- Parent Line can't stop a transfer. Only the bank can, which is why "call the bank" is one of the three jobs.
