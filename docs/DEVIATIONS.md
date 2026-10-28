# Deviations Log

Where the implementation differs from the SRS, the SAD or the Test Plan, and why. Entries are added as the work is done. Each says what to change in the document, or confirms that the document is still right.

| ID | Story | Document and section | What the document says | What was built or found | Action |
|---|---|---|---|---|---|
| D-01 | US-02 | Test Plan, SV-01 test data | Lists `Password123!` as a password on the compromised list | It is not on Django's common-password list of 19,640 entries. `password1!` is, and it passes every other rule, so it isolates the list check | Test Plan corrected in this change |
| D-02 | US-02 | SRS 3.1 UI-6 screen inventory | Lists "Login and Password Reset" | A password change screen was added, because NFR-SEC11 requires sessions to end on password change and a user needs a way to do that | Add "Change Password" to the screen inventory |
| D-03 | US-02 | SRS NFR-SEC1 | Authenticate by username and password | Sign-in is by username. Email is also required and unique, because NFR-SEC4 emails the holder on lockout and the reset flow needs it | None, consistent with the SRS |
| D-04 | US-02 | SRS NFR-SEC4 | Lock for 15 minutes after 5 failures and notify the holder | The sign-in form says the account is locked and for how long when the username exists. This helps a real user and tells an attacker the username is valid. Failed attempts on unknown usernames get the normal generic message | Accepted trade-off. Revisit if the security review objects |
