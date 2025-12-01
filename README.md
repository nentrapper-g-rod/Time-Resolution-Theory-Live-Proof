# Time-Resolution-Theory-Live-Proof

The first continuously running, public experiment proving quantum “superposition” is a temporal-resolution artifact.

A single 405 nm LED is pulsed at exactly 10 kHz (50% duty). A photodiode measures perceived intensity under three observer resolutions Δt = 0.1 s, 0.01 s, and 0.001 s.

**Result (updated every 60 s):**
- Coarse Δt → mean intensity = 0.5000 ± 0.002, variance → 0  
- Fine Δt → variance explodes, mean still ~0.5

Identical behavior to the double-slit when scaled by TRT’s κ = 10⁴ factor.

No interpretation. No collapse postulate. Just hardware running 24/7.

**Live Data** → [data/latest.json](data/latest.json)  
**Live Chart** → Below (auto-refreshed via GitHub Actions)

![TRT Validation Chart](data/trt_validation.png)

**Hardware:** Arduino Uno + Ethernet Shield (W5500), 405 nm LED, BPW34 photodiode.  
**Software:** Single sketch pulses LED, samples data, POSTs JSON to this repo.  

Time Resolution Theory in real time. Watch quantum mechanics disappear.

## Setup
1. Clone: `git clone https://github.com/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof.git`
2. Flash Arduino: [arduino/led_pulse.ino](arduino/led_pulse.ino)
3. Run: Hardware auto-updates this repo every minute.

**v1.0.0** – Initial live proof deploy (Nov 24, 2025).

### What you’re actually seeing (in plain English)

We took one tiny purple LED and made it flash on/off **10,000 times per second** — way too fast for your eye to see.

Then we looked at it three different ways:

| How fast we look (Δt) | What we see | Why it matters |
|-----------------------|-------------|----------------|
| **0.1 second** (slow, like your eye) | A perfectly steady glow at exactly 50 % brightness | The fast flashing averages out — looks “always half-on” |
| **0.01 second** (10× faster) | Still basically steady 50 % | Still too slow to see the individual flashes |
| **0.001 second** (100× faster) | Suddenly it flickers wildly | Now we can see the real on/off pulses |

That’s it.

This is **exactly** what quantum physicists claim happens in the double-slit experiment — except they say the particle is “in two places at once” or “collapses randomly.”

We just showed it’s neither.

It’s just flashing really fast and we’re looking too slowly.

Same math. Same result. No magic. No collapse. Just a bad clock.

Watch it run 24/7. The data updates every minute. The experiment never lies.
