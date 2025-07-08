document.addEventListener('DOMContentLoaded', function() {
  const navLinks = document.querySelectorAll('.navbar-links a, .cta-button');
  const hamburger = document.querySelector('.hamburger');
  const navbarLinks = document.querySelector('.navbar-links');
  const flashMessages = document.querySelector('.flash-messages');

  // Function to remove active class from all links
  function clearActiveClass() {
    navLinks.forEach(link => link.classList.remove('active'));
  }

  // Set active class based on current URL
function setActiveLink() {
  const currentPath = window.location.pathname;
  const currentHash = window.location.hash;

  clearActiveClass();

  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;

    const hrefPath = href.split('#')[0];
    const hrefHash = href.includes('#') ? `#${href.split('#')[1]}` : '';

    const isExactMatch = hrefPath === currentPath && hrefHash === currentHash;
    const isRootMatch = href === '/' && currentPath === '/' && !currentHash;
    const isCTAHashMatch =
      href === '/#about' &&
      link.classList.contains('cta-button') &&
      currentPath === '/' &&
      currentHash === '#about';

    if (isExactMatch || isRootMatch || isCTAHashMatch) {
      link.classList.add('active');
    }
  });
}


  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      const href = this.getAttribute('href');

      if (href.startsWith('/#') && window.location.pathname === '/') {
        e.preventDefault();
        clearActiveClass();
        if (this.classList.contains('navbar-links') || !this.classList.contains('cta-button')) {
          this.classList.add('active');
        }

        const targetId = href.split('#')[1];
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
          const navbarHeight = document.querySelector('.navbar').offsetHeight || 64;
          const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - navbarHeight;
          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });
        }
      } else {
        window.location.href = href;
      }

      navbarLinks.classList.remove('active');
      hamburger.querySelector('.material-icons').textContent = 'menu';
    });
  });

  // Toggle mobile menu
  hamburger.addEventListener('click', () => {
    navbarLinks.classList.toggle('active');
    hamburger.querySelector('.material-icons').textContent = navbarLinks.classList.contains('active') ? 'close' : 'menu';
  });

  // Set initial active link on page load
  setActiveLink();

  // Update active link on hash change
  window.addEventListener('hashchange', setActiveLink);

  // Close mobile menu when resizing to larger screens
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768 && navbarLinks.classList.contains('active')) {
      navbarLinks.classList.remove('active');
      hamburger.querySelector('.material-icons').textContent = 'menu';
    }
  });

  // Auto-dismiss flash messages after 5 seconds
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
  }
});