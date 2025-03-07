document.addEventListener('DOMContentLoaded', () => {
    ['table-form', 'ps-room-form', 'order-form'].forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                });
                const result = await response.json();
                alert(result.message || result.error);
            });
        }
    });
});