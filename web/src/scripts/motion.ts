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
    .fromTo("[data-via-path]", { drawSVG: "0%" }, { drawSVG: "50%", duration: 0.5, ease: "power2.in" })
    .from("[data-via-node]", { scale: 0, transformOrigin: "50% 50%", duration: 0.4, ease: "back.out(3)" }, "-=0.1")
    .from(".via-text p", { opacity: 0, x: -8, duration: 0.4 }, "<");
  rules.forEach((r, i) =>
    intro.to(r, { scrambleText: { text: ruleText[i], chars: "0123456789₹#", speed: 0.6 }, duration: 0.6, ease: "none" }, i ? "-=0.35" : ">"),
  );
  intro
    .to("[data-via-path]", { drawSVG: "100%", duration: 0.5, ease: "power2.out" })
    .from("[data-hero-alarm] > *", { y: 24, opacity: 0, duration: 0.9, stagger: 0.08 }, "-=0.1");

  // After the intro, one message at a time keeps travelling from the SMS through Bank watch to the alarm.
  const dot = $("[data-via-dot]");
  const node = $("[data-via-node]");
  const loop = gsap.timeline({ repeat: -1, repeatDelay: 1.4, delay: intro.duration() })
    .set(dot, { attr: { cy: 0 }, opacity: 1 })
    .to(dot, { attr: { cy: 60 }, duration: 0.7, ease: "power1.in" })
    .to(node, { scale: 1.35, transformOrigin: "50% 50%", duration: 0.15, yoyo: true, repeat: 1 })
    .to(dot, { attr: { cy: 120 }, duration: 0.7, ease: "power1.out" })
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

// The room: hairlines run from the hub to each seat, then messages keep moving along them.
// Alarms travel into the room in red; the people and agents who talk get messages back out in ink.
function room() {
  const map = $("[data-room]");
  const hub = $("[data-hub]", map);
  const seats = $$("[data-seat]", map);
  const rows = $$("[data-row]");
  const links = seats.map((seat) => {
    const link = document.createElement("span");
    link.className = "link";
    link.setAttribute("aria-hidden", "true");
    const line = document.createElement("i");
    const packet = document.createElement("b");
    if (seat.dataset.flow === "alarm") packet.className = "in";
    link.append(line, packet);
    map.prepend(link);
    return link;
  });
  const layout = () => {
    const { width, height } = map.getBoundingClientRect();
    seats.forEach((s, i) => {
      const dx = (parseFloat(s.style.getPropertyValue("--x")) / 100 - 0.5) * width;
      const dy = (parseFloat(s.style.getPropertyValue("--y")) / 100 - 0.5) * height;
      links[i].style.width = `${Math.hypot(dx, dy)}px`;
      links[i].style.transform = `rotate(${Math.atan2(dy, dx)}rad)`;
    });
  };
  layout();
  ScrollTrigger.addEventListener("refreshInit", layout);

  // Pointing at a row in the list lights up that participant's line in the diagram, and the other way round.
  const highlight = (i: number | null) => {
    rows.forEach((r, k) => r.classList.toggle("active", k === i));
    seats.forEach((s, k) => s.classList.toggle("dim", i !== null && k !== i));
    links.forEach((l, k) => { l.classList.toggle("active", k === i); l.classList.toggle("dim", i !== null && k !== i); });
  };
  [...rows, ...seats].forEach((el) => {
    const i = Number(el.dataset.row ?? el.dataset.seat);
    el.addEventListener("pointerenter", () => highlight(i));
    el.addEventListener("pointerleave", () => highlight(null));
    el.addEventListener("focus", () => highlight(i));
    el.addEventListener("blur", () => highlight(null));
  });

  gsap.timeline({ scrollTrigger: { trigger: map, start: "top 78%" } })
    .from(hub, { opacity: 0, duration: 1, ease: "expo.out" })
    .from(links.map((l) => l.firstChild), { scaleX: 0, duration: 0.9, stagger: 0.07, ease: "power3.inOut" }, "-=0.7")
    .from(seats, { opacity: 0, duration: 0.8, stagger: 0.07, ease: "power2.out" }, "-=0.7");

  const css = getComputedStyle(document.documentElement);
  const stamp = css.getPropertyValue("--stamp").trim(), ink = css.getPropertyValue("--ink").trim();
  const traffic = gsap.timeline({ repeat: -1 });
  links.forEach((link, i) => {
    const packet = link.lastChild as HTMLElement;
    const inbound = packet.classList.contains("in");
    traffic
      .fromTo(packet, { left: inbound ? "100%" : "0%" }, { left: inbound ? "0%" : "100%", duration: 1.3, ease: "power1.inOut" }, i * 0.55)
      .fromTo(packet, { opacity: 0 }, { opacity: 1, duration: 0.15 }, i * 0.55)
      .to(packet, { opacity: 0, duration: 0.15 }, i * 0.55 + 1.15)
      .to(hub, { borderColor: inbound ? stamp : ink, duration: 0.15, yoyo: true, repeat: 1 }, i * 0.55 + (inbound ? 1.2 : 0));
  });
  whileVisible(map, traffic);
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
