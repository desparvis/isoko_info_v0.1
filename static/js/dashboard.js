document.addEventListener('DOMContentLoaded', function() {
  // Handle active link for sidebar and bottom nav
  const navLinks = document.querySelectorAll('.sidebar-links a, .bottom-nav .nav-links a');
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      navLinks.forEach(l => l.classList.remove('active'));
      this.classList.add('active');
      const href = this.getAttribute('href');
      if (href && !href.startsWith('#')) {
        window.location.href = href;
      }
    });
  });

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