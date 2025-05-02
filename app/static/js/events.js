document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("eventForm");

    // Validación de formulario de evento
    if (form) {
        const titleField = form.querySelector("[name='title']");
        const dateField = form.querySelector("[name='date']");
        const submitButton = form.querySelector("[type='submit']");

        const validateForm = () => {
            const title = titleField.value.trim();
            const date = dateField.value;

            let isValid = true;

            if (!title) {
                showError(titleField, "Por favor ingrese un título.");
                isValid = false;
            } else {
                clearError(titleField);
            }

            if (!date) {
                showError(dateField, "Por favor ingrese una fecha.");
                isValid = false;
            } else {
                clearError(dateField);
            }

            submitButton.disabled = !isValid;
            return isValid;
        };

        const showError = (field, message) => {
            let error = field.nextElementSibling;
            if (!error || !error.classList.contains("error-message")) {
                error = document.createElement("div");
                error.classList.add("error-message");
                field.parentNode.appendChild(error);
            }
            error.textContent = message;
            field.classList.add("is-invalid");

            // Mostrar SweetAlert cuando hay error
            Swal.fire({
                icon: 'error',
                title: 'Oops...',
                text: message,
            });
        };

        const clearError = (field) => {
            let error = field.nextElementSibling;
            if (error && error.classList.contains("error-message")) {
                error.remove();
            }
            field.classList.remove("is-invalid");
        };

        form.addEventListener("submit", (e) => {
            if (!validateForm()) {
                e.preventDefault();
            }
        });

        titleField.addEventListener("input", validateForm);
        dateField.addEventListener("input", validateForm);

        validateForm();
    }

    // ############################ Lógica de calificación con estrellas ############################
    const starContainer = document.getElementById('star-rating');
    if (starContainer) {
        const stars = starContainer.querySelectorAll('.star');
        let currentRating = parseInt(starContainer.dataset.ratingCurrent) || 0;
        paintStars(currentRating);

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
    }

    // Mostrar alerta de éxito tras enviar el formulario de calificación
    const ratingForms = document.querySelectorAll("#rating-form");
    ratingForms.forEach(form => {
        form.addEventListener("submit", (event) => {
            // Verifica si el usuario es su primera calificación
            const isFirstRating = form.dataset.firstRating === "true";

            // Si es la primera calificación, mostrar la alerta
            if (isFirstRating) {
                Swal.fire({
                    icon: 'success',
                    title: '¡Gracias por tu calificación!',
                    showConfirmButton: false, // No se muestra el botón de confirmación
                    timer: 1000 // La alerta se cerrará automáticamente después de 3 segundos
                }).then(() => {
                    // Después de que la alerta se cierre, enviar el formulario
                    form.submit();
                });
            } else {
                // Si no es la primera calificación, simplemente envía el formulario sin alerta
                form.submit();
            }

            // Prevenir el envío del formulario hasta que se cierre la alerta
            event.preventDefault();
        });
    });

    // Confirmación con SweetAlert al eliminar calificación
    const deleteButtons = document.querySelectorAll(".delete-rating-btn");

    deleteButtons.forEach(button => {
        button.addEventListener("click", (e) => {
            e.preventDefault();
            const url = button.dataset.url;

            Swal.fire({
                title: '¿Estás seguro?',
                text: "Esta acción eliminará la calificación.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Redirige a la URL de eliminación
                    window.location.href = url;
                }
            });
        });
    });
});