(function ($) {
    'use strict';

    function showSkillMessage(message, isError) {
        const $container = $('.site-messages');
        const alertClass = isError ? 'danger' : 'success';
        const $alert = $('<div>', {
            class: 'alert alert-' + alertClass + ' alert-dismissible fade show',
            role: 'alert'
        }).text(message);
        $('<button>', {
            type: 'button',
            class: 'btn-close',
            'data-bs-dismiss': 'alert',
            'aria-label': 'Close'
        }).appendTo($alert);
        $container.prepend($alert);
    }

    function setLoading($button, loading) {
        if (loading) {
            $button.data('original-html', $button.html());
            $button.prop('disabled', true).attr('aria-busy', 'true');
            $button.html('<span class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>Updating...');
        } else {
            $button.prop('disabled', false).removeAttr('aria-busy');
            $button.html($button.data('original-html'));
        }
    }

    function updateSummary(kind, skillId, skillName, selected) {
        const $list = $('[data-summary-list="' + kind + '"]');
        if (!$list.length) return;

        const selector = '[data-summary-skill-id="' + skillId + '"]';
        if (selected && !$list.find(selector).length) {
            const badgeClass = kind === 'wanted' ? 'skill-badge skill-badge-accent' : 'skill-badge';
            $('<span>', {
                class: badgeClass,
                'data-summary-skill-id': skillId,
                text: skillName
            }).appendTo($list);
        } else if (!selected) {
            $list.find(selector).remove();
        }

        const count = $list.find('[data-summary-skill-id]').length;
        $('[data-summary-count="' + kind + '"]').text(count);
        $list.find('[data-summary-empty]').toggleClass('d-none', count > 0);
        if (!count && !$list.find('[data-summary-empty]').length) {
            const text = kind === 'wanted' ? 'Nothing here yet — follow your curiosity.' : 'Nothing here yet — share what you know.';
            $('<span>', {
                class: 'summary-empty',
                'data-summary-empty': kind,
                text: text
            }).appendTo($list);
        }
    }

    function updateCard($card, data) {
        const kind = data.kind;
        const selected = data.selected;
        $card.find('[data-skill-action-form][data-kind="' + kind + '"]').each(function () {
            const $form = $(this);
            $form.toggleClass('d-none', (selected && $form.data('operation') === 'add') || (!selected && $form.data('operation') === 'remove'));
        });

        const $state = $card.find('[data-skill-state="' + kind + '"]');
        $state.empty();
        if (selected) {
            const label = kind === 'offered' ? 'You offer this' : 'You want to learn this';
            const badgeClass = kind === 'offered' ? 'skill-state-badge is-offered' : 'skill-state-badge is-wanted';
            $('<span>', { class: badgeClass }).append($('<i>', { class: 'bi bi-check2' })).append(document.createTextNode(label)).appendTo($state);
        }
        updateSummary(kind, data.skill_id, data.skill_name, selected);
    }

    $(document).on('submit', '[data-skill-action-form]', function (event) {
        event.preventDefault();
        const $form = $(this);
        const $button = $form.find('button[type="submit"]');
        if ($button.prop('disabled')) return;

        setLoading($button, true);
        $.ajax({
            url: $form.attr('action'),
            type: 'POST',
            data: $form.serialize(),
            dataType: 'json',
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        }).done(function (response) {
            if (response.ok) {
                updateCard($form.closest('[data-skill-card]'), response.data);
                showSkillMessage(response.message, false);
            } else {
                showSkillMessage(response.message || 'Unable to update this skill.', true);
            }
        }).fail(function (xhr) {
            const response = xhr.responseJSON || {};
            showSkillMessage(response.message || 'Unable to update this skill right now.', true);
        }).always(function () {
            setLoading($button, false);
        });
    });
}(window.jQuery));
