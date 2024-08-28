document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('[data-currency-input]').forEach(inputField => {
        const formattedDisplay = document.getElementById(inputField.dataset.formattedDisplay);

        inputField.addEventListener('input', function(e) {
            let value = e.target.value.replace(/,/g, '');
            value = parseFloat(value.replace(/[^0-9.]/g, ''));
            if (!isNaN(value)) {
                formattedDisplay.value = `$ ${value.toLocaleString('en-US', {
                    style: 'decimal',
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 2
                })}`;
            } else {
                formattedDisplay.value = 'Invalid input';
            }
        });
    });
});