# Generated by Django 5.2.4 on 2025-07-06 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userAuth', '0007_remove_studentprofile_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacherprofile',
            name='gender',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
