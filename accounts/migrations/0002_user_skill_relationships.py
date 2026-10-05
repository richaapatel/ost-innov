from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('skills', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='offered_skills',
            field=models.ManyToManyField(blank=True, related_name='teachers', to='skills.skill'),
        ),
        migrations.AddField(
            model_name='user',
            name='wanted_skills',
            field=models.ManyToManyField(blank=True, related_name='learners', to='skills.skill'),
        ),
    ]
