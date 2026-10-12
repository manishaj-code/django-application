from django import forms, template

register = template.Library()


@register.filter
def is_checkbox(bound_field):
    return isinstance(bound_field.field.widget, forms.CheckboxInput)


@register.filter
def bs_widget(bound_field):
    """Render a form field's widget with Bootstrap classes and ARIA attributes."""
    widget = bound_field.field.widget
    if isinstance(widget, forms.CheckboxInput):
        css = "form-check-input"
    elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
        css = "form-select"
    else:
        css = "form-control"
    if bound_field.errors:
        css += " is-invalid"
    existing = widget.attrs.get("class", "")
    attrs = {"class": f"{existing} {css}".strip()}

    described_by = []
    if bound_field.errors:
        attrs["aria-invalid"] = "true"
        described_by.append(f"{bound_field.auto_id}_error")
    if bound_field.help_text:
        described_by.append(f"{bound_field.auto_id}_helptext")
    if described_by:
        attrs["aria-describedby"] = " ".join(described_by)
    return bound_field.as_widget(attrs=attrs)
