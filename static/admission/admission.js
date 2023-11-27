$(function () {
    // Prevent to submit data from form inputs in disabled containers
    $('form').on('submit', function() {
        $(this).find('div[disabled] *').prop('disabled', true);
    })

    // Prevent to drop files except in file inputs
    $(document).on({
        drop: function(event) {
            if (event.originalEvent.dataTransfer.types.indexOf('Files') !== -1 && event.target.type !== 'file') {
                event.preventDefault();
            }
        },
        dragover: function(event) {
            // Ensure that the drop event will be called
            if (event.originalEvent.dataTransfer.types.indexOf('Files') !== -1 && event.target.type !== 'file') {
                event.preventDefault();
            }
        }
    });
})
