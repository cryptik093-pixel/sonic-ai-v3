# Echo, Space and Freeze implementation

These modules are production DSP, not JUCE demonstration effects. `prepare` owns
allocation; callback processing and incremental clearing contain no allocation,
deallocation, locks, I/O or logging. `reset` is an offline lifecycle operation.

## Echo

Two four-second float rings supply at most two linearly interpolated read taps.
Delay-time changes finish the current 100ms linear transition, then transition to
the latest queued target. Tempo/signature values are validated before use;
invalid host tempo uses the bounded displayed manual BPM and invalid signature
uses 4/4. Sync output is clamped to 10–4000ms with an exposed clamp flag.

Return filtering uses a complementary one-pole high pass followed by a one-pole
low pass, with 20ms coefficient smoothing. The return then passes four serial
allpasses per channel (0.65 coefficient, exact specified nominal times); Diffuse
linearly blends filtered and diffused returns before both output and feedback.
The feedback matrix is the specified interpolated identity/swap matrix; each
channel is protected by `4*tanh(x/4)` before applying the bounded feedback gain.
At full ping-pong, the arithmetic mono input sum injects only left, so a centered
source alternates channels. At zero ping-pong, injection preserves stereo.

Throw controls only new input: throw-only is 0→1 and continuous is 1→10^(6/20),
with exactly 5ms linear ramps. Feedback and stored repeats remain independent.
Enable, feedback, ping-pong and diffusion use 20ms one-pole smoothing. There is no
lookahead or hidden direct voice. `maximumState()` measures un-limited ring state.

## Space

The eight distinct delays use the specified 29.7/37.1/41.1/43.7/53.1/59.3/67.7/
71.9ms nominal times, rounded to distinct sample counts. Feedback is the
Householder matrix `I - 11^T/4`. Per-line gain is `10^(-3*d/T)` with one-pole
damping; target seconds remain a target because damping changes the measured
frequency-dependent decay. Coefficients and excitation gain smooth over 20ms.

Input vectors are `(1,1,1,1,1,1,1,1)/sqrt(8)` and
`(1,-1,1,-1,1,-1,1,-1)/sqrt(8)`, combined with an additional `1/sqrt(2)`.
Output vectors are `(1,1,-1,-1,1,1,-1,-1)/sqrt(8)` and
`(1,-1,-1,1,1,-1,-1,1)/sqrt(8)`. All vectors have unit Euclidean norm;
the input pair and output pair are orthogonal. Predelay is preallocated stereo.
Delay send taps its already leveled return before ducking.

Ducking measures the pre-cleanup input's linked sample peak. Desired reduction
is `min(maxReduction, max(0, peakDb-threshold)*0.75)` and the reduction in dB
uses attack/release exponential smoothing with `alpha=exp(-1/(time*Fs))`.
The returned duck gain is applied by the engine to both spatial returns. It
never enters either network's feedback; Freeze remains outside this gain.

## Freeze

Two preallocated 250ms stereo histories alternate immutable hold and normal
spatial recording. A rising edge exchanges ownership rather than copying audio.
History receives only the normal, already ducked delay/reverb combination, never
the held voice. Loop wrap uses 20ms complementary overlap with unity-sum weights,
giving a 230ms repeated period from the captured 250ms window. Fade into hold is
50ms; release is 250ms. The engine suppresses new spatial excitation while held
and resumes it on release while the normal return crossfades back.

**Rapid re-trigger policy:** until the rolling spare contains a complete new
250ms window, reuse the most recent complete immutable window. This prevents
stale partial rings and satisfies bounded work without extra capture storage.
A fresh capture becomes available after 250ms. This is explicit coalescing, not
an undocumented audio-thread buffer copy. No vocal buffers enter serialization.

## Clearing and evidence

Every module's `clearStep(maxWrites)` counts total float writes across all owned
buffers and filter states; zero budget cannot advance clearing. Scalar indices
are reset outside the float-write loop. Processing stays muted during clearing;
the parent transition controller supplies the specified fades and global budget.
`allocatedBytes()` reports vector capacities, excluding fixed object overhead.

Tests use the actual production classes: impulse timing and tempo matrix,
ping-pong channel alternation, Throw ratios, zero-feedback diffusion, internal
feedback bounds, Schroeder T20 decay extrapolation, duck limits/network
independence, stereo excitation, 60-second constant texture hold, exact fades and
one-float clearing. Actual PASS/FAIL and measured decay values belong in the
aggregate verification report; source existence alone is not test evidence.
