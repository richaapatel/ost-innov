(function ($) {
    'use strict';

    $('.discover-filter-card form').on('submit', function () {
        const $button = $(this).find('button[type="submit"]');
        if ($button.length) {
            $button.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span class="visually-hidden">Loading</span>');
        }
    });
}(window.jQuery));
