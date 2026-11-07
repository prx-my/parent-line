---
title: "The scam works because nobody else is on the call"
description: "Parent Line: a family group chat, a few AI agents, and one rule: the parent never has to handle it alone. Built on Switch for the WeMakeDevs Flip the Switch hackathon."
date: 2026-11-07
---

My father's card was misused in small steps first: ₹5, then ₹10, then ₹20. Then about ₹2–3 lakh went. Each step looked too small to worry about, and by the time anyone looked at the whole picture, the money was gone.

That story, and a few from friends (a night auto ride that felt wrong, a helpline that wouldn't take a complaint from anyone but the victim), all have the same shape. **The person can't act alone, needs several people, and the problem crosses several apps.** Parent Line is my attempt to build for that shape.

## The problem: isolation is the attack

Take "digital arrest" scams, where a caller poses as police or a government agency, puts an older person on a video call, and says they're under investigation.

- The Ministry of Home Affairs told the Supreme Court of **21,900+ digital-arrest complaints involving ₹647 crore+** from January to August 2026. Complaints are falling, from 1.24 lakh in 2024 to 58,239 in 2025, but the numbers are still large. ([Hindustan Times, 23 Oct 2026](https://www.hindustantimes.com/india-news/21900-digital-arrest-complaints-registered-till-sept-mha-to-sc-101792697131006.html))
- Victims are held on calls "for hours or even days" and told they "must not communicate with anyone else". ([Indian Express, 30 Oct 2026](https://indianexpress.com/article/explained/digital-arrest-scams-supreme-court-rbi-bank-liability-explained-10943089/))
- The NHRC says cybercrimes "mostly affect elderly persons" and recommends "trusted-person authentication" alerts. ([PIB, 9 Jun 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2270875&lang=1&reg=3))

The bank's confirmation call doesn't fix this. It reaches the one person the scammer controls, and that person has been told what to say. The scam only breaks when someone else gets in.

Families have done exactly that: a daughter in Lucknow saved her 86-year-old father ₹60 lakh ([Amar Ujala](https://www.amarujala.com/lucknow/up-digital-arrest-daughter-saves-86-year-old-father-from-being-duped-2026-04-22)), a daughter in Rajkot stopped ₹41 lakh more from leaving her parents' account ([India Today](https://www.indiatoday.in/cities/other-cities/story/digital-arrest-scam-rajkot-elderly-couple-duped-rs-55-5-lakh-fake-mumbai-crime-branch-officers-2981908-2026-08-28)), and an 8-year-old in Bareilly ended a 10-hour scam call on his parents ([India Today](https://www.indiatoday.in/india/story/digital-arrest-cyber-scam-bareilly-8-year-old-boy-saves-parents-2894121-2026-04-10)). I should be straight about this: these are single stories. I found no study that measures how often family help stops these scams. But the pattern is hard to miss.

## What Parent Line does

When the parent's bank SMS looks like a scam, an alarm lands in the **family's Telegram group**. The parent doesn't have to spot anything. The family and two AI agents then work it together:

1. **Bank watch** reads the bank SMS and fires on plain, tested rules: a large debit, a new payee, a fixed deposit broken early, a loan, several debits close together, a debit late at night. These are code, not an AI's judgement, so they're predictable. Ordinary spending goes nowhere.
2. **The Guardian** (an AI agent) turns the alarm into three jobs: call the parent on a normal call (which breaks the video call's hold), report on 1930 or cybercrime.gov.in, and call the bank. It tracks who took which job, chases the ones nobody took, and closes the case when the parent is safe.
3. **The Clerk** (a second AI agent) does the paperwork: it opens a case file, drafts the 1930 complaint and the bank letter, and tracks RBI's reporting window, 3 working days for an unauthorised debit, with a reminder on the last day.

In a live test on Telegram, the Guardian answered 5 seconds after the alarm, and the Clerk had updated the case file 28 seconds after it. When nobody took a job, the Guardian chased the family at 3 minutes.

Two smaller services grew from the same idea:

- **Ride watch** is a check-in for a ride alone at night. Write `@ride-watch 25 min` and paste the trip-share message. If you haven't said `reached` 10 minutes after that time, it asks, and with no answer in 5 more minutes it raises the alarm with the vehicle number, driver details and trip link. A code word raises it at once, for when you can't talk freely. It runs only when someone starts it, and nobody is tracked otherwise.
- **Call watch** is for a parent who can't type or use an app. They save the family's number as "Family SOS" and give it a missed call. Call watch rejects the call (so it costs nothing) and posts "Mom gave a missed call. Who's calling Mom?" in the family group.

## Why this needed Switch

An alarm in a chat is easy. What makes it work is that **people and agents share one room, with one history, and can hand work to each other.** That is what Switch is for.

- Switch's Telegram bridge turns the family group into a Switch room, so the family and the agents are in the same conversation.
- The Guardian hands the case to the Clerk with an ordinary message (`@clerk please open a case`), an agent-to-agent handoff through Switch. The Clerk keeps the case file as a Switch room document.
- Bank watch, Ride watch and Call watch have **no AI at all**. Each is a small Python service with its own Switch agent identity that posts into the room through Switch's agent API, and delivery of its @-mention to the Guardian is Switch's job. Ride watch reads its messages through Switch's event stream because it has to keep a clock, and AI agents can't keep a clock.
- When the Clerk drafts a public post tagging a bank or a ride app that won't answer, nothing is published by an agent. The Clerk sends a link; tapping it opens X with the text filled in, and a family member presses Post themselves. The draft never carries names, phone numbers or account numbers.

One decision I'd defend: the part that decides "is this a scam?" is plain code, and the AI agents only coordinate people. I'd rather have a rule I can read than a judgement I have to trust.

## What isn't done

- **Line**, the help line for the parent in their own WhatsApp or SMS chat, replies in Hindi, English or Hinglish and refuses scam-shaped requests ("install AnyDesk", "tell me the OTP") by raising the alarm. It needs Switch's WhatsApp or SMS adapter, which are still open pull requests, so it's optional here. Everything above runs on official Switch.
- **Hosting.** Ideally each family runs its own Switch. For parents who can't, someone would host it for them; that's a plan, not something built.
- **Gujarati and Marathi** come after Hindi, English and Hinglish.
- **It isn't proven.** The alarm rules are tested and the flow works in a live test. Whether families respond fast enough in real life is the open question, and I won't claim an answer I don't have.

## Try it

It takes about 20 minutes and needs no phone and no bank: one Telegram group and a simulated bank SMS show the whole flow.

```bash
git clone https://github.com/prx-my/parent-line && cd parent-line
cp family.example.toml family.toml
python3 -m unittest discover -s tests
```

The README has the full setup with Switch Console and Telegram.

If you've seen a parent through one of these calls, or you're the child who got the phone call, I'd like to hear what would have helped most.
