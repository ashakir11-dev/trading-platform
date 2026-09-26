# Follow-Up: isolation mode

The user asked for a follow-up of one position outside the regular tick, usually to
force a full re-review now. Run the tripwire check, then **always** run the full
re-review, whatever the cooldown and interval say. Report alerts as usual; the
middleware agent decides whether they count as delivered.
