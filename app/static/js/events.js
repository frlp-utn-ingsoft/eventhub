document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("eventForm");

    // Lógica de validación del formulario
    if (form) {
        const titleField = form.querySelector("[name='title']");
        const dateField = form.querySelector("[name='date']");
        const submitButton = form.querySelector("[type='submit']");

        // Función para verificar si los campos son válidos
        const validateForm = () => {
            const title = titleField.value.trim();
            const date = dateField.value;

            let isValid = true;

            // Validar título
            if (!title) {
                showError(titleField, "Por favor ingrese un título.");
                isValid = false;
            } else {
                clearError(titleField);
            }

            // Validar fecha
            if (!date) {
                showError(dateField, "Por favor ingrese una fecha.");
                isValid = false;
            } else {
                clearError(dateField);
            }

            // Activar o desactivar el botón de envío según la validez del formulario
            submitButton.disabled = !isValid;

            return isValid;
        };

        // Mostrar el mensaje de error debajo de un campo
        const showError = (field, message) => {
            let error = field.nextElementSibling;
            if (!error || !error.classList.contains("error-message")) {
                error = document.createElement("div");
                error.classList.add("error-message");
                field.parentNode.appendChild(error);
            }
            error.textContent = message;
            field.classList.add("is-invalid");
        };

        // Limpiar el mensaje de error y el estado de error de un campo
        const clearError = (field) => {
            let error = field.nextElementSibling;
            if (error && error.classList.contains("error-message")) {
                error.remove();
            }
            field.classList.remove("is-invalid");
        };

        // Validar al enviar el formulario
        form.addEventListener("submit", (e) => {
            if (!validateForm()) {
                e.preventDefault(); // Prevenir el envío si no es válido
            }
        });

        // Validar en tiempo real al cambiar los campos
        titleField.addEventListener("input", validateForm);
        dateField.addEventListener("input", validateForm);

        // Deshabilitar el botón de envío si el formulario es inválido
        validateForm(); // Verificar el estado inicial del formulario
    }

    // ############################ Lógica de calificación con estrellas ############################
    const starContainer = document.getElementById('star-rating');
    const stars = starContainer.querySelectorAll('.star');
    let currentRating = parseInt(starContainer.dataset.ratingCurrent) || 0;
    paintStars(currentRating); // <- Esto pinta las estrellas al cargar la página
    
    function paintStars(rating) {
        stars.forEach(star => {
            const starValue = parseInt(star.dataset.value);
            const icon = star.querySelector('i');
            if (starValue <= rating) {
                icon.classList.remove('bi-star');
                icon.classList.add('bi-star-fill');
            } else {
                icon.classList.remove('bi-star-fill');
                icon.classList.add('bi-star');
            }
        });
    }

    stars.forEach(star => {
        star.addEventListener('mouseenter', () => {
            const hoverValue = parseInt(star.dataset.value);
            paintStars(hoverValue);
        });

        star.addEventListener('click', () => {
            const selectedValue = parseInt(star.dataset.value);
            currentRating = selectedValue;
            starContainer.dataset.ratingCurrent = selectedValue;
            document.getElementById(`star${selectedValue}`).checked = true;
        });
    });

    starContainer.addEventListener('mouseleave', () => {
        paintStars(currentRating);
    });
});