# Contributing to EMDR Bilateral Stimulation Device

Thank you for your interest in this project! This is a personal research project shared openly under open-source licenses.

## How to Contribute

### Bug Reports & Suggestions

**Issues are welcome!** If you find bugs, have questions, or want to suggest improvements:

1. Open an issue on GitHub
2. Describe the problem or suggestion clearly
3. Include relevant details (hardware revision, firmware version, logs if applicable)

### Code Contributions

**I prefer to implement changes myself.** This ensures:

- Hands-on testing with the actual hardware
- Consistency with the AI-assisted development workflow
- Direct verification of therapeutic safety requirements

If you have a code suggestion, please open an issue describing the change rather than a pull request. I'll implement and test it myself.

### Forks Welcome

Feel free to fork this project and take it in your own direction! The licenses allow this:

- **Hardware:** CERN-OHL-S v2 (share-alike)
- **Software:** GPL v3

If you build something interesting, I'd love to hear about it.

## Why This Approach?

This project has tight integration between:
- Hardware design (custom PCB with specific component choices)
- Firmware (ESP-IDF with FreeRTOS, JPL coding standards)
- Therapeutic requirements (EMDRIA standards for bilateral stimulation)

Making changes requires testing on physical hardware to verify safety and effectiveness. Since I have the hardware and understand the full context, it's more efficient for me to implement changes directly.

## Questions?

Open an issue! I'm happy to discuss the design, explain implementation choices, or help you adapt the project for your needs.
