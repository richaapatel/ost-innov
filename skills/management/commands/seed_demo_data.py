from django.core.management.base import BaseCommand

from accounts.models import User
from exchanges.models import Exchange
from exchanges.services import change_exchange_status, create_exchange_request
from skills.models import Skill


DEMO_PASSWORD = 'SkillSwapDemoOnly123!'

SKILLS = (
    ('Python', 'Technology', 'Backend programming and automation.'),
    ('Java', 'Technology', 'Object-oriented application development.'),
    ('JavaScript', 'Technology', 'Programming for web applications.'),
    ('React', 'Technology', 'Component-based frontend development.'),
    ('UI/UX Design', 'Design', 'User interface and user experience design.'),
    ('Graphic Design', 'Design', 'Visual communication and digital graphics.'),
    ('Public Speaking', 'Communication', 'Confident and effective presentations.'),
    ('Digital Marketing', 'Business', 'Online marketing strategy and campaigns.'),
    ('Spanish', 'Languages', 'Conversational Spanish language practice.'),
    ('Guitar', 'Music', 'Acoustic and electric guitar fundamentals.'),
)

USERS = (
    ('alice@example.com', 'Alice Johnson', ('Python', 'Public Speaking'), ('Spanish', 'Guitar')),
    ('bob@example.com', 'Bob Smith', ('Spanish', 'Guitar'), ('Python', 'UI/UX Design')),
    ('carlos@example.com', 'Carlos Garcia', ('Guitar', 'JavaScript'), ('Public Speaking', 'Spanish')),
    ('diana@example.com', 'Diana Patel', ('UI/UX Design', 'Graphic Design'), ('React', 'Guitar')),
    ('elena@example.com', 'Elena Rossi', ('Digital Marketing', 'Spanish'), ('Java', 'Graphic Design')),
    ('frank@example.com', 'Frank Williams', ('Java', 'React', 'Spanish'), ('Digital Marketing', 'Python')),
)

EXCHANGES = (
    ('bob@example.com', 'alice@example.com', 'Python', 'Please help me build a small Python project.', Exchange.Status.PENDING),
    ('carlos@example.com', 'diana@example.com', 'UI/UX Design', 'I would like feedback on my mobile app wireframes.', Exchange.Status.ACCEPTED),
    ('elena@example.com', 'frank@example.com', 'Spanish', 'I am looking for conversational Spanish practice.', Exchange.Status.REJECTED),
    ('alice@example.com', 'carlos@example.com', 'Guitar', 'I can trade public speaking practice for guitar lessons.', Exchange.Status.COMPLETED),
)


class Command(BaseCommand):
    help = 'Create or update the local development demo dataset without duplicating records.'

    def handle(self, *args, **options):
        skill_map = {}
        new_skills = 0
        for name, category, description in SKILLS:
            skill, created = Skill.objects.get_or_create(
                name=name,
                defaults={'category': category, 'description': description},
            )
            skill_map[name] = skill
            new_skills += int(created)

        user_map = {}
        new_users = 0
        for email, name, offered, wanted in USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'name': name},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=('password',))
                new_users += 1
            user.offered_skills.set([skill_map[item] for item in offered])
            user.wanted_skills.set([skill_map[item] for item in wanted])
            user_map[email] = user

        new_exchanges = 0
        for learner_email, teacher_email, skill_name, message, target_status in EXCHANGES:
            learner = user_map[learner_email]
            teacher = user_map[teacher_email]
            skill = skill_map[skill_name]
            exchange = Exchange.objects.filter(
                learner=learner,
                teacher=teacher,
                skill=skill,
                message=message,
            ).first()
            if exchange is None:
                exchange = create_exchange_request(
                    learner=learner,
                    teacher_id=teacher.pk,
                    skill_id=skill.pk,
                    message=message,
                )
                new_exchanges += 1

            if exchange.status == Exchange.Status.PENDING and target_status == Exchange.Status.ACCEPTED:
                change_exchange_status(exchange=exchange, actor=teacher, action=Exchange.Status.ACCEPTED)
            elif exchange.status == Exchange.Status.PENDING and target_status == Exchange.Status.REJECTED:
                change_exchange_status(exchange=exchange, actor=teacher, action=Exchange.Status.REJECTED)
            elif exchange.status == Exchange.Status.PENDING and target_status == Exchange.Status.COMPLETED:
                accepted = change_exchange_status(
                    exchange=exchange,
                    actor=teacher,
                    action=Exchange.Status.ACCEPTED,
                )
                change_exchange_status(
                    exchange=accepted,
                    actor=learner,
                    action=Exchange.Status.COMPLETED,
                )

        self.stdout.write(self.style.SUCCESS(
            f'Demo data ready: {len(user_map)} users, {len(skill_map)} skills, '
            f'{Exchange.objects.count()} exchanges '
            f'({new_users} users, {new_skills} skills, {new_exchanges} exchanges created this run).'
        ))
