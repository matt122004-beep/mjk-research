(function () {
  "use strict";

  var progress = document.querySelector("[data-cv-progress]");
  var indexLinks = Array.from(document.querySelectorAll(".dossier-index nav a[href^='#']"));
  var sections = indexLinks.map(function (link) {
    return document.querySelector(link.getAttribute("href"));
  }).filter(Boolean);
  var frame = 0;

  if (!progress && !sections.length) return;

  function update() {
    frame = 0;

    if (progress) {
      var root = document.documentElement;
      var available = Math.max(1,root.scrollHeight - window.innerHeight);
      var value = Math.min(1,Math.max(0,window.scrollY / available));
      progress.style.transform = "scaleX(" + value + ")";
    }

    if (sections.length) {
      var readingLine = window.innerHeight * .34;
      var active = sections[0];
      sections.forEach(function (section) {
        if (section.getBoundingClientRect().top <= readingLine) active = section;
      });

      indexLinks.forEach(function (link) {
        if (link.getAttribute("href") === "#" + active.id) {
          link.setAttribute("aria-current","location");
        } else {
          link.removeAttribute("aria-current");
        }
      });
    }
  }

  function schedule() {
    if (!frame) frame = window.requestAnimationFrame(update);
  }

  window.addEventListener("scroll",schedule,{ passive: true });
  window.addEventListener("resize",schedule);
  update();
})();
