# Parent Line roadmap

What is built, what is waiting on Switch, and what comes next. Each item says where to start and when it is done.

## Built and running today

- **Bank watch**: bank SMS rules, the alarm in the family group, the reminder on the last day to report (`bankwatch/`).
- **Guardian**: the family room's agent; hands out the three jobs, tracks them, chases untaken jobs (`guardian/family-room-instructions.md`).
- **Clerk**: case file as a Switch room document, the 1930 complaint and bank letter, RBI's 3-day deadline, X posts behind an approval card (`clerk/`).
- **Ride watch**: check-in timer for a ride alone at night, code word, driver details and screenshots (`ridewatch/`).
- **Call watch**: the parent's missed call to the family's Twilio number is an SOS; the call is rejected so it costs nothing (`callwatch/`).
- **Line's instructions**: the parent's help line in Hindi, English and Hinglish (`guardian/line-instructions.md`). It runs only on the WhatsApp or SMS adapter below.

## 1. Switch adapters: get them merged

Parent Line's parent-side features depend on these. They are changes to [Switch](https://github.com/sandbox-quantum/switch), not to this repo.

| Item | State | Done when |
|---|---|---|
| WhatsApp adapter, [sandbox-quantum/switch#1166](https://github.com/sandbox-quantum/switch/pull/1166) | open PR | merged; Line runs on official Switch |
| SMS through Twilio, [sandbox-quantum/switch#1244](https://github.com/sandbox-quantum/switch/pull/1244) | open PR | merged |
| SMS hourly limit kept in the database, shared by every server instance | local branch `sms-db-budget`, not pushed | pushed into #1244 or its own PR |
| Hide tool calls in Telegram, [sandbox-quantum/switch#1585](https://github.com/sandbox-quantum/switch/pull/1585) | open PR | merged; Telegram chats show only the agents' answers |
| WhatsApp template messages: message someone outside WhatsApp's 24-hour window | local branch `feat/whatsapp-templates`, one commit, not pushed | PR stacked on #1166; plan in [docs/whatsapp-template-plan.md](whatsapp-template-plan.md) |

#1166 and #1244 conflict with each other today, so one server runs one or the other. Resolving that is part of merging them.

## 2. The family group on WhatsApp

Most Indian families' group chat is on WhatsApp, not Telegram. Today the family room is a Telegram group.

- **First, find out what's possible.** Check what Meta's WhatsApp Cloud API allows for group chats today: whether a business number can be in a group, the size limit, how members join, and the cost. Write the answer here before building anything.
- **If groups work:** extend the WhatsApp adapter to make a group a Switch room, then run the family room there. The Guardian's instructions use only bold, numbered lines and bullets, so they carry over.
- **If they don't:** keep the family room on Telegram and say so in the README.
- **Done when:** an alarm from `python3 -m bankwatch simulate` lands in a WhatsApp family group and the Guardian answers there.

## 3. Line reaches the family first

Line can only answer the parent today. With templates (item 1) it can also start a conversation.

- "Your daughter is calling you, please pick up": sent to the parent during an alarm, as an approved template, in English and Hindi.
- Alert a trusted person on WhatsApp who isn't in the family group.
- **Done when:** during an alarm, the parent gets the template message even with no chat in the last 24 hours.

## 4. When nobody in the family answers

Use case 6 in `docs/design.md`. The Guardian chases once, but it can't keep time, and only acts when someone writes to it.

- A small timer service like Ride watch (plain code, an agent identity with no AI session) that re-raises an unanswered alarm on a schedule and names people, then the backup contact.
- **Done when:** with nobody replying, the alarm is repeated at set intervals and finally reaches the backup contact, with tests for the schedule.

## 5. More banks, fewer missed alarms

- Parsers and tests for the SMS formats of the main Indian banks (HDFC, ICICI, Axis, Kotak, PNB, Bank of Baroda, and others), beside the SBI and generic rules in `bankwatch/parse.py`.
- Payee names written in lower case (today only capitals are read).
- A bank-holiday calendar for the "report to the bank by" date, which today counts every day but Sunday.
- **Done when:** each bank has real sample SMS in `tests/` (with account numbers and names replaced by placeholders).

## 6. Real bank SMS from a real phone

- Test an Android SMS-forwarder app posting to `python3 -m bankwatch serve` over days, with the phone locked and on battery saver.
- Write the setup steps for a non-technical family member, with screenshots.
- **Done when:** the README names an app and settings that were tested for a week on a real phone.

## 7. More languages

- Gujarati and Marathi for Line and the Guardian, after Hindi, English and Hinglish.
- Public posts stay in English.
- **Done when:** a parent writing in Gujarati or Marathi gets every answer in that language, including the scam refusal.

## 8. Ride watch knows where the rider is

Today it knows only that the rider hasn't said "reached".

- Telegram live location reaching agents through Switch's Telegram bridge. This is a Switch change.
- Then: is the vehicle getting closer to home? Raise the alarm early if it moves away.
- **Done when:** a shared live location reaches Ride watch and an alarm can fire on distance, not only on time.

## 9. Complaints for women's safety

Some helplines won't take a complaint filed by someone else for the person it happened to. The Clerk can prepare the complaint so the person files it themself, with the family's help.

- Complaint texts for harassment on public transport and in ride apps: who to file with, what to include, and the escalation path.
- **Done when:** after a ride alarm or a reported incident, the Clerk opens a case file and gives a complaint ready for the person to file.

## 10. Hosting for families who can't run Switch

Ideally each family runs its own Switch. Many can't.

- A hosted option: one Switch server per family, run for a small fee, with each family's data kept apart.
- A setup flow for a non-technical family: one link, connect Telegram (or WhatsApp), add family members, done. Today's setup is the 20-minute developer path in the README.
- **Done when:** a family with no laptop can get from nothing to a working alarm.

## 11. Line as a full help desk

Line already helps step by step and refuses scam requests. Next:

- Split it into a front desk (understands what the parent wants, routes it) and a tutor (teaches one phone task at a time, checks each step with a photo).
- **Done when:** a parent can get a common phone task done end to end in Hindi with Line, and a scam request in the middle of it still raises the alarm.

## Not planned

- Stopping a transfer: only the bank can do that.
- A direct bank integration: bank SMS is the only feed.
- An agent placing phone calls.
- Scams that never touch the bank account, and scammers pretending to be a family member.
