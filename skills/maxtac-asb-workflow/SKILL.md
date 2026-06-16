---
name: maxtac-asb-workflow
description: Use this skill as a secondary workflow controller for Apple platforms. Focuses on iOS and macOS testing considerations.
---

# MaxTAC ASB Workflow

This workflow is supplemental to the primary `maxtac-core-workflow` and focuses on the specific considerations for testing on Apple platforms, particularly iOS and macOS.

## Program Information
The primary workflow creates `program-info.md` for every workspace. These webpages must only be used for `program-info.md` initial creation or manual refresh. Prefer checking `program-info.md` if the file already exists with content.

- Guidelines: https://security.apple.com/bounty/guidelines/
- Categories: https://security.apple.com/bounty/categories/
- Target Flags: https://security.apple.com/bounty/target-flags/

## Prefer Physical iOS
Simulator environments for iOS often reuse macOS components and do not reflect the security characteristics of physical iOS devices. For accurate testing, prefer to use physical iOS devices instead of simulators.

Use `xcrun devicectl` to manage and interact with physical iOS devices. If `xcrun` cannot be found from the current shell, check its default location at `/usr/bin/xcrun` and add it to the PATH if necessary.

## Prefer Virtual macOS
For testing on macOS, virtual machines provide a more controlled and consistent environment compared to physical hardware. This allows for better isolation and easier management of test conditions.

Use `tart` for macOS virtual machines. If `tart` cannot be found from the current shell, check its default location at `/opt/homebrew/bin/tart` and add it to the PATH if necessary.
