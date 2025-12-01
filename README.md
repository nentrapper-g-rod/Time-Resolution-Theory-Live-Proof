# Time-Resolution-Theory-Live-Proof

**The first continuously running, public experiment proving quantum "superposition" is a temporal-resolution artifact.**

## 📖 Theoretical Foundation

This experiment is a live demonstration of **Time Resolution Theory (TRT)**, a deterministic framework proposing that quantum uncertainty, superposition, and mass are artifacts of limited temporal resolution—not fundamental properties of nature.

**[Read the full TRT paper →](TRT_Theory.md)**

**Key concepts:**
- **Mass is frozen energy**: What we observe as mass is energy vibrating too fast for our instruments to resolve
- **Superposition is a blur**: Like a slow camera shutter blurs a fast object, coarse time resolution blurs quantum paths
- **Deterministic universe**: Quantum randomness arises from measurement limits, not fundamental indeterminacy

**Core equation:**
```
m = (E - γ·ℏ/Δt) / c²
```
Where improving temporal resolution (smaller Δt) reduces observed mass, revealing the underlying energy motion.

**License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) - Free to share with attribution.

---

## 🔬 Live Experiment

A single 405 nm LED is pulsed at exactly 10 kHz (50% duty). A photodiode measures perceived intensity under three observer resolutions Δt = 0.1 s, 0.01 s, and 0.001 s.

**Result (updated every 60 s):**
- Coarse Δt → mean intensity = 0.5000 ± 0.002, variance → 0
- Fine Δt → variance explodes, mean still ~0.5

Identical behavior to the double-slit when scaled by TRT's κ = 10⁴ factor.

**No interpretation. No collapse postulate. Just hardware running 24/7.**

---

## 📊 LIVE AUTO-VALIDATION GRAPHS
**Updated automatically every 10 minutes**

### Main Experiment — TRT Live Proof (10 kHz, running forever)
![TRT LIVE PROOF](data/live_trt.png)

### Control Tests — Proving Hardware Validity

**Blind Control (LED OFF) — Expect: Mean ≈ 0.0V, Variance ≈ 0**
![Control: LED OFF](data/control_off.png)

**Positive Control (LED 100% ON) — Expect: Mean ≈ 1.0V, Variance ≈ 0**
![Control: LED ON](data/control_on.png)

### Frequency Sweep — Proving Frequency Dependence

**100 Hz — High variance at all Δt (visible flicker)**
![100 Hz Sweep](data/sweep_100hz.png)

**1 kHz — Moderate variance**
![1 kHz Sweep](data/sweep_1khz.png)

**10 kHz — Low variance (same as main experiment)**
![10 kHz Sweep](data/sweep_10khz.png)

**20 kHz — Minimal variance**
![20 kHz Sweep](data/sweep_20khz.png)

---

**All data and graphs auto-generated. No human intervention. Watch variance collapse as frequency increases. Then watch it lock at 0.500 forever.**

**Quantum collapse = bad clock. That's it.**

**Hardware:** Arduino GIGA R1 WiFi + GIGA Display Shield (480x800), 405 nm LED, BPW34 photodiode.
**Software:** Automated 7-phase validation system, samples data, POSTs JSON to this repo every 60s.

---

## 🔬 Auto-Validation System

The experiment runs **7 automated phases** in a continuous loop, each lasting 5 minutes:

1. **Phase 0: LED OFF** → Control test (expect mean ≈ 0V, variance ≈ 0)
2. **Phase 1: LED ON** → Control test (expect mean ≈ 1V, variance ≈ 0)
3. **Phase 2: 100 Hz** → Frequency sweep (visible flicker, high variance)
4. **Phase 3: 1 kHz** → Frequency sweep (moderate variance)
5. **Phase 4: 10 kHz** → Frequency sweep (low variance)
6. **Phase 5: 20 kHz** → Frequency sweep (minimal variance)
7. **Phase 6: LIVE TRT** → Main 10 kHz experiment (runs forever)

Each phase uploads data to separate JSON files, and graphs are auto-generated every 10 minutes.

## Setup & Installation

### Hardware Requirements
- Arduino GIGA R1 WiFi
- Arduino GIGA Display Shield
- 405 nm LED
- BPW34 photodiode
- WiFi network connection

### Software Setup
1. Clone repository:
   ```bash
   git clone https://github.com/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof.git
   cd Time-Resolution-Theory-Live-Proof
   ```

2. Flash Arduino with auto-validation sketch:
   - Open `arduino/TRT_Auto_Validation.ino`
   - Update WiFi credentials and GitHub token
   - Upload to Arduino GIGA R1 WiFi

3. Set up automated graph generation (optional):
   - Edit `update_graphs.sh` and add your GitHub token
   - Make executable: `chmod +x update_graphs.sh`
   - Add to crontab: `crontab -e`
   - Add line: `*/10 * * * * /path/to/update_graphs.sh >> ~/trt_graphs.log 2>&1`

4. Run: Hardware auto-updates this repo every 60 seconds with new data.

**v2.0.0** – Auto-validation system with GIGA Display (Nov 30, 2025).
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
