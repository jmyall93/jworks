# JWorks V11.1

## Company onboarding and users
- New Company wizard now creates the company and its initial Company Administrator together.
- Platform Owner can add users to any managed company.
- Company and Platform administrators can change roles, enable/disable accounts, and reset passwords.
- Active-seat limits are enforced when adding or re-enabling users.

## Sign-in microphone
- Voice microphone controls are explicitly anchored to the far-right side of supported sign-in inputs.

## AI diagnostics
- Test AI Connection now independently calls OpenRouter `/api/v1/key` before the chat-completions test.
- Diagnostics separately report key endpoint reachability/authentication and chat endpoint authentication.
- No secret value is returned to the browser.

## Data
- No new D1 migration is required for V11.1. Existing V11 company and project data is preserved.
