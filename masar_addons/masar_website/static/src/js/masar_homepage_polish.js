/* Small progressive enhancements for the public homepage only. */
(() => {
  const start = () => {
    const home = document.querySelector(".masar-pay:not(.masar-page)");
    if (!home) return;
    const closing = home.querySelector(".masar-closing__actions");
    const primary = closing?.querySelector(".masar-btn--primary");
    const secondary = closing?.querySelector(".masar-btn--ghost");
    if (primary && secondary && primary.href === secondary.href) secondary.hidden = true;
    home.querySelectorAll("[data-masar-carousel]").forEach(root => {
      const track = root.querySelector(".masar-service-grid");
      const cards = [...root.querySelectorAll(".masar-service-card")];
      const dots = root.querySelector(".masar-service-carousel__dots");
      if (!track || !dots || !cards.length) return;
      const label = () => {
        const controls = [...dots.querySelectorAll("button")];
        controls.forEach((button, index) => {
          const title = cards[index]?.querySelector(".masar-service-card__title")?.textContent.trim();
          if (title) button.setAttribute("aria-label", title);
        });
        return controls.length === cards.length;
      };
      if (!label()) {
        const observer = new MutationObserver(() => { if (label()) observer.disconnect(); });
        observer.observe(dots, {childList: true});
      }
      root.addEventListener("click", event => {
        if (!matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        const button = event.target.closest(".masar-service-carousel__nav,.masar-service-carousel__dot");
        if (!button || button.disabled) return;
        const midpoint = track.getBoundingClientRect().left + track.clientWidth / 2;
        const current = cards.reduce((best, card, index) => {
          const rect = card.getBoundingClientRect();
          const distance = Math.abs(rect.left + rect.width / 2 - midpoint);
          return distance < best.distance ? {index, distance} : best;
        }, {index: 0, distance: Infinity}).index;
        const controls = [...dots.querySelectorAll("button")];
        const index = button.classList.contains("masar-service-carousel__dot")
          ? controls.indexOf(button)
          : current + (button.classList.contains("masar-service-carousel__nav--next") ? 1 : -1);
        const card = cards[Math.max(0, Math.min(cards.length - 1, index))];
        const rect = card.getBoundingClientRect();
        event.preventDefault();
        event.stopImmediatePropagation();
        track.scrollBy({left: rect.left + rect.width / 2 - midpoint, behavior: "auto"});
      }, true);
    });
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, {once:true});
  else start();
})();
