from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_user_skill_relationships'),
        ('skills', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Exchange',
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
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('pending', 'Pending'),
                            ('accepted', 'Accepted'),
                            ('rejected', 'Rejected'),
                            ('completed', 'Completed'),
                        ],
                        default='pending',
                        max_length=10,
                    ),
                ),
                ('message', models.CharField(blank=True, default='', max_length=500)),
                (
                    'active_request_key',
                    models.CharField(blank=True, max_length=310, null=True, unique=True),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'learner',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='sent_exchanges',
                        to='accounts.user',
                    ),
                ),
                (
                    'skill',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='exchanges',
                        to='skills.skill',
                    ),
                ),
                (
                    'teacher',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='received_exchanges',
                        to='accounts.user',
                    ),
                ),
            ],
            options={
                'indexes': [
                    models.Index(fields=('teacher', 'status'), name='exchange_teacher_status_idx'),
                    models.Index(fields=('learner', 'status'), name='exchange_learner_status_idx'),
                    models.Index(fields=('skill', 'status'), name='exchange_skill_status_idx'),
                    models.Index(fields=('created_at',), name='exchange_created_at_idx'),
                ],
                'constraints': [
                    models.CheckConstraint(
                        condition=~models.Q(teacher=models.F('learner')),
                        name='exchange_teacher_learner_diff',
                    ),
                ],
            },
        ),
    ]
