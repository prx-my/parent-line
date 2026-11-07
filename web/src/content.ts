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

export type Seat = { x: number; y: number; name: string; kind: string; what: string; call: string };

// Positions are percentages of the diagram, on an ellipse around the room.
export const seats: Seat[] = [
  { x: 50, y: 9, name: "The family", kind: "people", what: "Take the jobs: call Mom, report, call the bank.", call: "Telegram bridge" },
  { x: 83, y: 22, name: "Guardian", kind: "AI agent", what: "Hands out the jobs, chases them, closes the alarm.", call: "the room's instructions" },
  { x: 88, y: 62, name: "Clerk", kind: "AI agent", what: "Case file, complaints, the bank's deadline, public posts.", call: "create_room_document" },
  { x: 67, y: 91, name: "Line", kind: "AI agent, optional", what: "The parent's help line on WhatsApp or SMS.", call: "connect_to_room" },
  { x: 33, y: 91, name: "Call watch", kind: "service, no AI", what: "Turns the parent's missed call into an SOS.", call: "Twilio in, agent API out" },
  { x: 12, y: 62, name: "Ride watch", kind: "service, no AI", what: "A check-in timer for a ride alone at night.", call: "GET /agents/{id}/events" },
  { x: 17, y: 22, name: "Bank watch", kind: "service, no AI", what: "Reads bank SMS and posts only alarms.", call: "POST /agents/{id}/message" },
];
