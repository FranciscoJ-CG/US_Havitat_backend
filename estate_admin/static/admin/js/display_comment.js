document.addEventListener('DOMContentLoaded', function() {
    window.toggleComment = function(element) {
        if (element.style.whiteSpace === 'normal') {
            element.style.whiteSpace = 'nowrap';
            element.style.overflow = 'hidden';
            element.style.textOverflow = 'ellipsis';
        } else {
            element.style.whiteSpace = 'normal';
            element.style.overflow = 'visible';
            element.style.textOverflow = 'clip';
        }
    };
});
