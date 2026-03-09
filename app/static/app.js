// Small UI helpers
(() => {
  const navbar = document.querySelector(".navbar");
  const onScroll = () => {
    if (!navbar) return;
    const scrolled = window.scrollY > 8;
    navbar.classList.toggle("shadow", scrolled);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Auto-dismiss alerts after 4.5s (keep errors visible a bit longer)
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((el) => {
    const isDanger = el.classList.contains("alert-danger");
    const timeout = isDanger ? 7000 : 4500;
    window.setTimeout(() => {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
        bsAlert.close();
      } catch {
        el.remove();
      }
    }, timeout);
  });
})();
