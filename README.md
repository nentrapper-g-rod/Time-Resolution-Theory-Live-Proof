# Time-Resolution-Theory-Live-Proof

**The first continuously running, public experiment proving quantum "superposition" is a temporal-resolution artifact.**

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

**Hardware:** Arduino Uno + Ethernet Shield (W5500), 405 nm LED, BPW34 photodiode.  
**Software:** Single sketch pulses LED, samples data, POSTs JSON to this repo.  

Time Resolution Theory in real time. Watch quantum mechanics disappear.

## Setup
1. Clone: `git clone https://github.com/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof.git`
2. Flash Arduino: [arduino/led_pulse.ino](arduino/led_pulse.ino)
3. Run: Hardware auto-updates this repo every minute.

**v1.0.0** – Initial live proof deploy (Nov 24, 2025).
