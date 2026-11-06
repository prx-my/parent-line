# Parent Line

Digital-arrest scammers win by isolation: they keep an elderly victim on a video call for hours and forbid them to talk to anyone. Parent Line breaks that isolation by bringing the family in.

It is built on [Switch](https://github.com/sandbox-quantum/switch), which connects the family's Telegram group, the AI agents and, optionally, the parent's WhatsApp.

## How it works

1. **An alarm starts without the parent having to spot the scam.** Bank watch reads the parent's bank SMS and fires on scam patterns: a large debit, a new payee, an FD broken early, a loan, several debits close together, a debit late at night. Or the parent asks "is this real?" on WhatsApp.
2. **The family group gets the alarm.** It lands in the family's Telegram group, addressed to the Guardian agent.
3. **The family and the Guardian respond together.** Someone calls the parent on a normal call. Someone reports on 1930 or cybercrime.gov.in, with a complaint the Guardian drafts. Someone calls the bank. The Guardian tracks who has which job, chases anyone who hasn't answered, and closes the alarm when the parent is safe.

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
> Reply with the number of the job you're taking.

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
| **Bank watch** | A small Python service: [bankwatch/](bankwatch/) | A Switch agent identity with no AI session. When a rule fires, it posts the alarm into the family room through Switch's agent API (`POST /agents/{id}/message`) and @-mentions the Guardian, and Switch delivers that mention. |
| **Line** (optional) | An AI agent in the parent's WhatsApp chat | Switch's WhatsApp bridge makes the chat a room. Line answers the parent there, then hops to the family room (`connect_to_room`) to raise the alarm. The WhatsApp bridge is in our fork of Switch and not yet merged; see step 4 below. |

## Run it

You need Python 3.11+ and Switch Console. Bank watch has no dependencies.

### 1. Switch and Telegram

1. Install Switch Console and add a server. See the [Switch docs](https://docs.switchagents.ai/).
2. Turn on "follow the conversation" for the server: add `follow_the_conversation` to `FEATURE_FLAGS_ENABLED` in its `.env`, then restart it. Without it, family replies reach the Guardian only when they @-mention it.
3. Create a Telegram bot with BotFather. **Turn Group Privacy off before adding it anywhere** (`/mybots` → your bot → **Bot Settings** → **Group Privacy** → **Turn off**).
4. In Switch Console, open the server's **Home** → **Messaging apps** → **Connect** → **Telegram**, and paste the bot token and username.
5. Make a Telegram group for the family, add the bot and send one message. The room appears in Switch Console.

### 2. The Guardian

1. In Switch Console, create an agent named `guardian` (Claude Code). Under **Who can talk to your agent**, choose **Anyone**: the family and Bank watch must be able to address it.
2. Add it to the family room. In the Telegram group: `!invite-agent @guardian`.
3. Set the room's instructions to [guardian/family-room-instructions.md](guardian/family-room-instructions.md) (everything below the line), with the family details at the bottom filled in. Switch Console has no instructions box for a room adopted from Telegram, so set them through the server's API, signed in as an admin: `PATCH /gateway/rooms/{room_id}` with `{"instructions": "…"}`.
4. In the Telegram group: `!assign-agent @guardian`, so every family message reaches it.

### 3. Bank watch

1. Create the agent's folder: `mkdir -p bank-watch`.
2. In Switch Console, create a second agent named `bank-watch`, with that folder as its working directory. Switch Console writes its credentials to `bank-watch/.switch/agents/bank-watch.json`, which is git-ignored. Bank watch never runs an AI session.
3. Add it to the family room: `!invite-agent @bank-watch` in the Telegram group.
4. `cp family.example.toml family.toml`, then set `room_id` (the family room's id from Switch Console), `webhook_secret` and the rule limits.
5. Try it:

   ```bash
   python3 -m bankwatch simulate "Dear UPI user A/C X1234 debited by 480000.00 on date 06Nov26 trf to RAKESH KUMAR Refno 431234567890. -SBI" --at 23:40
   ```

   The alarm appears in the Telegram group and the Guardian takes over. Add `--dry-run` to see the alarm without posting it. The same SMS is ignored as a duplicate for an hour; delete `bankwatch-state.json` to start fresh.
6. For real bank SMS:
   - run `python3 -m bankwatch serve`
   - expose port 8787 with a tunnel, for example `cloudflared tunnel --url http://localhost:8787`
   - set an SMS-forwarder app on the parent's Android phone to POST bank SMS to `https://<tunnel>/sms?key=<webhook_secret>`. It accepts JSON (`text`, `message`, `body`, `msg` or `sms`) or plain text.

### 4. Optional: the "is this real?" line on WhatsApp

This needs the Switch WhatsApp adapter from our fork ([sandbox-quantum/switch#1166](https://github.com/sandbox-quantum/switch/pull/1166)), plus your own Meta app and WhatsApp Business number. Create an agent named `line`, put it in the parent's WhatsApp room and the family room, and set [guardian/line-instructions.md](guardian/line-instructions.md) as the WhatsApp room's instructions.

### Tests

```bash
python3 -m unittest discover -s tests
```

## Limits

- Bank watch reads SMS text. A bank whose SMS it can't read raises no alarm, and payee names are read only when the bank writes them in capitals.
- If the parent's phone is off, or the bank sends no SMS, nothing reaches Bank watch.
- Parent Line can't stop a transfer. Only the bank can, which is why "call the bank" is one of the three jobs.
