document.addEventListener("DOMContentLoaded", () => {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.body.classList.add("js-ready");

  if (!prefersReducedMotion) {
    initRevealAnimations();
    initHeroTilt();
    initCardTilt();
    initHomeOrbit();
    initMagneticButtons();
  }

  initGoogleSidePopup();
});

function initRevealAnimations() {
  const revealTargets = [
    ...document.querySelectorAll(".hero-card"),
    ...document.querySelectorAll(".section h2"),
    ...document.querySelectorAll(".tool-card"),
    ...document.querySelectorAll(".content-section"),
    ...document.querySelectorAll(".site-footer")
  ];

  revealTargets.forEach((el, idx) => {
    el.classList.add("reveal-item");
    el.style.setProperty("--reveal-delay", `${Math.min((idx % 8) * 50, 280)}ms`);
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.16, rootMargin: "0px 0px -10% 0px" }
  );

  revealTargets.forEach((el) => observer.observe(el));
}

function initHeroTilt() {
  const graphic = document.querySelector(".hero-graphic");
  if (!graphic) return;

  graphic.addEventListener("pointermove", (event) => {
    const bounds = graphic.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width - 0.5;
    const y = (event.clientY - bounds.top) / bounds.height - 0.5;
    graphic.style.transform = `translate3d(${x * 8}px, ${y * 8}px, 0)`;
  });

  graphic.addEventListener("pointerleave", () => {
    graphic.style.transform = "";
  });
}

function initCardTilt() {
  const cards = document.querySelectorAll(".tool-card");
  cards.forEach((card) => {
    card.addEventListener("pointermove", (event) => {
      const bounds = card.getBoundingClientRect();
      const relX = event.clientX - bounds.left;
      const relY = event.clientY - bounds.top;

      card.style.setProperty("--mx", `${(relX / bounds.width) * 100}%`);
      card.style.setProperty("--my", `${(relY / bounds.height) * 100}%`);

      const rotateY = ((relX / bounds.width) - 0.5) * 6;
      const rotateX = (0.5 - (relY / bounds.height)) * 6;
      card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-2px)`;
      card.classList.add("is-hovered");
    });

    card.addEventListener("pointerleave", () => {
      card.style.transform = "";
      card.classList.remove("is-hovered");
    });
  });
}

function initHomeOrbit() {
  const orbit = document.querySelector(".home-orbit");
  if (!orbit) return;

  orbit.addEventListener("pointermove", (event) => {
    const bounds = orbit.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width - 0.5;
    const y = (event.clientY - bounds.top) / bounds.height - 0.5;
    orbit.style.transform = `translate3d(${x * 6}px, ${y * 6}px, 0) scale(1.01)`;
  });

  orbit.addEventListener("pointerleave", () => {
    orbit.style.transform = "";
  });
}

function initMagneticButtons() {
  const buttons = document.querySelectorAll(".magnetic-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("pointermove", (event) => {
      const box = btn.getBoundingClientRect();
      const x = event.clientX - box.left - box.width / 2;
      const y = event.clientY - box.top - box.height / 2;
      btn.style.transform = `translate(${x * 0.08}px, ${y * 0.12}px)`;
    });

    btn.addEventListener("pointerleave", () => {
      btn.style.transform = "";
    });
  });
}

function initGoogleSidePopup() {
  const popup = document.querySelector("[data-google-popup]");
  if (!popup) return;

  const closeButton = popup.querySelector("[data-google-popup-close]");
  const key = "pdfsign_google_popup_closed_v1";
  const closedAt = Number(window.localStorage.getItem(key) || "0");
  const cooloffMs = 24 * 60 * 60 * 1000;

  if (Date.now() - closedAt < cooloffMs) {
    return;
  }

  popup.hidden = false;
  window.setTimeout(() => {
    popup.classList.add("is-visible");
  }, 450);

  closeButton?.addEventListener("click", () => {
    popup.classList.remove("is-visible");
    window.localStorage.setItem(key, String(Date.now()));
    window.setTimeout(() => {
      popup.hidden = true;
    }, 180);
  });
}
