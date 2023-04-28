$(function () {
    // Prevent to submit data from form inputs in disabled containers
    $('form').on('submit', function() {
        $(this).find('div[disabled] *').prop('disabled', true);
    })
})
