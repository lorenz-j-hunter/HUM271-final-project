const layers = [
  {
    el: document.getElementById("parallax-bg"),
    start: 100,
    end: 600,
    speed: 80   // slowest
  },
  {
    el: document.getElementById("parallax-mid"),
    start: 150,
    end: 650,
    speed: 140  // medium
  },
  {
    el: document.getElementById("parallax-fg"),
    start: 200,
    end: 700,
    speed: 220  // fastest
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
