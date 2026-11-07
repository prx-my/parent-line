// The page's copy that repeats in a pattern. Message text is the agents' own layouts from
// guardian/family-room-instructions.md and guardian/line-instructions.md, without the emoji they add for Telegram.

export const repo = "https://github.com/prx-my/parent-line";

export type JobState = "idle" | "none" | "wait" | "done";

export type AlarmStep = {
  time: string;
  clock: string;
  caption: string;
  from: string;
  kind: string;
  html: string;
  jobs: [JobState, string][];
};

const nobody: [JobState, string][] = [["none", "nobody yet"], ["none", "nobody yet"], ["none", "nobody yet"]];

export const jobs = ["Call Mom", "Report on 1930", "Call SBI"];

// Labels on the alarm's timeline, one per step below.
export const alarmMarks = ["0 s", "5 s", "28 s", "3 min", "reply", "+2 s", "later"];

export const alarmSteps: AlarmStep[] = [
  {
    time: "0 s", clock: "0 s", caption: "Bank watch posts the alarm", from: "Bank watch", kind: "service, no AI",
    html: `<p><span class="alarm">Bank alarm: Mom, 23:40.</span> ₹4,80,000 left the account to RAKESH KUMAR. @guardian over to you.</p>`,
    jobs: [["idle", "waiting"], ["idle", "waiting"], ["idle", "waiting"]],
  },
  {
    time: "5 s", clock: "5 s", caption: "The Guardian splits it into three jobs", from: "Guardian", kind: "AI agent",
    html: `<p><b>₹4,80,000 left Mom's SBI account at 23:40</b><br>To RAKESH KUMAR · ref 431234567890<br>Looks like a digital-arrest scam: big amount, new payee, late at night.</p>
<ol><li><b>Call Mom now</b>, normal call, not WhatsApp</li><li><b>Report</b> on 1930 or cybercrime.gov.in</li><li><b>Call SBI</b> on 1800 111 109 (from their SMS)</li></ol>
<p>Reply @guardian with the number of the job you're taking.</p>`,
    jobs: nobody,
  },
  {
    time: "28 s", clock: "28 s", caption: "The Clerk opens the case file", from: "Clerk", kind: "AI agent",
    html: `<p>Case file opened: <code>case-2026-11-06-sbi-480000</code></p>`,
    jobs: nobody,
  },
  {
    time: "3 min", clock: "3 min", caption: "Nobody has a job yet. The Guardian chases.", from: "Guardian", kind: "AI agent",
    html: `<p><span class="mono">1  nobody yet<br>2  nobody yet<br>3  nobody yet</span>Riya, Arjun: call Mom first.</p>`,
    jobs: nobody,
  },
  {
    time: "", clock: "3 min", caption: "Riya takes job 1", from: "Riya", kind: "family",
    html: `<p>@guardian I'll take 1</p>`,
    jobs: nobody,
  },
  {
    time: "+2 s", clock: "+2 s", caption: "The Guardian updates the jobs", from: "Guardian", kind: "AI agent",
    html: `<p><span class="mono">1  Riya calling Mom<br>2  nobody yet<br>3  nobody yet</span>Arjun, can you take 3? @clerk is writing the complaint.</p>`,
    jobs: [["wait", "Riya calling"], ["none", "nobody yet"], ["none", "nobody yet"]],
  },
  {
    time: "later", clock: "Later", caption: "Mom is safe. The alarm is closed.", from: "Guardian", kind: "AI agent",
    html: `<p><b>Alarm closed: Mom is safe</b><br>Done: Riya reached Mom · SBI blocked transfers · complaint filed<br>Still open: complaint number from 1930</p>`,
    jobs: [["done", "Riya reached Mom"], ["done", "complaint filed"], ["done", "SBI blocked transfers"]],
  },
];

// flow: "alarm" seats only post into the room (alarms, drawn red); "talk" seats read and post.
export type Seat = { x: number; y: number; name: string; kind: string; call: string; flow: "alarm" | "talk" };

// Positions are percentages of a square diagram, evenly spaced on a circle around the room.
export const seats: Seat[] = [
  { x: 50, y: 12, name: "The family", kind: "people", call: "Telegram bridge", flow: "talk" },
  { x: 79.7, y: 26.3, name: "Guardian", kind: "AI agent", call: "the room's instructions", flow: "talk" },
  { x: 87, y: 58.5, name: "Clerk", kind: "AI agent", call: "create_room_document", flow: "talk" },
  { x: 66.5, y: 84.2, name: "Line", kind: "AI agent, optional", call: "connect_to_room", flow: "alarm" },
  { x: 33.5, y: 84.2, name: "Call watch", kind: "service, no AI", call: "Twilio in, agent API out", flow: "alarm" },
  { x: 13, y: 58.5, name: "Ride watch", kind: "service, no AI", call: "GET /agents/{id}/events", flow: "alarm" },
  { x: 20.3, y: 26.3, name: "Bank watch", kind: "service, no AI", call: "POST /agents/{id}/message", flow: "alarm" },
];
