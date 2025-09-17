document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.querySelector('.mobile-menu');
    const navLinks = document.querySelector('.nav-links');
  
    if(mobileMenuBtn && navLinks) {
      mobileMenuBtn.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        const icon = mobileMenuBtn.querySelector('i');
        if (navLinks.classList.contains('active')) {
          icon.className = 'ri-close-line';
          mobileMenuBtn.setAttribute('aria-expanded', 'true');
        } else {
          icon.className = 'ri-menu-line';
          mobileMenuBtn.setAttribute('aria-expanded', 'false');
        }
      });
  

      document.addEventListener('click', (e) => {
        if (!e.target.closest('.nav-links') && !e.target.closest('.mobile-menu') && navLinks.classList.contains('active')) {
          navLinks.classList.remove('active');
          mobileMenuBtn.querySelector('i').className = 'ri-menu-line';
          mobileMenuBtn.setAttribute('aria-expanded', 'false');
        }
      });
    }
  });
  