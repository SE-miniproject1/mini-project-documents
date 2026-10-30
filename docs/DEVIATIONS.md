# Deviations Log

Where the implementation differs from the SRS, the SAD or the Test Plan, and why. Entries are added as the work is done. Each says what to change in the document, or confirms that the document is still right.

| ID | Story | Document and section | What the document says | What was built or found | Action |
|---|---|---|---|---|---|
| D-01 | US-02 | Test Plan, SV-01 test data | Lists `Password123!` as a password on the compromised list | It is not on Django's common-password list of 19,640 entries. `password1!` is, and it passes every other rule, so it isolates the list check | Test Plan corrected in this change |
| D-02 | US-02 | SRS 3.1 UI-6 screen inventory | Lists "Login and Password Reset" | A password change screen was added, because NFR-SEC11 requires sessions to end on password change and a user needs a way to do that | Add "Change Password" to the screen inventory |
| D-03 | US-02 | SRS NFR-SEC1 | Authenticate by username and password | Sign-in is by username. Email is also required and unique, because NFR-SEC4 emails the holder on lockout and the reset flow needs it | None, consistent with the SRS |
| D-04 | US-02 | SRS NFR-SEC4 | Lock for 15 minutes after 5 failures and notify the holder | The sign-in form says the account is locked and for how long when the username exists. This helps a real user and tells an attacker the username is valid. Failed attempts on unknown usernames get the normal generic message | Accepted trade-off. Revisit if the security review objects |
| D-05 | US-03 | SRS 3.1 UI-5 | Irreversible actions need a confirmation dialog naming the record | Not built in this story. No irreversible action exists yet. It is built with the first one (US-14 manual discard, US-19 issue) | Tracked against those stories |
| D-06 | US-03 | SRS 3.1 UI-3 | Alt+N new record, Alt+S save, Alt+F search, Escape cancel | Implemented with the key's physical position, so it works on any layout including macOS, where Alt+letter types a different character. Pages opt in with `data-shortcut="new|save|search|cancel"` | None, behaviour matches the SRS |
| D-07 | US-03 | SRS 3.1 UI-6 | One home screen per role | A single home page lists the screens the role may use. The menu is generated from one registry in `core/navigation.py` and only shows a link once its page exists | None |
| D-08 | US-04 | SRS Appendix B.1 | Lists the donor fields | Two fields were added: `user`, which links the donor to its sign-in account, and `deferral_review_date`, which REQ-8 needs to clear a deferral automatically. Both are needed and neither contradicts the layout | Add both to Appendix B.1 and the ER diagram |
| D-09 | US-04 | SRS 5.1.2 sequence 1 | Registration creates the donor record | Registration also creates the donor's sign-in account in the same transaction, with the donor ID as the username. The password is chosen on the registration form | Mention the account in sequence 1 |
| D-10 | US-04 | SRS REQ-2 | Identifier of the form DNR followed by 8 digits | Numbers come from a database counter starting at 10000001, matching the Test Plan seed data. A rejected registration does not use up a number | None |
