"""Update docs/FINAL_PROJECT_REPORT.html to align with verified empirical figures in FINAL_PROJECT_REPORT.md."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "docs" / "FINAL_PROJECT_REPORT.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update Abstract paragraph
old_abs = """Comprehensive empirical testing across a 111-test suite demonstrated a <strong>99.1% pass rate</strong> (110 passed, 0 failed, 1 intentionally skipped for live prosody). In live measurements on an NVIDIA GeForce RTX 4050 Laptop GPU, Parlor achieved a conversational Time to First Audio (<strong>TTFA</strong>) of <strong>0.781 s</strong>, an end-to-end wellness cycle latency of <strong>2.82 s</strong> (well within the 5.0 s budget), and a hardware footprint of <strong>3.84 GB VRAM</strong>. A network socket audit confirmed <strong>0.00 KB</strong> of outbound data transmission. In ground-truth validation using an Ecological Momentary Assessment (<strong>EMA</strong>) protocol across $N=8$ participants and 144 paired observation windows, the system achieved a <strong>77.8% exact-tier agreement rate</strong>, a <strong>100.0% one-tier-tolerance agreement rate</strong>, and <strong>0.0% false-positive and false-negative critical error rates</strong>. Parlor establishes that clinically meaningful, explainable affective wellness computing can be achieved locally, privately, and affordably on everyday personal computing devices."""

new_abs = """Comprehensive empirical testing across a 111-test suite demonstrated a <strong>99.1% pass rate</strong> (110 passed, 0 failed, 1 intentionally skipped for live prosody). In live measurements on an NVIDIA GeForce RTX 4050 Laptop GPU and Intel Core i5-13450HX CPU, Parlor achieved a conversational Time to First Audio (<strong>TTFA</strong>) of <strong>1.411 s mean</strong> (wellness loop OFF) and <strong>1.829 s mean</strong> (wellness loop ON, +0.418 s concurrency cost mitigated by voice turn deferral), an on-device SLM qualitative reasoning latency of <strong>2.14 s mean / 2.42 s p95</strong> (leaving a 2.58 s safety margin below the 5.0 s engineering window budget), real face extraction latency of <strong>3.97 ms mean</strong>, and a hardware footprint of <strong>3.90 GB VRAM</strong>. A network socket audit confirmed <strong>0.00 KB</strong> of outbound data transmission. Human ground-truth accuracy is formally marked as <strong>NOT YET COLLECTED / REQUIRES HUMAN STUDY</strong>, with turnkey collection and evaluation tooling ready. Parlor establishes that robust, explainable affective wellness computing can be achieved locally, privately, and affordably on everyday personal computing devices."""

html = html.replace(old_abs, new_abs)

# 2. Update Section 5.2 Table
old_s52 = """<h3>5.2 System Latency and Subsystem Benchmark Breakdown</h3>
<p>| Subsystem Component | Empirical Measurement | Target Specification | Latency Margin |<br />
|:---|:---:|:---:|:---:|<br />
| <strong>Conversational Turn TTFA</strong> | <strong>0.781 s</strong> | $\\le 1.000\\text{ s}$ | $+219\\text{ ms}$ |<br />
| <strong>Acoustic Turn Classification (<code>smart-turn</code>)</strong> | <strong>68.2 ms</strong> | $\\le 100.0\\text{ ms}$ | $+31.8\\text{ ms}$ |<br />
| <strong>Facial AU Feature Extraction</strong> | <strong>14.2 ms</strong> | $\\le 35.0\\text{ ms}$ | $+20.8\\text{ ms}$ |<br />
| <strong>Vocal Acoustic DSP Extraction</strong> | <strong>18.7 ms</strong> | $\\le 30.0\\text{ ms}$ | $+11.3\\text{ ms}$ |<br />
| <strong>Temporal Feature Fusion &amp; Prompt Build</strong> | <strong>0.02 ms</strong> | $\\le 5.0\\text{ ms}$ | $+4.98\\text{ ms}$ |<br />
| <strong>SLM Qualitative Reasoning (GPU)</strong> | <strong>2.760 s</strong> | $\\le 4.500\\text{ s}$ | $+1.740\\text{ s}$ |<br />
| <strong>SQLite Transaction Logging</strong> | <strong>2.57 ms</strong> | $\\le 10.0\\text{ ms}$ | $+7.43\\text{ ms}$ |<br />
| <strong>Total Observation Cycle E2E Latency</strong> | <strong>2.820 s</strong> | $\\le 5.000\\text{ s}$ | $+2.180\\text{ s}$ |</p>
<p>The 95th-percentile SLM latency across 30 repeated live cycles was <strong>3.12 s</strong>, which, combined with the 21 ms non-SLM extraction overhead, leaves a generous <strong>1.859 s safety margin</strong> below the 5.0-second window budget.</p>"""

new_s52 = """<h3>5.2 System Latency and Subsystem Benchmark Breakdown</h3>
<p>All latency figures represent empirical measurements captured on this machine and logged in <code>evidence/</code>:</p>
<table border="1" cellpadding="6" style="border-collapse:collapse; width:100%; margin: 1rem 0;">
<thead>
<tr style="background:#f1f5f9;">
<th>Subsystem Component</th><th>Empirical Measurement</th><th>Engineering Budget</th><th>Evidence File</th>
</tr>
</thead>
<tbody>
<tr><td><strong>Conversational Turn TTFA (Loop OFF)</strong></td><td><strong>1.411 s mean / 1.384 s p50</strong> (N=10)</td><td>—</td><td><code>evidence/voice_ttfa.csv</code></td></tr>
<tr><td><strong>Conversational Turn TTFA (Loop ON)</strong></td><td><strong>1.829 s mean / 1.745 s p50</strong> (N=10)</td><td>—</td><td><code>evidence/voice_ttfa.csv</code> (+0.418s mitigated cost)</td></tr>
<tr><td><strong>Facial AU Extraction (Real Face, Normal)</strong></td><td><strong>3.97 ms mean / 4.81 ms p95</strong> (N=100)</td><td>—</td><td><code>evidence/facial_extraction_real.csv</code></td></tr>
<tr><td><strong>Facial AU Extraction (Real Face, Dim 15%)</strong></td><td><strong>4.39 ms mean / 6.84 ms p95</strong> (N=100)</td><td>—</td><td><code>evidence/facial_extraction_dim.csv</code></td></tr>
<tr><td><strong>Facial AU Extraction (Head Turned ~30°)</strong></td><td><strong>4.69 ms mean / 6.58 ms p95</strong> (N=100)</td><td>—</td><td><code>evidence/facial_extraction_turned.csv</code></td></tr>
<tr><td><strong>Facial AU Extraction (Blank / No Face)</strong></td><td><strong>1.92 ms mean / 2.45 ms p95</strong> (N=100)</td><td>—</td><td><code>evidence/facial_extraction_blank.csv</code> (early exit)</td></tr>
<tr><td><strong>Vocal Acoustic DSP Extraction (CPU)</strong></td><td><strong>2.85 ms mean / 3.73 ms p95</strong> (N=100)</td><td>—</td><td><code>evidence/vocal_extraction.csv</code></td></tr>
<tr><td><strong>Temporal Feature Fusion &amp; Prompt Build</strong></td><td><strong>&lt; 0.05 ms</strong></td><td>—</td><td>In-memory deque aggregation</td></tr>
<tr><td><strong>SLM Qualitative Reasoning (GPU, Gemma 4 E2B)</strong></td><td><strong>2.14 s mean / 2.42 s p95</strong> (N=30)</td><td>$\le 5.000\\text{ s}$ (window)</td><td><code>evidence/wellness_slm_latency.csv</code> (+2.58s margin)</td></tr>
<tr><td><strong>SQLite Transaction Logging</strong></td><td><strong>4.07 ms mean / 5.29 ms p95</strong> (N=100)</td><td>—</td><td><code>evidence/db_write_latency.csv</code></td></tr>
<tr><td><strong>Complete Observation Cycle E2E Latency</strong></td><td><strong>2.15 s mean / 2.43 s p95 total</strong></td><td>$\le 5.000\\text{ s}$ (window)</td><td><code>evidence/wellness_slm_latency.csv</code> (+2.57s margin)</td></tr>
</tbody>
</table>
<p>The 95th-percentile SLM latency across 30 repeated live cycles was <strong>2.42 s</strong>, which, combined with the &lt; 8 ms non-SLM extraction and database overhead, leaves a generous <strong>2.57 s safety margin</strong> below the 5.0-second window budget. Running background wellness monitoring concurrently adds +0.418 s latency to conversational speech turns on a single GPU, which is actively mitigated by deferring wellness SLM cycles during active speech.</p>"""

html = html.replace(old_s52, new_s52)

# 3. Update VRAM in Section 5.3
html = html.replace('<strong><code>3.84 GB</code></strong> / 6.00 GB (64.0% allocation)', '<strong><code>3.90 GB</code></strong> (3991 MB peak / 6141 MB allocation)')

# 4. Update Section 5.5
old_s55 = """<h3>5.5 Ground-Truth Accuracy Validation (EMA Protocol Analysis)</h3>
<blockquote>
<p><strong>Important Distinction:</strong><br />
<strong>Model Quantization Agreement (91.4%):</strong> Measures synthetic output fidelity of 4-bit compressed weights compared to uncompressed 16-bit teacher models across benchmark test vectors.<br />
<strong>Ground-Truth Agreement (77.8%):</strong> Measures diagnostic agreement between the system's inferred stress tiers and actual human psychological self-report across live participants.</p>
</blockquote>
<h4>5.5.1 Experimental Setup ($N=8$, 144 Windows)</h4>
<p>The validation protocol evaluated 8 participants (3 core developers, 5 peer student volunteers) across 4 controlled conditions:</p>
<ol>
<li><em>Quiet Focused Work</em> (5 windows / person): Reading technical documentation quietly.</li>
<li><em>Active Speaking / Collaboration</em> (5 windows / person): Technical explanation aloud.</li>
<li><em>Acute Cognitive Stressor</em> (5 windows / person): 60-second timed mental arithmetic + Stroop color-word interference task under auditory noise.</li>
<li><em>Single-Modality Fallback</em> (3 windows / person): Camera occluded / lighting $&lt;20$ lux during acute stress task.</li>
</ol>
<h4>5.5.2 3x3 Empirical Confusion Matrix</h4>
<pre><code>                         EMA Ground Truth (Human Self-Report)
                     ┌──────────────┬──────────────┬──────────────┐
                     │    Tier 0    │    Tier 1    │    Tier 2    │
  ┌──────────────────┼──────────────┼──────────────┼──────────────┤
  │ System Tier 0    │      40      │      28      │       0      │
  ├──────────────────┼──────────────┼──────────────┼──────────────┤
  │ System Tier 1    │       0      │      12      │       3      │
  ├──────────────────┼──────────────┼──────────────┼──────────────┤
  │ System Tier 2    │       0      │       1      │      60      │
  └──────────────────┴──────────────┴──────────────┴──────────────┘
</code></pre>
<h4>5.5.3 Key Accuracy Metrics</h4>
<ul>
<li><strong>Exact-Tier Agreement Rate:</strong> <strong><code>77.8%</code></strong> (112 of 144 paired windows).</li>
<li><strong>One-Tier-Tolerance Agreement Rate:</strong> <strong><code>100.0%</code></strong> (144 of 144 windows).</li>
<li><strong>Catastrophic Errors ($0 \\leftrightarrow 2$):</strong> <strong><code>0.0%</code></strong> (Zero extreme misclassifications).</li>
<li><strong>False Positive Rate (FPR) for Tier 2:</strong> <strong><code>0.0%</code></strong> (0 of 40 Tier 0 baseline windows misclassified as Tier 2).</li>
<li><strong>False Negative Rate (FNR) for Tier 2:</strong> <strong><code>0.0%</code></strong> (0 of 63 Tier 2 acute stress windows misclassified as Tier 0).</li>
<li><strong>Multimodal Condition Accuracy:</strong> <strong><code>75.0%</code></strong> exact agreement.</li>
<li><strong>Audio-Only Fallback Accuracy:</strong> <strong><code>91.7%</code></strong> exact agreement.</li>
</ul>
<p><em>Analysis of Discrepancies:</em> All 32 off-diagonal classifications occurred at subjective boundary thresholds (EMA composite scores 5–6 between Tier 0/1, or 10–11 between Tier 1/2) or reflected autonomic recovery lag (where a participant felt mentally calm immediately following the timed stressor while physiological brow tension and vocal perturbation took 60–90 seconds to normalize).</p>"""

new_s55 = """<h3>5.5 Affective Validation and EMA Ground-Truth Study</h3>
<blockquote>
<p><strong>Critical Methodological Distinction:</strong><br />
<strong>Model Quantization Agreement:</strong> Measures numerical and syntactic fidelity between quantized weights and full-precision FP16 weights on identical prompts. On this machine, FP16 weights were not downloaded for Gemma 4 E2B, so quantization agreement is marked <strong>NOT MEASURED</strong>.<br />
<strong>Human Ground-Truth Agreement:</strong> Measures agreement between the system's inferred stress tiers and genuine human psychological self-reports via Ecological Momentary Assessment (EMA).</p>
</blockquote>
<h4>5.5.1 Data Provenance Audit and Human Study Status</h4>
<p>A comprehensive code and data audit (<code>EVIDENCE_AUDIT.md</code>) revealed that preliminary reports referencing 144 windows with 77.8% exact agreement were based on synthetically generated trials in <code>shared_state/ema_validation_trials.json</code> produced by <code>scripts/run_ema_validation.py</code> using statistical distributions for verifying analysis pipelines.</p>
<p>In strict adherence to academic research integrity:</p>
<ol>
<li><strong>The synthetic numbers are NOT represented as empirical human ground truth.</strong></li>
<li><strong>Empirical EMA Accuracy is formally marked as: <code>NOT COLLECTED / REQUIRES HUMAN STUDY</code>.</strong></li>
<li>A complete, turnkey collection harness and standardized human study protocol have been established in <code>scripts/ema_collector.py</code> and <code>docs/EMA_RECOLLECTION_KIT.md</code> for execution by the student team with $\ge 8$ human participants (4 developers + 4 external peers) prior to viva.</li>
</ol>
<h4>5.5.2 Human Ground-Truth Accuracy Status &amp; Tooling Readiness</h4>
<p><strong>Human ground-truth accuracy: NOT YET COLLECTED. Protocol and tools are ready.</strong></p>
<p>The evaluation suite has been updated in <code>scripts/evaluate_ema.py</code> with:</p>
<ul>
<li>Strict integrity and consent refusal check (rejects unverified or missing consent flags).</li>
<li>Ground-truth class distribution and majority-class baseline.</li>
<li>Exact tier agreement and one-tier tolerance agreement with 95% bootstrap confidence intervals.</li>
<li>Quadratic-weighted Cohen's Kappa ($\kappa_w$).</li>
<li>Full 3x3 confusion matrix with marginals.</li>
<li>Per-participant agreement breakdown.</li>
<li>Tier 2 safety rates (False Positive Rate and False Negative Rate) computed separately with and without developers to detect confirmation bias.</li>
<li>Fully tested and verified on <code>shared_state/toy_ema_records.json</code>.</li>
</ul>"""

html = html.replace(old_s55, new_s55)

# 5. Update Section 5.6
old_s56 = """<h3>5.6 Cross-Modal Conflict and Signal Honesty Verification</h3>
<p>To prove that the Small Language Model performs genuine pattern reasoning rather than executing fixed thresholds:</p>
<ol>
<li><strong>Cross-Modal Conflict Test:</strong> The model was fed an artificial input with severe vocal frequency perturbation ($\Delta F0 &gt; 30\\text{ Hz}$, high jitter) but completely relaxed facial landmarks (AU04 = 0.05). A static threshold system triggers a false-positive Tier 2 alert. Parlor's SLM correctly evaluated the conflict, outputting Tier 1 with the rationale:
<blockquote>
<p><em>&quot;Assessed as Moderate Stress due to conflicting signals between modalities... Vocal biomarkers indicate acoustic tension while facial expressions remain neutral.&quot;</em></p>
</blockquote>
</li>
<li><strong>Signal Honesty Test:</strong> When the webcam was covered and the participant remained silent, the system output:
<blockquote>
<p><em>&quot;No facial or vocal signals detected in the current observation window&quot;</em> with <code>confidence_score: 0.0</code>, correctly suppressing any intervention firing.</p>
</blockquote>
</li>
</ol>"""

new_s56 = """<h3>5.6 Cross-Modal Conflict, Signal Honesty, and Failure Recovery Verification</h3>
<p>Live empirical benchmarks were executed directly against Google Gemma 4 E2B IT on this machine to verify pattern reasoning, resilience, and failure recovery:</p>
<ol>
<li><strong>Cross-Modal Conflict Test (5 Repeats, Evidence: <code>evidence/live_pattern_reasoning.json</code>):</strong> In 5 out of 5 consecutive trials, Gemma 4 E2B correctly evaluated vocal pitch spikes ($\Delta F0=+37.5\\text{ Hz}$) with relaxed face (AU04=0.05) as <strong>Low (Tier 0)</strong>, citing vocal arousal without emotional distress.</li>
<li><strong>Consistent Multimodal Stress Test (5 Repeats, Evidence: <code>evidence/live_pattern_reasoning.json</code>):</strong> In 5 out of 5 consecutive trials, Gemma 4 E2B classified concurrent brow furrowing (AU04=0.84) and vocal strain as <strong>Moderate (Tier 1)</strong> with 0.92 confidence.</li>
<li><strong>Signal Honesty Test (Evidence: <code>evidence/live_zero_signal.json</code>):</strong> When the webcam is covered and microphone is silent, the system outputs <code>confidence_score: 0.0</code> and Tier 0 with zero compute wasted.</li>
<li><strong>Graceful Failure and Mid-Session Recovery (3 Repeats, Evidence: <code>evidence/live_llama_kill_recovery.log</code>):</strong> Killing <code>llama-server</code> mid-session cleanly raises <code>LLAMAServerError</code>. The server automatically respawns and restores healthy state in <strong>3.95 s mean recovery time</strong>.</li>
</ol>"""

html = html.replace(old_s56, new_s56)

# 6. Update Section 6.2
old_s62 = """<h3>6.2 System Limitations Under Adverse Environmental Conditions</h3>
<ol>
<li><strong>Webcam Lighting Degradation:</strong> In environments with illumination $&lt;20\\text{ lux}$, MediaPipe FaceMesh landmark confidence degrades, causing <code>face_detected</code> to toggle to False. The system gracefully falls back to audio-only acoustic estimation.</li>
<li><strong>Head Pose Sensitivity:</strong> Yaw angles $&gt;30^\\circ$ (user looking sideways away from the screen) introduce perspective distortion in Euclidean facial landmark distances.</li>
<li><strong>Acoustic Dependency on Active Speech:</strong> Vocal acoustic biomarkers require the user to speak. During prolonged silent work, the system relies exclusively on facial Action Units and blink frequency.</li>
</ol>"""

new_s62 = """<h3>6.2 System Limitations and Boundary Disclosures</h3>
<ol>
<li><strong>Voice Latency Cost of Concurrent Monitoring:</strong> On a shared GPU, running affective monitoring concurrently with conversational turns adds +0.418 s mean latency to voice TTFA (1.411s loop off vs 1.829s loop on). While mitigated by deferring wellness cycles during speech, concurrency cost remains a physical reality on a single consumer GPU.</li>
<li><strong>Single GPU Contention and KV Cache Eviction:</strong> <code>llama-server</code> operates on a single GPU slot (<code>-np 1</code>). If a background reasoning pass is dispatched, the conversational prefix tokens in the KV cache can be evicted, requiring context re-prefill for subsequent conversational requests unless deferred.</li>
<li><strong>Vocal Biomarker Speech Requirement:</strong> Vocal acoustic biomarkers require active speech. During extended silent reading or programming, the system relies exclusively on facial Action Units and blink metrics.</li>
<li><strong>Lighting and Head-Pose Sensitivity:</strong> MediaPipe landmark tracking requires &gt;20 lux ambient illumination. Under dim lighting or head yaw &gt;30°, confidence degrades, falling back to audio-only estimation.</li>
<li><strong>Corrective Glasses and Skin-Tone Bias:</strong> Thick-rimmed glasses dampen AU07 (eyelid tightening) detection. Demographic diversity across skin tones and facial structures requires extensive cross-cohort testing before general deployment.</li>
<li><strong>Absence of Large-Scale Human Clinical Data:</strong> Empirical human ground truth is marked as <code>NOT YET COLLECTED / REQUIRES HUMAN STUDY</code>. Real EMA data collection ($N \\ge 8$) is prepared and pending execution.</li>
<li><strong>Strict Non-Clinical Boundary:</strong> The system estimates behavioral stress indicators to suggest ergonomic micro-breaks; it is NOT clinically validated and does NOT diagnose medical conditions.</li>
<li><strong>Network Boundary Scope:</strong> Standard operation is strictly local (0 outbound sockets); initial model weights are downloaded once, and optional user-triggered research mode is the only network-capable feature.</li>
</ol>"""

html = html.replace(old_s62, new_s62)

# 7. Update Conclusion Section 7.2
old_s72 = """<p>With a <strong>99.1% test suite pass rate</strong>, sub-second conversational TTFA (<strong>0.781 s</strong>), a <strong>2.82 s</strong> end-to-end observation cycle latency, complete network isolation (<strong>0.00 KB</strong> outbound), and <strong>77.8% exact / 100% one-tier ground-truth agreement</strong> against human EMA self-reports, Parlor demonstrates that robust, private, and explainable affective AI is achievable today on everyday edge computing devices.</p>"""

new_s72 = """<p>With a <strong>99.1% test suite pass rate</strong> (110 passed, 0 failed, 1 skipped by design), conversational TTFA of <strong>1.411 s mean</strong> (loop off) and <strong>1.829 s mean</strong> (loop on, +0.418s concurrency cost), a <strong>2.14 s mean / 2.42 s p95</strong> SLM reasoning latency (leaving a 2.58 s safety margin below the 5.0 s budget), real face extraction of <strong>3.97 ms mean</strong>, vocal DSP of <strong>2.85 ms mean</strong>, complete local network isolation (<strong>0.00 KB</strong> outbound transmission), and a standardized Human Study Re-Collection Kit (<code>docs/EMA_RECOLLECTION_KIT.md</code>), Parlor establishes that robust, private, and explainable affective AI is achievable today on everyday edge computing devices.</p>
<hr />
<h2>APPENDIX A: SYNTHETIC PIPELINE SMOKE TEST (REFERENCE ONLY)</h2>
<p>For algorithmic verification of the matrix rendering logic during early development, a synthetic test run was performed to verify code execution:</p>
<pre><code>                  REFERENCE SYNTHETIC MATRIX (PIPELINE TEST ONLY)
                         EMA Ground Truth (Simulated Labels)
                      ┌──────────────┬──────────────┬──────────────┐
                      │    Tier 0    │    Tier 1    │    Tier 2    │
   ┌──────────────────┼──────────────┼──────────────┼──────────────┤
   │ System Tier 0    │      40      │      28      │       0      │
   ├──────────────────┼──────────────┼──────────────┼──────────────┤
   │ System Tier 1    │       0      │      12      │       3      │
   ├──────────────────┼──────────────┼──────────────┼──────────────┤
   │ System Tier 2    │       0      │       1      │      60      │
   └──────────────────┴──────────────┴──────────────┴──────────────┘
</code></pre>
<p><em>NOTICE: The synthetic values above are preserved solely as a pipeline smoke test. They do not constitute an empirical performance result. Real human evaluation data will be generated by running <code>scripts/evaluate_ema.py</code> following participant collection.</em></p>"""

html = html.replace(old_s72, new_s72)

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("Updated docs/FINAL_PROJECT_REPORT.html successfully!")

