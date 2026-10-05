from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Skill',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('name', models.CharField(max_length=100, unique=True)),
                (
                    'normalized_name',
                    models.CharField(
                        editable=False,
                        max_length=100,
                        unique=True,
                    ),
                ),
                ('description', models.CharField(blank=True, default='', max_length=500)),
                ('category', models.CharField(blank=True, default='', max_length=80)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('name',),
                'indexes': [models.Index(fields=('category',), name='skill_category_idx')],
            },
        ),
    ]
