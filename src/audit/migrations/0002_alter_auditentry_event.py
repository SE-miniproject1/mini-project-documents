from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditentry",
            name="event",
            field=models.CharField(
                choices=[
                    ("unit_status", "Unit status change"),
                    ("login_success", "Sign-in"),
                    ("login_failure", "Failed sign-in"),
                    ("logout", "Sign-out"),
                    ("lockout", "Account locked"),
                    ("authz_failure", "Authorisation failure"),
                    ("config_change", "Configuration change"),
                    ("request_status", "Blood request status change"),
                    ("allocation", "Unit allocation or issue"),
                    ("location_transfer", "Unit location transfer"),
                ],
                db_index=True,
                max_length=20,
            ),
        ),
    ]
