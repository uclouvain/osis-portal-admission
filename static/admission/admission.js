$(function () {
    const is_letter = character => RegExp(/(\p{L})/, 'u').test(character);

    // Format some fields
    $(".formatted-field input").on('input', function () {
        const splittedString = Array.from(this.value);
        let hasChanged = false;

        for (let i = 0; i < splittedString.length - 1; i++) {
            if (is_letter(splittedString[i]) && is_letter(splittedString[i + 1])) {
                splittedString[i + 1] = splittedString[i + 1].toLowerCase();
                hasChanged = true;
            }
        }
        if (hasChanged) {
            const previousCursorPosition = this.selectionEnd;
            this.value = splittedString.join('');
            this.selectionEnd = previousCursorPosition;
        }
    });
})