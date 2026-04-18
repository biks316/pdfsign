document.addEventListener("DOMContentLoaded", () => {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.body.classList.add("js-ready");

  if (!prefersReducedMotion) {
    initRevealAnimations();
    initHeroTilt();
    initCardTilt();
  }
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
