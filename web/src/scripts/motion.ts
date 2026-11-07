import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";

type JobState = "idle" | "none" | "wait" | "done";
type Step = { clock: string; caption: string; jobs: [JobState, string][] };

const $ = <T extends Element = HTMLElement>(sel: string, root: ParentNode = document) => root.querySelector<T>(sel)!;
const $$ = <T extends Element = HTMLElement>(sel: string, root: ParentNode = document) => [...root.querySelectorAll<T>(sel)];

// With reduced motion the page stays as the HTML renders it: everything visible, nothing pinned.
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) start();

function start() {
  gsap.registerPlugin(ScrollTrigger);

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

  // Hero: the headline rises word by word, then the SMS travels down the line and becomes the alarm
  gsap.timeline({ defaults: { ease: "expo.out" } })
    .from(splitWords($(".hero h1")), { yPercent: 115, duration: 1.3, stagger: 0.045 })
    .from("[data-hero-intro] > *", { y: 24, opacity: 0, duration: 1, stagger: 0.1 }, "-=1")
    .from("[data-hero-sms]", { y: 28, opacity: 0, duration: 1 }, "-=0.8")
    .from("[data-hero-line]", { scaleY: 0, duration: 0.8, ease: "power2.inOut" }, "-=0.5")
    .from("[data-hero-rules] p, [data-hero-rules] li", { opacity: 0, x: -8, duration: 0.5, stagger: 0.08, ease: "power2.out" }, "-=0.3")
    .from("[data-hero-alarm]", { y: 32, opacity: 0, duration: 1.1 }, "-=0.1");

  // The statement lights up word by word as it is read
  const statement = $("[data-words]");
  statement.innerHTML = statement.textContent!.trim().split(/\s+/).map((w) => `<span>${w}</span>`).join(" ");
  gsap.fromTo(statement.children, { opacity: 0.16 }, {
    opacity: 1, stagger: 0.1, ease: "none",
    scrollTrigger: { trigger: statement, start: "top 78%", end: "bottom 42%", scrub: true },
  });

  // The two lanes draw left to right (top to bottom on phones)
  $$("[data-lane]").forEach((lane) => {
    mm.add({ wide: "(min-width: 861px)", narrow: "(max-width: 860px)" }, (ctx) => {
      const draw = ctx.conditions!.wide ? { scaleX: 0 } : { scaleY: 0 };
      gsap.timeline({ scrollTrigger: { trigger: lane, start: "top 80%", end: "top 40%", scrub: 0.6 } })
        .from($("[data-lane-rule]", lane), { ...draw, ease: "none", duration: 1 })
        .from($$("[data-lane-node]", lane), { opacity: 0, y: 14, stagger: 0.25, duration: 0.4 }, 0);
    });
  });

  // Counters
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

  // Reveals
  $$(".head, [data-reveal], .note").forEach((el) =>
    gsap.from(el, { y: 44, opacity: 0, duration: 1.2, ease: "expo.out", scrollTrigger: { trigger: el, start: "top 88%" } }),
  );
  $$("[data-stagger]").forEach((el) =>
    gsap.from(el.children, { y: 30, opacity: 0, duration: 1, ease: "expo.out", stagger: 0.1, scrollTrigger: { trigger: el, start: "top 85%" } }),
  );

  alarm(mm);
  room(mm);

  // Ride watch: the three windows fill in order
  gsap.from("[data-tick]", { scaleX: 0, duration: 1, stagger: 0.5, ease: "power2.inOut", scrollTrigger: { trigger: "[data-tick]", start: "top 82%" } });

  // The deadline: the days count in, Sunday is struck out
  gsap.timeline({ scrollTrigger: { trigger: "[data-days]", start: "top 80%", end: "top 35%", scrub: 0.6 } })
    .from("[data-day]", { opacity: 0.1, y: 24, stagger: 0.3, duration: 0.5 })
    .from("[data-strike]", { scaleX: 0, duration: 0.4 }, 0.8);

  // Footer wordmark
  gsap.from(splitWords($("footer [data-split]")), {
    yPercent: 110, duration: 1.4, ease: "expo.out", stagger: 0.08,
    scrollTrigger: { trigger: "footer", start: "top 80%" },
  });

  document.fonts.ready.then(() => ScrollTrigger.refresh());
}

// The alarm is pinned on wide screens: scrolling moves the clock, the jobs and the transcript one step at a time.
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
  let current = -1;

  const render = (i: number) => {
    if (i === current) return;
    current = i;
    const s = steps[i];
    msgs.forEach((m, k) => { m.classList.toggle("on", k <= i); m.classList.toggle("now", k === i); });
    const span = $("span", clock);
    if (span.textContent !== s.clock) {
      span.textContent = s.clock;
      gsap.fromTo(span, { yPercent: 40, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 0.5, ease: "expo.out" });
    }
    clock.classList.toggle("closed", i === steps.length - 1);
    cap.textContent = s.caption;
    jobs.forEach((el, k) => { el.dataset.s = s.jobs[k][0]; $(".state", el).textContent = s.jobs[k][1]; });
    caseFile.classList.toggle("on", i >= 2);
    const last = msgs[i];
    const y = Math.min(0, feed.clientHeight - (last.offsetTop + last.offsetHeight) - 8);
    gsap.to(list, { y, duration: 0.8, ease: "expo.out", overwrite: true });
  };

  mm.add("(min-width: 960px) and (min-height: 640px)", () => {
    sec.classList.add("is-pinned");
    current = -1;
    render(0);
    const st = ScrollTrigger.create({
      trigger: sec, start: "top top", end: `+=${steps.length * 420}`, pin: true, anticipatePin: 1,
      onUpdate: (self) => render(Math.min(steps.length - 1, Math.floor(self.progress * steps.length))),
    });
    return () => {
      st.kill();
      sec.classList.remove("is-pinned");
      gsap.set(list, { clearProps: "transform" });
      msgs.forEach((m) => m.classList.remove("on", "now"));
    };
  });
  mm.add("(max-width: 959px), (max-height: 639px)", () => {
    msgs.forEach((m) => gsap.from(m, { y: 28, opacity: 0, duration: 1, ease: "expo.out", scrollTrigger: { trigger: m, start: "top 90%" } }));
  });
}

// The room: hairlines run from the hub to each seat, then the seats arrive
function room(mm: gsap.MatchMedia) {
  const map = $("[data-room]");
  const hub = $("[data-hub]", map);
  const seats = $$("[data-seat]", map);
  const links = seats.map(() => {
    const link = document.createElement("span");
    link.className = "link";
    link.setAttribute("aria-hidden", "true");
    link.appendChild(document.createElement("i"));
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

  mm.add("(min-width: 1061px)", () => {
    gsap.timeline({ scrollTrigger: { trigger: map, start: "top 72%" } })
      .from(hub, { scale: 0.8, opacity: 0, duration: 1, ease: "expo.out" })
      .from(links.map((l) => l.firstChild), { scaleX: 0, duration: 0.9, stagger: 0.07, ease: "power3.inOut" }, "-=0.6")
      .from(seats, { opacity: 0, y: 20, duration: 0.9, stagger: 0.07, ease: "expo.out" }, "-=0.8");
  });
  mm.add("(max-width: 1060px)", () => {
    gsap.from([hub, ...seats], { opacity: 0, y: 24, duration: 0.9, stagger: 0.06, ease: "expo.out", scrollTrigger: { trigger: map, start: "top 85%" } });
  });
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
