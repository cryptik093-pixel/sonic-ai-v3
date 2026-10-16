# ADLIB-93 native interface

The native JUCE editor retains the approved 1040×680 pedal composition, ten primary parameter controls and six scrollable detail pages. Character, movement, echo, reverb and cleanup enable flags are available separately from branch-level controls. Main labels open their named detail pages. Slider attachments preserve stable parameter IDs, numeric input, keyboard operation, fine drag and double-click defaults. Interface-scale choices are 75/100/125/150%; Windows DPI and keyboard acceptance remain PENDING until exercised in a real host.

The compact top-row input trim uses a horizontal label/value layout instead of placing a 24-pixel text editor into a 16-pixel slider remainder. Frequency readouts show effective `min(requested,0.45×sampleRate)` values and CLAMP when limited, while retaining the underlying requested parameter. Send overrides and Clean-mode Drive explanations remain visible without rewriting stored Insert values.

## Preset browser

Factory rows display approved names/families. User JSON is read through the real `PresetStore` validator on the message thread; each read is bounded by its existing 256 KiB limit and directory/filename/schema validation. Display and search use the validated preset display name rather than its opaque internal filename. Corrupt or unsafe files are omitted and a visible browser notice counts rejected files. No source vocal recordings or capture buffers are read or saved by the browser.

An intentional single-click or Enter loads the selected row. Search updates, arrow-key navigation and programmatic selection do not load. LOAD remains an explicit accessible alternative. Clear-state guards reject activation even before the disabled controls repaint; preset navigation/loading, A/B, resets, routing and conflicting performance/parameter controls are disabled while clearing. Browser Close remains available.

## Performance and diagnostics

Throw has distinct press/release handling for mouse and keyboard. Momentary Throw releases on the Throw control losing focus, the editor losing focus and editor destruction; explicit latch mode retains its own state. Listen, Freeze and Clearing indicators are combined rather than hiding one another. A separate visible DIAG counter displays the processor's actual diagnostic count without replacing those indicators. Meter reads use the existing atomic bridge at 30 Hz.

## Evidence boundary

The complete approved specification and plan remain unchanged. Added UI.BrowserActivation tests cover navigation versus explicit activation and clearing inhibition using the production control model. Existing UI.Bindings, UI.RoutingOverrides and UI.Gestures cover mapping, overrides and gesture state. Native compilation and offscreen rendering at 75/100/150% passed; final captures are in evidence/editor-final. The title/header decoding repair was visually inspected. pluginval strictness10 also passed editor lifecycle/automation checks. Real host focus/keyboard behavior, interface scales × Windows 100/150/200% DPI, FL Studio operation and listening remain PENDING. An offscreen render is not host compatibility or accessibility acceptance.

The pinned JUCE 9 headers still provide `Graphics::setFont(float)`. Legacy `Font(float,style)` constructors are deprecated rather than absent; editor font construction now uses `FontOptions` to avoid relying on those deprecated constructors.
