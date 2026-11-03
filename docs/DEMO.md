# Sprint 1 demo video

[`docs/demo/sprint1-demo.mp4`](demo/sprint1-demo.mp4), 75 seconds, 1280 by 720, with captions and no sound.

## What it shows, in order

1. **Staff sign in.** The menu shows only the screens the staff role may use.
2. **Inventory console.** Available units by blood group and component, counted live.
3. **Donor search.** Deferred donors have Start collection struck through, with the reason and review date. An eligible donor can start a collection.
4. **Record a donation.** Volume and bag lot, saved with Alt+S. The unit is created Quarantined.
5. **Unit label.** A Code 128 barcode, the unit ID and blood group, and no donor details.
6. **Screening results.** Four of five tests recorded, release refused with "Missing results: Malaria". Then the fifth is recorded and the unit is released.
7. **Stock count** goes up straight away.
8. **A donor signs in.** They see only their own eligibility and next date, and are refused the staff inventory screen.

This is Sprint 1: stories US-01 to US-05, US-07 to US-11 and US-13.

## How it was made

It was recorded from the app itself in a headless browser, driven by a script, **not by capturing a desktop**. That is why it contains only the seeded demo data and nothing from anyone's screen. To make it again:

```bash
cd src && python manage.py migrate && python manage.py seed_demo --password 'Demo#Pass2026x'
python manage.py runserver 8766 --noreload          # leave running
cd .. && npm install puppeteer-core
CHROME=/path/to/chrome-headless-shell OUT=frames node tools/demo/record_demo.js
pip install imageio imageio-ffmpeg pillow numpy
python tools/demo/encode_video.py frames docs/demo/sprint1-demo.mp4
```

The password above is the demo-only password for the seed data. It is not used anywhere real.
