import gsap from "gsap";
import { DrawSVGPlugin } from "gsap/DrawSVGPlugin";
import { MotionPathPlugin } from "gsap/MotionPathPlugin";
import { ScrambleTextPlugin } from "gsap/ScrambleTextPlugin";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { TextPlugin } from "gsap/TextPlugin";
import Lenis from "lenis";

type JobState = "idle" | "none" | "wait" | "done";
type Step = { clock: string; caption: string; jobs: [JobState, string][] };

const $ = <T extends Element = HTMLElement>(sel: string, root: ParentNode = document) => root.querySelector<T>(sel)!;
const $$ = <T extends Element = HTMLElement>(sel: string, root: ParentNode = document) => [...root.querySelectorAll<T>(sel)];

// With reduced motion the page stays as the HTML renders it: everything visible, nothing pinned or looping.
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) start();

function start() {
  gsap.registerPlugin(ScrollTrigger, DrawSVGPlugin, MotionPathPlugin, TextPlugin, ScrambleTextPlugin);

  const lenis = new Lenis({ lerp: 0.09 });
  lenis.on("scroll", ScrollTrigger.update);
  gsap.ticker.add((t) => lenis.raf(t * 1000));
  gsap.ticker.lagSmoothing(0);

  const nav = $("[data-nav]");
  lenis.on("scroll", ({ scroll, direction }: Lenis) => nav.classList.toggle("hide", direction === 1 && scroll > 240));
  $$<HTMLAnchorElement>('a[href^="#"]').forEach((a) =>
    a.addEventListener("click", (e) => {
      const target = document.querySelector<HTMLElement>(a.getAttribute("href")!);
      if (!target) return;
      e.preventDefault();
      lenis.scrollTo(target, { duration: 1.6 });
    }),
  );

  const mm = gsap.matchMedia();

  hero();
  why(mm);
  reveals();
  alarm(mm);
  room();
  ways();
  deadline();

  gsap.from(splitWords($("footer [data-split]")), {
    yPercent: 110, duration: 1.4, ease: "expo.out", stagger: 0.08,
    scrollTrigger: { trigger: "footer", start: "top 80%" },
  });

  document.fonts.ready.then(() => ScrollTrigger.refresh());
}

// A looping animation that runs only while its section is on screen.
function whileVisible(trigger: Element, tl: gsap.core.Animation) {
  tl.pause();
  ScrollTrigger.create({ trigger, start: "top bottom", end: "bottom top", onToggle: (self) => (self.isActive ? tl.play() : tl.pause()) });
  return tl;
}

// Hero: the headline rises, the SMS arrives, it travels down to Bank watch, the rules fire, and the alarm lands.
function hero() {
  const sms = $("[data-sms]");
  const smsText = sms.textContent!;
  sms.style.minHeight = `${sms.offsetHeight}px`;
  sms.textContent = "";
  const rules = $$("[data-rule]");
  const ruleText = rules.map((r) => r.textContent!);
  rules.forEach((r) => { r.style.minHeight = "1.6em"; r.textContent = ""; });

  const intro = gsap.timeline({ defaults: { ease: "expo.out" } })
    .from(splitWords($(".hero h1")), { yPercent: 115, duration: 1.3, stagger: 0.045 })
    .from("[data-hero-intro] > :not(h1), #run > *", { y: 24, opacity: 0, duration: 1, stagger: 0.1 }, "-=1")
    .from("[data-hero-sms] .meta-row", { opacity: 0, y: 12, duration: 0.6 }, "-=0.8")
    .to(sms, { text: { value: smsText }, duration: 1.4, ease: "none" }, "-=0.4")
    .fromTo("[data-via-path]", { scaleY: 0 }, { scaleY: 0.5, duration: 0.5, ease: "power2.in" })
    .from("[data-via-node]", { scale: 0, transformOrigin: "50% 50%", duration: 0.4, ease: "back.out(3)" }, "-=0.1")
    .from(".via-text p", { opacity: 0, x: -8, duration: 0.4 }, "<");
  rules.forEach((r, i) =>
    intro.to(r, { scrambleText: { text: ruleText[i], chars: "0123456789₹#", speed: 0.6 }, duration: 0.6, ease: "none" }, i ? "-=0.35" : ">"),
  );
  intro
    .to("[data-via-path]", { scaleY: 1, duration: 0.5, ease: "power2.out" })
    .from("[data-hero-alarm] > *", { y: 24, opacity: 0, duration: 0.9, stagger: 0.08 }, "-=0.1");

  // After the intro, one message at a time keeps travelling from the SMS through Bank watch to the alarm.
  const dot = $("[data-via-dot]");
  const node = $("[data-via-node]");
  const loop = gsap.timeline({ repeat: -1, repeatDelay: 1.4, delay: intro.duration() })
    .set(dot, { top: "0%", opacity: 1 })
    .to(dot, { top: "50%", duration: 0.7, ease: "power1.in" })
    .to(node, { scale: 1.35, transformOrigin: "50% 50%", duration: 0.15, yoyo: true, repeat: 1 })
    .to(dot, { top: "100%", duration: 0.7, ease: "power1.out" })
    .to(dot, { opacity: 0, duration: 0.2 });
  whileVisible($(".hero"), loop);
}

// Why: the statement lights up as it is read; the two lanes draw, then keep moving.
function why(mm: gsap.MatchMedia) {
  const statement = $("[data-words]");
  statement.innerHTML = statement.textContent!.trim().split(/\s+/).map((w) => `<span>${w}</span>`).join(" ");
  gsap.fromTo(statement.children, { opacity: 0.16 }, {
    opacity: 1, stagger: 0.1, ease: "none",
    scrollTrigger: { trigger: statement, start: "top 78%", end: "bottom 45%", scrub: true },
  });

  $$("[data-lane]").forEach((lane) => {
    const rule = $("[data-lane-rule]", lane);
    const nodes = $$("[data-lane-node]", lane);
    const pulse = $("[data-lane-pulse]", lane);
    mm.add({ wide: "(min-width: 901px)", narrow: "(max-width: 900px)" }, (ctx) => {
      const wide = ctx.conditions!.wide;
      gsap.timeline({ scrollTrigger: { trigger: lane, start: "top 80%", end: "top 40%", scrub: 0.6 } })
        .from(rule, { ...(wide ? { scaleX: 0 } : { scaleY: 0 }), ease: "none", duration: 1 })
        .from(nodes, { opacity: 0, y: 14, stagger: 0.25, duration: 0.4 }, 0);
      if (wide) {
        const end = nodes[nodes.length - 1];
        whileVisible(lane, gsap.timeline({ repeat: -1, repeatDelay: 0.8 })
          .fromTo(pulse, { x: 0, opacity: 0 }, { x: () => end.offsetLeft - 3, duration: 2, ease: "power1.inOut" })
          .to(pulse, { opacity: 1, duration: 0.2 }, 0)
          .to(pulse, { opacity: 0, duration: 0.2 }, 1.8));
      }
    });
  });

  // The bank's lane keeps losing money; the family's lane ends in a ringing call.
  const drops = $$("[data-drip] .drop");
  whileVisible($("[data-drip]"), gsap.timeline({ repeat: -1 })
    .fromTo(drops, { y: 0, opacity: 1 }, { y: 28, opacity: 0, duration: 1.1, ease: "power2.in", stagger: 0.45 }));
  const rings = $$("[data-rings] .ring");
  whileVisible($("[data-rings]"), gsap.timeline({ repeat: -1 })
    .fromTo(rings, { scale: 1, opacity: 0.9, transformOrigin: "50% 50%" }, { scale: 2.8, opacity: 0, duration: 1.6, ease: "power1.out", stagger: 0.5 }));

  $$("[data-count]").forEach((el) => {
    const end = Number(el.dataset.count);
    if (!end) return;
    const pre = el.dataset.prefix ?? "", suf = el.dataset.suffix ?? "";
    const o = { v: 0 };
    gsap.to(o, {
      v: end, duration: 2, ease: "power3.out",
      scrollTrigger: { trigger: el, start: "top 85%", once: true },
      onUpdate: () => { el.textContent = pre + Math.round(o.v).toLocaleString("en-IN") + suf; },
    });
  });
}

function reveals() {
  $$(".head").forEach((el) =>
    gsap.from(el.children, { y: 40, opacity: 0, duration: 1.2, ease: "expo.out", stagger: 0.12, scrollTrigger: { trigger: el, start: "top 85%" } }),
  );
  $$("[data-reveal], .note").forEach((el) =>
    gsap.from(el, { y: 40, opacity: 0, duration: 1.2, ease: "expo.out", scrollTrigger: { trigger: el, start: "top 88%" } }),
  );
  $$("[data-stagger]").forEach((el) =>
    gsap.from(el.children, { y: 30, opacity: 0, duration: 1, ease: "expo.out", stagger: 0.1, scrollTrigger: { trigger: el, start: "top 85%" } }),
  );
}

// The alarm is pinned on wide screens: scrolling moves the clock, the timeline, the jobs and the transcript one step at a time.
function alarm(mm: gsap.MatchMedia) {
  const sec = $("[data-alarm]");
  const steps: Step[] = JSON.parse(sec.dataset.steps!);
  const msgs = $$("[data-msg]", sec);
  const feed = $("[data-feed]", sec);
  const list = $("[data-feed-list]", sec);
  const clock = $("[data-clock]", sec);
  const cap = $("[data-cap]", sec);
  const jobs = $$("[data-job]", sec);
  const caseFile = $("[data-case]", sec);
  const ticks = $$("[data-rail-tick]", sec);
  const fill = $("[data-rail-fill]", sec);
  let current = -1;

  const render = (i: number) => {
    if (i === current) return;
    current = i;
    const s = steps[i];
    msgs.forEach((m, k) => { m.classList.toggle("on", k <= i); m.classList.toggle("now", k === i); });
    ticks.forEach((t, k) => { t.classList.toggle("past", k <= i); t.classList.toggle("now", k === i); });
    const span = $("span", clock);
    if (span.textContent !== s.clock) {
      span.textContent = s.clock;
      gsap.fromTo(span, { yPercent: 40, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 0.5, ease: "expo.out" });
    }
    clock.classList.toggle("closed", i === steps.length - 1);
    gsap.to(cap, { text: { value: s.caption }, duration: 0.5, ease: "none", overwrite: true });
    jobs.forEach((el, k) => { el.dataset.s = s.jobs[k][0]; $(".state", el).textContent = s.jobs[k][1]; });
    caseFile.classList.toggle("on", i >= 2);
    const last = msgs[i];
    const y = Math.min(0, feed.clientHeight - (last.offsetTop + last.offsetHeight) - 8);
    gsap.to(list, { y, duration: 0.8, ease: "expo.out", overwrite: true });
  };

  mm.add("(min-width: 960px) and (min-height: 700px)", () => {
    sec.classList.add("is-pinned");
    current = -1;
    render(0);
    const st = ScrollTrigger.create({
      trigger: sec, start: "top top", end: `+=${steps.length * 420}`, pin: true, anticipatePin: 1,
      onUpdate: (self) => {
        gsap.set(fill, { scaleX: self.progress });
        render(Math.min(steps.length - 1, Math.floor(self.progress * steps.length)));
      },
    });
    return () => {
      st.kill();
      sec.classList.remove("is-pinned");
      gsap.set(list, { clearProps: "transform" });
      msgs.forEach((m) => m.classList.remove("on", "now"));
    };
  });
  mm.add("(max-width: 959px), (max-height: 699px)", () => {
    msgs.forEach((m) => gsap.from(m, { y: 28, opacity: 0, duration: 1, ease: "expo.out", scrollTrigger: { trigger: m, start: "top 90%" } }));
  });
}

// The room: services post alarms in on the left; Switch delivers them to the people and agents on the
// right, whose replies come back. Each message travels its wire and then appears in the room's history.
type RoomLine = { from: string; who: string; text: string; alarm: boolean };

function room() {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const flow = $("[data-flow]");
  const svg = $<SVGSVGElement>("[data-wires]", flow);
  const box = $("[data-room-box]", flow);
  const log = $("[data-log]", flow);
  const nodes = $$("[data-node]", flow);
  const scenes: RoomLine[][] = JSON.parse(flow.dataset.scenes!);

  const wires = new Map<string, SVGPathElement>();
  const dots = new Map<string, SVGRectElement>();
  nodes.forEach((n) => {
    const path = document.createElementNS(SVG_NS, "path");
    if (n.classList.contains("optional")) path.classList.add("dash");
    const dot = document.createElementNS(SVG_NS, "rect");
    for (const [k, v] of Object.entries({ x: "-4", y: "-4", width: "8", height: "8", opacity: "0" })) dot.setAttribute(k, v);
    svg.append(path, dot);
    wires.set(n.dataset.node!, path);
    dots.set(n.dataset.node!, dot);
  });

  // Each wire runs from its node's port to the room's nearer edge, spread down that edge in the nodes' order.
  const layout = () => {
    const f = flow.getBoundingClientRect();
    const r = box.getBoundingClientRect();
    svg.setAttribute("viewBox", `0 0 ${f.width} ${f.height}`);
    for (const side of ["in", "out"]) {
      const group = nodes.filter((n) => n.dataset.side === side);
      group.forEach((n, i) => {
        const port = $("[data-port]", n).getBoundingClientRect();
        const x1 = (side === "in" ? port.right : port.left) - f.left;
        const y1 = port.top + port.height / 2 - f.top;
        const x2 = (side === "in" ? r.left : r.right) - f.left;
        const y2 = r.top - f.top + r.height * (0.28 + 0.44 * (group.length > 1 ? i / (group.length - 1) : 0.5));
        const dx = (x2 - x1) / 2;
        wires.get(n.dataset.node!)!.setAttribute("d", `M${x1} ${y1} C${x1 + dx} ${y1} ${x2 - dx} ${y2} ${x2} ${y2}`);
      });
    }
  };

  const push = (line: RoomLine) => {
    const li = document.createElement("li");
    if (line.alarm) li.className = "alarm";
    const who = document.createElement("b");
    who.textContent = line.who;
    const text = document.createElement("span");
    text.textContent = line.text;
    li.append(who, text);
    log.append(li);
    while (log.children.length > 4) log.firstElementChild!.remove();
    gsap.from(li, { y: 14, opacity: 0, duration: 0.5, ease: "expo.out" });
  };

  // A message travels between a node and the room: towards the room for an alarm or a reply, away from it for a delivery.
  const travel = (tl: gsap.core.Timeline, key: string, toRoom: boolean, alarm: boolean) => {
    const path = wires.get(key)!;
    const dot = dots.get(key)!;
    tl.call(() => { path.classList.add("lit"); dot.classList.toggle("alarm", alarm); })
      .set(dot, { opacity: 1 })
      .to(dot, { motionPath: { path, start: toRoom ? 0 : 1, end: toRoom ? 1 : 0 }, duration: 0.9, ease: "power1.inOut" })
      .set(dot, { opacity: 0 })
      .call(() => path.classList.remove("lit"));
  };

  layout();
  const tl = gsap.timeline({ repeat: -1 });
  scenes.forEach((scene) => {
    tl.call(() => log.replaceChildren());
    scene.forEach((line) => {
      if (line.alarm) travel(tl, line.from, true, true);
      else {
        travel(tl, line.from, false, false);
        travel(tl, line.from, true, false);
      }
      tl.call(() => push(line)).to({}, { duration: 0.7 });
    });
    tl.to({}, { duration: 2.4 });
  });
  whileVisible(flow, tl);

  const relayout = () => { layout(); tl.invalidate(); };
  ScrollTrigger.addEventListener("refreshInit", relayout);
  new ResizeObserver(relayout).observe(flow);

  // Pointing at a node lights up its wire.
  nodes.forEach((n) => {
    const path = wires.get(n.dataset.node!)!;
    const on = () => path.classList.add("lit");
    const off = () => path.classList.remove("lit");
    n.addEventListener("pointerenter", on);
    n.addEventListener("pointerleave", off);
    n.addEventListener("focus", on);
    n.addEventListener("blur", off);
  });

  gsap.timeline({ scrollTrigger: { trigger: flow, start: "top 78%" } })
    .from(box, { opacity: 0, y: 20, duration: 1, ease: "expo.out" })
    .from(nodes, { opacity: 0, y: 14, duration: 0.8, stagger: 0.06, ease: "expo.out" }, "-=0.7")
    .from(svg, { opacity: 0, duration: 0.8 }, "-=0.5");
}

function ways() {
  // Ride: the route draws as you scroll, then the ride keeps moving along it.
  const route = $("[data-route]");
  const path = $<SVGPathElement>("[data-route-path]");
  gsap.fromTo(path, { drawSVG: "0%" }, { drawSVG: "100%", ease: "none", scrollTrigger: { trigger: route, start: "top 85%", end: "top 45%", scrub: 0.6 } });
  whileVisible(route, gsap.to("[data-route-car]", {
    motionPath: { path, align: path, alignOrigin: [0.5, 0.5] }, duration: 5, ease: "none", repeat: -1, repeatDelay: 0.6,
  }));
  gsap.from("[data-tick]", { scaleX: 0, duration: 1, stagger: 0.5, ease: "power2.inOut", scrollTrigger: { trigger: "[data-tick]", start: "top 85%" } });

  // Missed call: it rings twice, Call watch rejects it, and the SOS appears in the family group.
  const call = $("[data-call]");
  const status = $("[data-call-status]");
  const post = $("[data-call-post]");
  const rings = $$("[data-call-ring]");
  whileVisible(call, gsap.timeline({ repeat: -1, repeatDelay: 1.6 })
    .set(status, { text: "Ringing" })
    .set("[data-call-cut]", { drawSVG: "0%", opacity: 1 })
    .set(post, { opacity: 0.25 })
    .fromTo(rings, { scale: 1, opacity: 0.9, transformOrigin: "50% 50%" }, { scale: 3.6, opacity: 0, duration: 1.3, ease: "power1.out", stagger: 0.35, repeat: 1 })
    .to("[data-call-cut]", { drawSVG: "100%", duration: 0.35, ease: "power2.out" })
    .to(status, { text: { value: "Rejected. Free." }, duration: 0.5, ease: "none" }, "<")
    .to(post, { opacity: 1, duration: 0.5 }, "+=0.3")
    .to({}, { duration: 2 }));
}

// The deadline: each working day hops to the next; Sunday is passed over and struck out.
function deadline() {
  const days = $$("[data-day]");
  const hops = $$("[data-hop]");
  gsap.set(hops, { drawSVG: "0%" });
  gsap.timeline({ scrollTrigger: { trigger: "[data-days]", start: "top 80%", end: "top 30%", scrub: 0.6 } })
    .from(days[0], { opacity: 0.1, y: 20, duration: 0.4 })
    .to(hops[0], { drawSVG: "100%", duration: 0.5 })
    .from(days[1], { opacity: 0.1, y: 20, duration: 0.4 })
    .from(days[2], { opacity: 0.1, y: 20, duration: 0.4 })
    .from("[data-strike]", { scaleX: 0, duration: 0.3 })
    .to(hops[1], { drawSVG: "100%", duration: 0.6 })
    .from(days[3], { opacity: 0.1, y: 20, duration: 0.4 })
    .to(hops[2], { drawSVG: "100%", duration: 0.5 })
    .from(days[4], { opacity: 0.1, y: 20, duration: 0.4 });
}

// Wrap each word in a mask so it can rise into view; keeps inner elements such as the soft first sentence.
function splitWords(el: HTMLElement) {
  const walk = (node: Node) => {
    [...node.childNodes].forEach((n) => {
      if (n.nodeType === Node.TEXT_NODE) {
        const frag = document.createDocumentFragment();
        n.textContent!.split(/(\s+)/).forEach((part) => {
          if (!part) return;
          if (/^\s+$/.test(part)) return frag.appendChild(document.createTextNode(" "));
          const w = document.createElement("span");
          w.className = "w";
          const inner = document.createElement("span");
          inner.textContent = part;
          w.appendChild(inner);
          frag.appendChild(w);
        });
        n.replaceWith(frag);
      } else if (n.nodeType === Node.ELEMENT_NODE) walk(n);
    });
  };
  walk(el);
  return $$(".w > span", el);
}
