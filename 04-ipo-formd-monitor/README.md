# 04 · IPO / Form D monitor

Track capital formation: **new S-1 IPO registrations** and **Form D private
placements** in a sector.

## What it does

- **S-1s** — `GET /v1/filings?form_type=S-1&filed_from=...` lists companies that
  just filed to go public.
- **Form D** — `GET /v1/raises` lists private placements, scoped by `industry`,
  `state`, `fund_type`, `is_pooled_fund`, and `min_amount`.

## Run

```bash
export CLOUS_API_KEY=clous_live_...

python ipo_formd_monitor.py                  # 30-day S-1s + CA venture raises >= $1M
python ipo_formd_monitor.py 14 "Technology"  # 14-day lookback, Technology-sector raises

./ipo_formd_monitor.sh                        # curl + jq variant
./ipo_formd_monitor.sh 14 Technology
```

## Going real-time

This recipe *polls*. To get **pushed** the moment a new S-1 or Form D lands,
create a monitor on the event types `sec.s1.new_registration` /
`sec.formd.new_offering` and attach a webhook — see
[07 · Monitor + webhook](../07-monitor-webhook). You can also tail the same
signals from the [events feed](https://docs.clous.ai/api/events):
`GET /v1/events?event_type=sec.formd.new_offering`.

Endpoints: [/v1/filings](https://docs.clous.ai/api/filings) ·
[/v1/raises](https://docs.clous.ai/api/raises).
