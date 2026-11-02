from django.db import migrations

# A starting list for the blood bank to review and adjust (SRS REQ-5, REQ-46). The figures
# for temporary conditions are common practice, not taken from the SRS.
PERMANENT = [
    "HIV positive",
    "Hepatitis B or C",
    "Heart disease",
    "Epilepsy",
    "Cancer",
    "Bleeding disorder",
    "Uses injected drugs",
]
TEMPORARY = [
    ("Fever or infection in the last 2 weeks", 14),
    ("Taking antibiotics", 14),
    ("Vaccination in the last 4 weeks", 28),
    ("Surgery in the last 6 months", 180),
    ("Tattoo or piercing in the last 6 months", 180),
    ("Pregnant or gave birth in the last 6 months", 180),
]


def add_conditions(apps, schema_editor):
    condition_model = apps.get_model("donors", "DeferralCondition")
    order = 0
    for name in PERMANENT:
        order += 1
        condition_model.objects.get_or_create(
            name=name, defaults={"kind": "permanent", "deferral_days": None, "sort_order": order}
        )
    for name, days in TEMPORARY:
        order += 1
        condition_model.objects.get_or_create(
            name=name, defaults={"kind": "temporary", "deferral_days": days, "sort_order": order}
        )


def remove_conditions(apps, schema_editor):
    names = PERMANENT + [name for name, _ in TEMPORARY]
    apps.get_model("donors", "DeferralCondition").objects.filter(name__in=names).delete()


class Migration(migrations.Migration):
    dependencies = [("donors", "0003_deferral_conditions")]
    operations = [migrations.RunPython(add_conditions, remove_conditions)]
