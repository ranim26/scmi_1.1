// password-toggle.js
// Toggle password visibility for login page

document.addEventListener('DOMContentLoaded', function() {
    var toggleIcons = document.querySelectorAll('.toggle-password');
    toggleIcons.forEach(function(icon) {
        icon.addEventListener('click', function() {
            var input = document.getElementById(icon.getAttribute('data-target'));
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    });
});
