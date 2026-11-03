"""Report definitions (SRS REQ-42, Appendix B.7). Column order is exact."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportSpec:
    slug: str
    title: str
    columns: tuple[str, ...]


REPORTS = {
    spec.slug: spec
    for spec in (
        ReportSpec(
            "registration",
            "Donor Registration Report",
            (
                "Donor ID",
                "Full Name",
                "Blood Group",
                "Mobile Number",
                "City",
                "Registration Date",
                "Eligibility Status",
                "Last Donation Date",
                "Next Eligible Date",
                "Total Donations",
            ),
        ),
        ReportSpec(
            "collection",
            "Blood Collection Report",
            (
                "Unit ID",
                "Donor ID",
                "Blood Group",
                "Component Type",
                "Volume",
                "Collection Date",
                "Collection Site",
                "Bag Lot Number",
                "Screening Outcome",
                "Current Status",
            ),
        ),
        ReportSpec(
            "inventory",
            "Inventory Status Report",
            (
                "Blood Group",
                "Component Type",
                "Available Count",
                "Reserved Count",
                "Quarantined Count",
                "Near-Expiry Count",
                "Expired Count",
                "Storage Location",
                "Oldest Expiry Date",
                "Total Volume",
            ),
        ),
        ReportSpec(
            "expiry",
            "Near-Expiry and Expiry Report",
            (
                "Unit ID",
                "Blood Group",
                "Component Type",
                "Collection Date",
                "Expiry Date",
                "Days To Expiry",
                "Storage Location",
                "Status",
                "Discard Reason",
                "Recorded By",
            ),
        ),
        ReportSpec(
            "request-issue",
            "Hospital Request and Issue Report",
            (
                "Request ID",
                "Hospital Name",
                "Blood Group",
                "Component Type",
                "Quantity Requested",
                "Quantity Issued",
                "Urgency",
                "Raised On",
                "Fulfilled On",
                "Status",
            ),
        ),
        ReportSpec(
            "camp",
            "Camp Performance Report",
            (
                "Camp ID",
                "Camp Name",
                "Camp Date",
                "Venue",
                "Organiser Name",
                "Donors Enrolled",
                "Donors Attended",
                "Target Units",
                "Units Collected",
                "Achievement Percentage",
            ),
        ),
    )
}
