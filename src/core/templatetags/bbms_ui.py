from django import template

register = template.Library()


@register.inclusion_tag("core/_sort_header.html", takes_context=True)
def sort_header(context, state, key, label):
    """A column header that sorts the list. Clicking the active column reverses it."""
    request = context["request"]
    active = state is not None and state.key == key
    next_dir = "desc" if active and state.direction == "asc" else "asc"
    params = request.GET.copy()
    params.pop("page", None)
    params["sort"] = key
    params["dir"] = next_dir
    return {
        "label": label,
        "url": f"?{params.urlencode()}",
        "active": active,
        "aria_sort": (
            ("ascending" if state.direction == "asc" else "descending") if active else "none"
        ),
        "arrow": ("▲" if state.direction == "asc" else "▼") if active else "",
    }


@register.simple_tag(takes_context=True)
def page_url(context, number):
    params = context["request"].GET.copy()
    params["page"] = number
    return f"?{params.urlencode()}"


@register.filter
def field_error_text(field):
    """Prefix each error with the field label, as SRS UI-4 requires."""
    return [f"{field.label}: {error}" for error in field.errors]


@register.filter
def render_field(field):
    """Render a bound field with ARIA attributes that tie it to its error message."""
    if field.errors:
        return field.as_widget(
            attrs={"aria-invalid": "true", "aria-describedby": f"{field.auto_id}_error"}
        )
    return field.as_widget()
