(function ($) {
    'use strict';

    function csrfHeader(xhr) {
        const token = $('#exchange-request-form input[name="csrfmiddlewaretoken"]').val();
        if (token) {
            xhr.setRequestHeader('X-CSRFToken', token);
        }
    }

    function clearRequestState() {
        const form = $('#exchange-request-form');
        if (!form.length) return;
        form[0].reset();
        $('#exchange-teacher-id').val('');
        $('#exchange-skill-id').html('<option value="">Choose a skill</option>').removeClass('is-invalid');
        $('#exchange-message').removeClass('is-invalid');
        $('#exchange-skill-error, #exchange-message-error').text('');
        $('#exchange-request-general-error, #exchange-request-success').addClass('d-none').text('');
        $('#exchange-request-submit').prop('disabled', false);
        $('.exchange-submit-label').removeClass('d-none');
        $('.exchange-submit-loading').addClass('d-none');
        $('#exchange-message-count').text('0 / 500');
    }

    function setFieldErrors(errors) {
        Object.keys(errors || {}).forEach(function (field) {
            const message = (errors[field] || []).join(' ');
            if (field === 'skill_id') {
                $('#exchange-skill-id').addClass('is-invalid');
                $('#exchange-skill-error').text(message);
            } else if (field === 'message') {
                $('#exchange-message').addClass('is-invalid');
                $('#exchange-message-error').text(message);
            } else {
                $('#exchange-request-general-error').removeClass('d-none').text(message);
            }
        });
    }

    $(function () {
        const modalElement = document.getElementById('exchangeRequestModal');
        if (!modalElement) return;

        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

        $(document).on('click', '[data-request-to-learn]', function (event) {
            event.preventDefault();
            clearRequestState();
            const trigger = $(this);
            let skills = [];
            try {
                skills = JSON.parse(trigger.attr('data-skills') || '[]');
            } catch (error) {
                skills = [];
            }
            $('#exchangeRequestModalLabel').text('Request to Learn from ' + trigger.attr('data-teacher-name'));
            $('#exchange-teacher-id').val(trigger.attr('data-teacher-id'));
            const select = $('#exchange-skill-id');
            skills.forEach(function (skill) {
                $('<option>', { value: skill.id, text: skill.name }).appendTo(select);
            });
            const preferred = trigger.attr('data-preferred-skill');
            if (preferred && select.find('option[value="' + preferred + '"]').length) {
                select.val(preferred);
            }
            modal.show();
        });

        $('#exchange-message').on('input', function () {
            $('#exchange-message-count').text($(this).val().length + ' / 500');
        });

        $('#exchange-request-form').on('submit', function (event) {
            event.preventDefault();
            const form = $(this);
            const submit = $('#exchange-request-submit');
            $('#exchange-request-general-error, #exchange-request-success').addClass('d-none').text('');
            $('#exchange-skill-id, #exchange-message').removeClass('is-invalid');
            $('#exchange-skill-error, #exchange-message-error').text('');
            submit.prop('disabled', true);
            $('.exchange-submit-label').addClass('d-none');
            $('.exchange-submit-loading').removeClass('d-none');

            $.ajax({
                url: form.attr('action'),
                method: 'POST',
                data: form.serialize(),
                beforeSend: csrfHeader,
            }).done(function (response) {
                $('#exchange-request-success').removeClass('d-none').text(response.message || 'Learning request sent successfully.');
                $('.exchange-submit-label').text('Request sent').removeClass('d-none');
                $('.exchange-submit-loading').addClass('d-none');
                submit.prop('disabled', false);
            }).fail(function (xhr) {
                const response = xhr.responseJSON || {};
                $('#exchange-request-general-error').removeClass('d-none').text(response.message || 'We could not send that request. Please try again.');
                setFieldErrors(response.errors || {});
                submit.prop('disabled', false);
                $('.exchange-submit-label').removeClass('d-none');
                $('.exchange-submit-loading').addClass('d-none');
            });
        });

        $(modalElement).on('hide.bs.modal', function (event) {
            if ($('#exchange-request-submit').prop('disabled')) {
                event.preventDefault();
            }
        });
        $(modalElement).on('hidden.bs.modal', clearRequestState);

        $(document).on('submit', '[data-exchange-status-form]', function (event) {
            event.preventDefault();
            const form = $(this);
            const button = form.find('button[type="submit"]');
            button.prop('disabled', true).prepend('<span class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>');
            $.ajax({
                url: form.attr('action'),
                method: 'POST',
                data: form.serialize(),
                beforeSend: function (xhr) {
                    const token = form.find('input[name="csrfmiddlewaretoken"]').val();
                    if (token) xhr.setRequestHeader('X-CSRFToken', token);
                },
            }).done(function () {
                window.location.reload();
            }).fail(function (xhr) {
                button.prop('disabled', false).find('.spinner-border').remove();
                const message = (xhr.responseJSON && xhr.responseJSON.message) || 'The exchange could not be updated.';
                $('<div class="alert alert-danger mt-3" role="alert"></div>').text(message).insertAfter(form);
            });
        });
    });
}(jQuery));
