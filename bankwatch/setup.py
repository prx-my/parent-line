"""`python -m bankwatch setup`: check the family room and set the Guardian's instructions.

It runs as the Bank watch agent, which is already in the family room, so nobody
has to sign in to the Switch admin API or paste instructions by hand.
"""

from __future__ import annotations

from pathlib import Path

from bankwatch.config import Config, ConfigError
from bankwatch.switch import SwitchAgent, SwitchPostError

TEMPLATE = Path(__file__).resolve().parent.parent / "guardian" / "family-room-instructions.md"
DETAILS_HEADING = "## Family details"


def family_room_instructions(config: Config, template: Path = TEMPLATE) -> str:
    """The Guardian's instructions: the template below its `---` line, with the
    family details filled in from family.toml."""
    family = config.family
    if family is None:
        raise ConfigError("[family] is missing from family.toml: copy it from family.example.toml and fill it in")
    text = template.read_text()
    head, sep, body = text.partition("\n---\n")
    if not sep or DETAILS_HEADING not in body:
        raise ConfigError(f"{template} has no '---' line or no '{DETAILS_HEADING}' section; did its layout change?")
    body = body[: body.index(DETAILS_HEADING)]
    details = [
        DETAILS_HEADING,
        "",
        f"- Parent: {config.parent_name}",
        f"- Parent's phone: {family.parent_phone}",
        f"- Family in this group: {', '.join(family.members)}",
        f"- Backup contact near the parent: {family.backup_contact}",
        f"- Parent's bank(s): {', '.join(family.banks)}",
    ]
    return body.strip() + "\n\n" + "\n".join(details) + "\n"


def run(config: Config, agent: SwitchAgent | None, *, dry_run: bool) -> int:
    """With no agent (a dry run) the instructions are printed, not set."""
    instructions = family_room_instructions(config)
    if dry_run or agent is None:
        print(instructions)
        return 0

    try:
        room = agent.op("get_room_detail", {"room_id": config.room_id})
    except SwitchPostError as exc:
        raise SwitchPostError(
            f"{exc}\nIs Bank watch in the family group? In the Telegram group send: !invite-agent @bank-watch"
        ) from exc
    where = f" on {room['bridge_display_name']}" if room.get("bridge_display_name") else ""
    print(f"✓ Bank watch can reach the family room: {room.get('name')}{where}")

    present = set(room.get("agent_names", [])) | set((room.get("aliases") or {}).values())
    missing = []
    for agent_name in dict.fromkeys([config.guardian, config.clerk]):
        if agent_name.lstrip("@") in present:
            print(f"✓ {agent_name} is in the room")
        else:
            missing.append(agent_name)
            print(f"✗ {agent_name} isn't in the room. In the Telegram group send: !invite-agent {agent_name}")

    agent.op("update_room", {"room_id": config.room_id, "instructions": instructions})
    print(f"✓ Set the Guardian's instructions ({len(instructions):,} characters) with the family details")

    if missing:
        return 1
    print(
        "\nReady. Try an alarm:\n"
        '  python3 -m bankwatch simulate "Dear Customer, A/C X1234 debited by Rs.480000.00 on date 06Nov26 '
        'by IMPS to RAKESH KUMAR Ref 431234567890. If not u? call 1800111109. -SBI" --at 23:40'
    )
    return 0
