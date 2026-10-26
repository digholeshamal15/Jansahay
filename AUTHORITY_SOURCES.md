# Official authority directory: verification record

Checked on **22 October 2026**. Only source-supported HTTPS URLs are included; no contact numbers, department emails, submission endpoints or status APIs were invented.

| Area | Directory destination | Official corroborating source | Verification limits |
|---|---|---|---|
| Pimpri-Chinchwad | https://www.pcmchelpline.in/ (SARATHI) | https://www.pcmcindia.gov.in/e_services.php links to this domain under SARATHI / Residents | Source page retrieved. Destination timed out; live availability is not claimed. |
| Pune Municipal Corporation | https://www.pmccare.in/ (PMC CARE) | https://www.pmc.gov.in/en/initiatives/pmc-care-portal links to this destination under Services → PMC Care | Destination is linked by PMC; no login, submission or live status integration was tested. |
| Other Maharashtra area / state grievance | https://grievances.maharashtra.gov.in/en | https://sjsa.maharashtra.gov.in/en/service/grievance-redressal/ endorses this portal; https://sdma.maharashtra.gov.in/en/grievance-redressal/ also links to it | Destination timed out. Source endorsement, not successful availability, was verified. Correct jurisdiction must be selected externally. |

The older PMC complaint portal was also found at https://complaint.pmc.gov.in/home?language=en but timed out. The directory uses the PMC CARE link currently published on PMC's official website instead.

## What the handoff actually does

1. The user chooses a municipality.
2. JanSahay saves the complaint locally when Save & open official portal is selected.
3. The app records a local portal-handoff event and presents the reviewed destination link in a notice.
4. The user chooses whether to open that external page in a new tab.
5. The user manually pastes/uploads their content and submits it there, then records any acknowledgement in JanSahay.

A handoff is not proof the page loaded or that any complaint was submitted. It deliberately leaves status, reference number and submission date unchanged. “Ready to Submit” remains ready until the user makes an explicit status update. The app does not scrape private government accounts, submit forms, transmit photo/text payloads, or verify a government status.

Each directory entry stores its source URL, fallback URL, review date and verification caveat in `data/authorities.json`. Recheck official source pages before maintaining or expanding the directory.
