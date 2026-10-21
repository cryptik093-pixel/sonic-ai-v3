# Release candidate limitations
FL Studio scan, playback, automation, project save/reopen and offline render acceptance require actual host testing. Native component/editor tests and VST3 validators do not establish this gate.

No human listening session has been claimed. Optional sample category suggestions remain provisional. Commercial JUCE licensing eligibility requires resolution before commercial distribution; local authorized evaluation does not resolve that obligation.

The engine accepts float32 processing. High sample transposition uses linear interpolation and can alias. State v2 from the interrupted sampler is rejected explicitly; v1 global synthesis controls migrate, and v3 kits preserve stable 181 parameters. Large optional sample layers increase memory. Exports share the control worker with kit/sample loading; audio playback continues, but those control operations wait or state recall cancels rendering. See the validation report for the actual callback performance result and any remaining failures.
