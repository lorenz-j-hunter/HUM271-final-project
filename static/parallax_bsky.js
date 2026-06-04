startpoint = 50; 
endpoint = 100;

document.addEventListener('DOMContentLoaded', () => {
  const layers = [
    {
      el: document.querySelector(".parallax-bsky"),
      start: startpoint,
      end: endpoint,
      speed: 80  
    }
  ];

  ['scroll', 'DOMContentLoaded'].forEach(event => {
    window.addEventListener(event, () => {
      const y = window.scrollY;

      for (const layer of layers) {
        const { el, start, end, speed } = layer;
        console.log(`el=${el}`);

        if (y < start) {
          // FIXED MODE (before range)
          el.style.backgroundAttachment = "fixed";
          el.style.backgroundPositionY = `-${start}px`;
          continue;
        }

        if (y > end) {
          // FIXED MODE (after range)
          el.style.backgroundAttachment = "fixed";
          el.style.backgroundPositionY = `-${end}px`;
          continue;
        }

        // TRANSFORM MODE (between start and end)
        el.style.backgroundAttachment = "scroll";
        const progress = (y - start) / (end - start); // 0 → 1
        const offset = progress * speed;

        el.style.backgroundPositionY = `-${offset}px`;
      }
    })
  });
});

