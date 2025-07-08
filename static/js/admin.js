document.addEventListener('DOMContentLoaded', function() {
  // Auto-dismiss flash messages after 5 seconds and handle close button
  const flashMessages = document.querySelector('.flash-messages');
  if (flashMessages) {
    const flashItems = flashMessages.querySelectorAll('.form-error, .form-success');
    flashItems.forEach(item => {
      setTimeout(() => {
        item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        item.style.opacity = '0';
        item.style.transform = 'translateY(-10px)';
        setTimeout(() => {
          item.remove();
          if (!flashMessages.children.length) {
            flashMessages.remove();
          }
        }, 500);
      }, 5000);
    });

    flashMessages.addEventListener('click', (e) => {
      if (e.target.classList.contains('close-btn')) {
        const item = e.target.closest('.form-error, .form-success');
        if (item) {
          item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
          item.style.opacity = '0';
          item.style.transform = 'translateY(-10px)';
          setTimeout(() => {
            item.remove();
            if (!flashMessages.children.length) {
              flashMessages.remove();
            }
          }, 300);
        }
      }
    });
  }
});