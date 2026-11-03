import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import render

from accounts.models import Role
from accounts.permissions import role_required

from .access import allowed_reports, can_run
from .definitions import REPORTS
from .forms import RangeForm
from .services.export import to_csv, to_pdf
from .services.generator import ReportError, generate
from .services.result import format_value

logger = logging.getLogger(__name__)

REPORT_ROLES = (Role.STAFF, Role.ADMIN, Role.HOSPITAL)


@role_required(*REPORT_ROLES)
def index(request):
    """The reports this user may run (SRS REQ-44)."""
    return render(request, "reports/index.html", {"reports": allowed_reports(request.user)})


@role_required(*REPORT_ROLES)
def run(request, slug):
    """Show one report for a date range, or export it as CSV or PDF (SRS REQ-42, REQ-43)."""
    if slug not in REPORTS:
        raise Http404
    if not can_run(request.user, slug):
        raise PermissionDenied
    spec = REPORTS[slug]
    form = RangeForm(request.GET if "start" in request.GET else None)
    result, error = None, ""
    if form.is_bound and form.is_valid():
        try:
            result = generate(
                slug, form.cleaned_data["start"], form.cleaned_data["end"], request.user
            )
        except ReportError as exc:
            error = str(exc)
    if result is not None:
        fmt = request.GET.get("format", "")
        if fmt in ("csv", "pdf"):
            logger.info("report exported slug=%s format=%s user_id=%s", slug, fmt, request.user.pk)
            body, mime = (
                (to_csv(result), "text/csv")
                if fmt == "csv"
                else (to_pdf(result), "application/pdf")
            )
            response = HttpResponse(body, content_type=mime)
            filename = f"{slug}-{result.start:%Y%m%d}-{result.end:%Y%m%d}.{fmt}"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
    if not form.is_bound:
        form = RangeForm(initial=RangeForm.last_30_days())
    rows = [[format_value(cell) for cell in row] for row in result.rows] if result else []
    return render(
        request,
        "reports/report.html",
        {
            "spec": spec,
            "form": form,
            "result": result,
            "rows": rows,
            "error": error,
            "query": request.GET.urlencode() if result else "",
        },
    )
