"""Check this machine can run Parent Line, before you set up Switch.

    python3 check.py

Written for any Python 3, so an old one is told what to install instead of
crashing. Needs no network, no Switch and no packages: Parent Line uses only
Python's standard library. It creates family.toml from the example if it is missing.
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SAMPLE_SMS = (
    "Dear Customer, A/C X1234 debited by Rs.480000.00 on date 06Nov26 by IMPS to RAKESH KUMAR "
    "Ref 431234567890. If not u? call 1800111109. -SBI"
)
failed = []


def ok(msg):
    print("  OK    " + msg)


def warn(msg):
    print("  NOTE  " + msg)


def fail(msg, fix):
    print("  FAIL  " + msg + "\n        Fix: " + fix)
    failed.append(msg)


def run(args):
    return subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)


print("Required for the offline check and the Telegram demo")

v = sys.version_info
if v < (3, 11):
    fail(
        "Python %d.%d.%d at %s; Parent Line needs 3.11 or newer (it reads its config with tomllib)" % (v[0], v[1], v[2], sys.executable),
        "install Python 3.12 (macOS: brew install python@3.12; Windows: py install 3.12 or python.org;"
        " any OS: uv python install 3.12) and run everything with that interpreter, e.g. python3.12 check.py",
    )
    print("\nStopped: the remaining checks need Python 3.11+.")
    sys.exit(1)
ok("Python %d.%d.%d (%s)" % (v[0], v[1], v[2], sys.executable))

missing = [p for p in ("bankwatch", "ridewatch", "callwatch", "clerk/xpost.py", "tests", "family.example.toml") if not os.path.exists(os.path.join(ROOT, p))]
if missing:
    fail("repo files missing: " + ", ".join(missing), "clone the whole repo: git clone https://github.com/prx-my/parent-line")
else:
    ok("repo files present")

family = os.path.join(ROOT, "family.toml")
if not os.path.exists(family):
    shutil.copyfile(os.path.join(ROOT, "family.example.toml"), family)
    warn("family.toml was missing, so it was copied from family.example.toml. Set room_id and [family] in it before the Switch steps")
try:
    import tomllib

    with open(family, "rb") as f:
        cfg = tomllib.load(f)
    ok("family.toml parses")
except Exception as e:
    cfg = {}
    fail("family.toml does not parse: %s" % e, "fix the line it names, or start again from family.example.toml")

r = run([sys.executable, "-m", "unittest", "discover", "-s", "tests"])
if r.returncode == 0:
    ok("unit tests: " + next((line for line in r.stdout.splitlines() if line.startswith("Ran ")), "passed"))
else:
    print(r.stdout)
    fail("unit tests failed (output above)", "run python3 -m unittest discover -s tests -v and read the first failure")

r = run([sys.executable, "-m", "bankwatch", "simulate", SAMPLE_SMS, "--at", "23:40", "--dry-run"])
if r.returncode == 0 and "4,80,000" in r.stdout:
    ok("bankwatch simulate --dry-run prints the scam alarm for the sample SMS")
else:
    print(r.stdout)
    fail("bankwatch simulate --dry-run did not print the alarm (output above)", "check family.toml's [rules], or compare with family.example.toml")

print("\nNeeded only for later steps (missing ones are fine for the offline check)")

if shutil.which("claude"):
    ok("Claude Code on PATH (the Guardian and the Clerk run on it, started by Switch Console)")
else:
    warn("Claude Code not on PATH: install it before the Telegram demo (https://docs.claude.com/claude-code), then set it up in Switch Console")

creds = os.path.join(ROOT, str(cfg.get("credentials") or "bank-watch/.switch/agents/bank-watch.json"))
if os.path.exists(creds):
    ok("Bank watch's Switch credentials exist; next: python3 -m bankwatch setup")
else:
    warn("no Bank watch credentials yet (%s): Switch Console writes them when you create the bank-watch agent (README, Run it, step 2)" % os.path.relpath(creds, ROOT))

for tool, why in (("cloudflared", "the missed-call SOS (step 6) and real bank SMS"), ("node", "only to build the website in web/")):
    if shutil.which(tool):
        ok("%s on PATH (%s)" % (tool, why))
    else:
        warn("%s not on PATH: needed for %s" % (tool, why))
if os.environ.get("TWILIO_AUTH_TOKEN"):
    ok("TWILIO_AUTH_TOKEN set (missed-call SOS)")

if failed:
    print("\n%d check(s) failed. Fix them before the Switch steps." % len(failed))
    sys.exit(1)
print("\nAll required checks passed. Next: README, Run it, step 1 (Switch server and Telegram bot).")
