endpoint = 1000

const layers = [
  {
    el: document.querySelector(".parallax-bg"),
    start: 0,
    end: endpoint,
    speed: 80   // slowest
  }
];

window.addEventListener("scroll", () => {
  const y = window.scrollY;

  for (const layer of layers) {
    const { el, start, end, speed } = layer;

    if (y < start) {
      // FIXED MODE (before range)
      el.style.backgroundAttachment = "fixed";
      el.style.backgroundPositionY = "center";
      continue;
    }

    if (y > end) {
      // FIXED MODE (after range)
      el.style.backgroundAttachment = "fixed";
      el.style.marginTop = `${end}px`;
      el.style.backgroundPositionY = "center";
      continue;
    }

    // TRANSFORM MODE (between start and end)
    el.style.backgroundAttachment = "scroll";

    const progress = (y - start) / (end - start); // 0 → 1
    const offset = progress * speed;

    el.style.backgroundPositionY = `-${offset}px`;
  }
});