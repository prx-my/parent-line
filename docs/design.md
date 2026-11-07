# Parent Line design

## The rule the design follows

A digital-arrest victim believes the call is real and has been told to tell no one. Parent Line never depends on the parent deciding they are being scammed. The alarm starts from what is happening (money moving, or the parent checking a claim), and it goes to the family, who act on it together with an AI agent.

## Why the bank's own check is not enough

Banks already confirm some large transfers by calling the account holder. In a digital arrest that call reaches the one person the scammer controls. The parent has been told what to say ("yes, it's me, it's for a property deal"), and often the scammer is still on video while they say it. Every check that asks the victim "did you do this?" fails the same way.

Parent Line asks someone else: the family. The NHRC recommends the same idea as "trusted-person authentication".

These scams also rarely end with one transfer. They run for hours or days: a transfer, then an FD broken early, then a loan. Catching the first one saves the rest.

## Who is involved

| Who | What they do |
|---|---|
| **Parent** | Nothing new. Optionally messages Line, their help line, on WhatsApp or SMS. |
| **Family** | Two or more relatives in one Telegram group. They act when an alarm comes in. |
| **Guardian** (AI agent) | Lives in the family group. Raises the alarm and runs the response with the family. |
| **Line** (AI agent) | Lives in the parent's WhatsApp or SMS chat. Helps with phone questions step by step, posts help cases to the family, and raises an alarm when a request is a scam. Optional, see below. |
| **Bank watch** (small service, not an AI) | Reads the parent's bank SMS and raises the alarm when a rule fires. |
| **Switch** | Connects all of them: the Telegram group, the WhatsApp chat and the agents. |

## How an alarm starts

### 1. Money tripwire (Bank watch)

The parent's phone forwards bank SMS to Bank watch: an Android SMS-forwarder app POSTs each SMS to a webhook. Bank watch reads the amount, payee and type, and raises the alarm on:

- a debit above the family's threshold
- a payment to a new payee
- an FD broken early, a loan or an overdraft
- several debits close together
- a debit late at night

The rules are plain code, not an AI judgement: whether to wake the family about money has to be predictable and testable. An ordinary bank SMS goes nowhere, so the family never sees the parent's everyday spending. Only the alarm is posted.

When a rule fires, Bank watch posts the alarm in the family group through Switch and @-mentions the Guardian.

### 2. A scam disguised as a question (Line agent, WhatsApp or SMS)

Many scams reach the parent as an ordinary request for help: "install AnyDesk so the bank can fix your KYC", "tell me the OTP", "scan this to receive your refund". A general assistant answers the question it's asked. Line checks every request against a danger list first. Because the parent already uses Line for everyday phone help, they ask it before doing the risky thing.

### 2b. "Is this real?" (Line agent)

The parent writes on WhatsApp what they are being told. Line:

1. Replies with one short fact in the parent's language: police, CBI, ED, customs and RBI never arrest anyone on a video call and never ask for money to "verify" it. Then the 1930 helpline.
2. Posts the alarm in the family group and @-mentions the Guardian.

It doesn't argue or lecture. It never tells the parent to keep anything from the caller, because that could put them at risk if the caller is watching.

### 3. A ride that didn't end (Ride watch)

The same isolation shows up on a night ride: someone alone in an Ola, Uber, Rapido or auto, and nobody knows if they got home. Ride watch is a check-in timer in the family group. The rider starts it (`@ride-watch 25 min` plus the app's share-trip message), so nobody is tracked by default. Past the expected arrival plus 10 minutes it asks once; with no answer 5 minutes later it posts the alarm and @-mentions the Guardian. A code word raises it at once.

Like Bank watch, it is plain code: reading the time, the timer and the alarm are tested rules, because AI agents can't keep time. It picks the vehicle number, the driver's name, rating and phone, the app and the trip link out of the rider's text. A screenshot of the ride app it keeps unread: if the alarm fires, the Guardian, which is Claude, downloads and reads it. Reading an image is a judgement, so it goes to the AI, and only when it matters. The Guardian's jobs are a normal call, checking the trip link, and 112. Afterwards the Clerk drafts the complaint to the ride app, filed by the rider themself, and the public post if the app doesn't answer.

It knows only that the rider hasn't confirmed, not where they are. Ride apps have no API for a trip, and Switch's Telegram bridge doesn't pass on live location. A location check (is the vehicle getting closer?) needs one of those, and is out of scope for now.

## The help line

Line is the parent's everyday helper on WhatsApp or SMS, in Hindi, English or Hinglish. Its instructions are [guardian/line-instructions.md](../guardian/line-instructions.md).

1. **Safety first.** Every request is checked against a danger list: remote-control apps, app files from links, OTPs and PINs, QR codes or UPI requests to "receive" money, "KYC update" and "account blocked" messages, callers posing as police or customs, "safe accounts", fees for prizes or loans, and customer-care numbers found on Google. On a match Line refuses, tells the parent it's a scam, and raises an alarm.
2. **One step at a time.** One instruction per message, written for their phone model, checked against their reply or a photo of the screen before the next one.
3. **The family when needed.** After three failed steps, or when it needs a password, payment, a person, or they ask for family, Line posts a help case to the family room with what they want, their phone, what's done and where they're stuck. The Guardian finds someone to call, and lets non-urgent cases wait for the morning.

Line never asks for or keeps an OTP, PIN, password or card number, and gives only 1930 or numbers from the parent's card, their bank's SMS, or the family's setup.

## The response, in the family group

This is the workflow the hackathon asks for: the family and the Guardian get a real task done together.

1. **Alarm.** The Guardian says what happened in one line, and why it matches the scam.
2. **Jobs.** It lists the three jobs and asks who takes each:
   - **Call the parent now** on a normal phone call. A ringing call breaks the video call's hold. If the line is busy, try the backup contact: a neighbour or nearby relative named at setup.
   - **Report** on 1930 or cybercrime.gov.in. Reporting fast can get the money frozen.
   - **Call the bank** to block further transfers.
3. **Tracking.** As people reply ("1", "I'll take the bank"), the Guardian posts a status message, one line per job: ⏳ in progress, ✅ done, ❌ nobody yet. If a job is still untaken after 3 minutes, it posts the status again and names people.
4. **Help.** It drafts the cybercrime complaint (amount, time, transaction reference, what the caller claimed), ready to paste. It also gives the bank's fraud line.
5. **Close.** When the family reports the parent safe, or says it was a real payment, the Guardian posts a short summary and closes the alarm.

A false alarm costs one reply: "it's fine, she's buying the flat."

## The Clerk: paperwork, deadlines and public pressure

Reporting is where families give up: it's slow, confusing, and comes when everyone is upset. The Clerk is a second agent in the family room. The Guardian hands it the case once money has moved.

- **Case file.** One Switch room document per incident (`create_room_document`): what happened, evidence, reports filed with their numbers, what's awaited, and what's next. Last 4 digits only; never OTPs, PINs or passwords.
- **Complaint texts.** The 1930 / cybercrime.gov.in text, and the dispute letter to the bank's grievance address, citing RBI's July 2017 circular on customer liability.
- **The deadline.** RBI's rule: an unauthorised electronic debit reported within 3 working days costs the customer nothing when a third party committed the fraud. Bank watch computes the date (code, not AI judgement), shows it in the alarm, and reminds the Clerk on the last day. A payment the parent made themselves under pressure may not be covered, and the Clerk says so.
- **Escalation.** The bank's 30 days, then the RBI Ombudsman (cms.rbi.org.in). For ride apps and others: grievance officer, then the National Consumer Helpline (1915).
- **Public posts.** When a company stays silent, a short English post on X tagging its support account, with a booking ID, vehicle number or complaint number, and never a name, phone, address or account number. `clerk/xpost.py` refuses unsafe drafts. The Clerk runs with Auto mode off, and its Claude Code settings allow its Switch tools and draft checks but make the post command wait for approval. Switch then puts an approval card in the family's chat. In a live test with Auto mode on, Claude Code's own safety review let the post command through without asking, which is why Auto mode stays off for the Clerk. A family member approves the exact text before it goes out.

## How it runs on Switch

| Switch room | Platform | Who is in it | Agent connected there |
|---|---|---|---|
| Family group | Telegram | The family, Guardian, Bank watch, Line | Guardian, as the room's assigned agent (`!assign-agent`), so every family message reaches it. This needs the server's `follow_the_conversation` feature flag. |
| Parent's chat | WhatsApp, one-to-one | The parent, Line | Line |

- **Why two agents.** A Switch agent gets events only from the one room it is connected to, so one agent can't hold the family group and the parent's chat at once. Line raises an alarm by hopping to the family group (`connect_to_room`), posting, and hopping back.
- **The handover is agent to agent through Switch.** Bank watch and Line both raise the alarm by @-mentioning the Guardian in the family group. The Guardian is set to let **Anyone** address it, so another agent's mention reaches it.
- **Bank watch is an agent identity without a session.** It connects to the family group over Switch's agent HTTP API and posts only when a rule fires.
- **The Guardian's behaviour** comes from that room's instructions. They hold the response steps above, the message layouts, and the family details such as the backup contact.
- **Message formatting.** Agents write Markdown, and Switch converts it for each chat app. On Telegram, bold, italics and bullets survive; headings become bold and tables stay as plain text. So the Guardian's layouts use only bold, numbered lines and bullets.

### Core and optional

| Part | Runs on | Reproducible from a clone of official Switch? |
|---|---|---|
| Bank watch → family Telegram group → Guardian + family | official Switch (Telegram bridge, agent API) | yes |
| Parent's help line (Line) on WhatsApp or SMS | Switch WhatsApp adapter, from the team's fork (PR sandbox-quantum/switch#1166, not merged) | no, runs from the fork |

The core works without the WhatsApp part.

The WhatsApp part needs the team's own Meta app and business number. A WhatsApp business may send free-form messages only within 24 hours of the person's last message. If Line must message the parent first (for example "your daughter is calling you, please pick up"), that goes as an approved template. Templates are built on the fork's `feat/whatsapp-templates` branch.

## Use cases

| # | Situation | What happens | Status |
|---|---|---|---|
| 1 | Parent on a scam call, unsure, hasn't paid | Asks Line on WhatsApp. Gets one fact and 1930. The family is alerted | covered (WhatsApp part) |
| 2 | Parent convinced, pays, confirms the bank's call | The debit SMS reaches Bank watch and the family is alerted | covered, the main case |
| 3 | Told to split the money into small transfers | "Several debits close together" fires | covered |
| 4 | Breaks an FD or takes a loan | The bank SMS for it fires, before money leaves | covered |
| 5 | Parent's phone busy on the scam video call | A normal call still shows as waiting. The Guardian suggests the backup contact | covered if a backup is set |
| 6 | Nobody in the family answers | The Guardian repeats the alarm and names people | to build |
| 7 | Real payment, false alarm | One family reply closes it | covered |
| 8 | Money already gone | Complaint draft, 1930, bank freeze. Speed is the point | covered |
| 9 | Parent told to switch the phone off | Bank SMS may still arrive. If none arrive, nothing reaches Bank watch | not covered, said plainly |
| 10 | Parent doesn't want to be "watched" | The parent agrees at setup. Bank watch sees bank SMS only, never calls or chats, and passes on only alarms | ground rule |

## Demo

1. The family Telegram group is open on screen, with the Guardian in it.
2. A sample bank SMS goes through Bank watch's simulate command (₹4,80,000 to a new payee at 23:40). It runs through the same parser and rules as a forwarded SMS. The video says it is simulated.
3. The alarm appears in the family group. Two relatives take the jobs, the Guardian drafts the complaint, and someone reports the parent safe. The Guardian closes the alarm.
4. If WhatsApp is ready: the parent asks Line for help changing their profile photo and gets it step by step; on another request they get stuck, and a help case reaches the family with a screenshot. Then the parent asks "bank wale bol rahe AnyDesk download karo". Line refuses, and the family group lights up with an alarm.

## Languages

Hindi, English and Hinglish (Hindi in Latin letters) first; Gujarati and Marathi next. Line answers in the language the parent writes in. Public posts, when they come, are in English.

## Out of scope for the hackathon

- Stopping a transfer. Only the bank can do that.
- A real bank integration. Bank SMS is the only feed.
- The agent placing a phone call.
- Scams that never touch the bank account (gift cards, cash or crypto handed over in person).
- A scammer pretending to be a family member.

## Open questions

- Each bank's SMS format differs. Start with the formats of the banks the demo family uses, plus a generic "debited ... Rs/INR" rule.
- Can an Android forwarder app POST to a webhook reliably in the background? Test on a real phone.
- The thresholds and the "late night" window should be set per family at setup.
