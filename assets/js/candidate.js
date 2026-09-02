(function () {
  "use strict";

  var menus = document.querySelectorAll(".candidate-menu");
  menus.forEach(function (menu) {
    var summary = menu.querySelector("summary");

    menu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        menu.removeAttribute("open");
      });
    });

    document.addEventListener("click", function (event) {
      if (menu.hasAttribute("open") && !menu.contains(event.target)) {
        menu.removeAttribute("open");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && menu.hasAttribute("open")) {
        menu.removeAttribute("open");
        if (summary) summary.focus();
      }
    });
  });

  var accordions = document.querySelectorAll("[data-study-accordion]");
  var desktopStory = window.matchMedia("(min-width: 901px)");

  accordions.forEach(function (accordion) {
    var studies = Array.from(accordion.querySelectorAll(".candidate-study"));
    var activeStudy = studies.find(function (study) {
      return study.classList.contains("is-open");
    }) || studies[0];
    var scrollFrame = 0;

    function setStudy(study, open) {
      var trigger = study.querySelector(".candidate-study-trigger");
      var panel = study.querySelector(".candidate-study-panel");
      var toggleLabel = study.querySelector(".candidate-study-toggle span");
      if (!trigger || !panel) return;

      if (open) {
        study.classList.add("is-open", "is-visible");
        trigger.setAttribute("aria-expanded", "true");
        panel.setAttribute("aria-hidden", "false");
        panel.removeAttribute("inert");
        if (toggleLabel) toggleLabel.textContent = "Current study";
      } else {
        study.classList.remove("is-visible", "is-open");
        trigger.setAttribute("aria-expanded", "false");
        panel.setAttribute("aria-hidden", "true");
        panel.setAttribute("inert", "");
        if (toggleLabel) toggleLabel.textContent = "View study";
      }
    }

    function openStudy(study) {
      if (!study || study === activeStudy) return;
      studies.forEach(function (candidate) {
        setStudy(candidate, candidate === study);
      });
      activeStudy = study;
    }

    studies.forEach(function (study) {
      var trigger = study.querySelector(".candidate-study-trigger");
      if (!trigger) return;

      trigger.addEventListener("click", function () {
        if (desktopStory.matches) {
          openStudy(study);
        } else {
          setStudy(study, !study.classList.contains("is-open"));
        }
      });
    });

    function studyAtReadingLine() {
      var line = window.innerHeight * 0.58;
      var accordionBox = accordion.getBoundingClientRect();
      if (accordionBox.top > line) return studies[0];
      if (accordionBox.bottom < line) return studies[studies.length - 1];

      var candidate = studies[0];
      studies.forEach(function (study) {
        var trigger = study.querySelector(".candidate-study-trigger");
        if (!trigger) return;
        var box = trigger.getBoundingClientRect();
        if (box.top + box.height * 0.5 <= line) candidate = study;
      });
      return candidate;
    }

    function updateStudyFromScroll() {
      scrollFrame = 0;
      if (!desktopStory.matches) return;
      if (accordion.contains(document.activeElement) && !document.activeElement.classList.contains("candidate-study-trigger")) return;

      var nextStudy = studyAtReadingLine();
      if (!nextStudy || nextStudy === activeStudy) return;
      openStudy(nextStudy);
    }

    function applyStoryMode() {
      if (desktopStory.matches) {
        studies.forEach(function (study) {
          setStudy(study, study === activeStudy);
        });
        updateStudyFromScroll();
      } else {
        studies.forEach(function (study) {
          setStudy(study, true);
        });
      }
    }

    window.addEventListener("scroll", function () {
      if (desktopStory.matches && !scrollFrame) scrollFrame = requestAnimationFrame(updateStudyFromScroll);
    }, { passive: true });

    window.addEventListener("resize", function () {
      updateStudyFromScroll();
    });

    if (desktopStory.addEventListener) {
      desktopStory.addEventListener("change", applyStoryMode);
    } else {
      desktopStory.addListener(applyStoryMode);
    }

    applyStoryMode();
  });

  function setupObservatory() {
    var story = document.querySelector("[data-observatory-story]");
    var observatory = document.querySelector("[data-observatory]");
    var canvas = document.querySelector("[data-observatory-canvas]");
    if (!story || !observatory || !canvas) return;

    var context = canvas.getContext("2d");
    if (!context) return;

    var field = canvas.parentElement;
    var steps = Array.from(story.querySelectorAll("[data-observatory-step]"));
    var panels = Array.from(observatory.querySelectorAll("[data-observatory-panel]"));
    var indexLabel = observatory.querySelector("[data-observatory-index]");
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
    var isStatic = document.documentElement.classList.contains("static");
    var nodes = [];
    var layouts = [[],[],[],[]];
    var currentStage = -1;
    var stageValue = 0;
    var targetStage = 0;
    var active = true;
    var frame = 0;
    var scrollFrame = 0;
    var width = 0;
    var height = 0;
    var ratio = 1;
    var pointer = { x: 0, y: 0, active: false };
    var palette = { ink: "#f4f2ec", muted: "#8f8c85", accent: "#e89275" };

    function seeded(index) {
      var value = Math.sin(index * 9283.31 + 17.17) * 43758.5453;
      return value - Math.floor(value);
    }

    for (var i = 0; i < 64; i += 1) {
      nodes.push({
        x: 0,
        y: 0,
        size: 1.15 + seeded(i + 70) * 2.05,
        phase: seeded(i + 130) * Math.PI * 2,
        messageLength: 5 + seeded(i + 190) * 11,
        accent: i % 9 === 0 || i % 13 === 0
      });
    }

    function updatePalette() {
      var styles = getComputedStyle(document.documentElement);
      palette.accent = styles.getPropertyValue("--candidate-inverse-accent").trim() || "#e89275";
    }

    function makeLayouts() {
      layouts = [[],[],[],[]];
      var usableHeight = Math.max(180,height * .62);

      nodes.forEach(function (_, index) {
        var scatterX = width * (.08 + seeded(index + 1) * .84);
        var scatterY = height * .07 + seeded(index + 20) * usableHeight;
        layouts[0].push({ x: scatterX, y: scatterY });

        var ring = index % 4;
        var angle = (index / nodes.length) * Math.PI * 2 * 3.1 + seeded(index + 4) * .38;
        var radiusX = width * (.095 + ring * .044);
        var radiusY = height * (.09 + ring * .041);
        layouts[1].push({
          x: width * .5 + Math.cos(angle) * radiusX,
          y: height * .34 + Math.sin(angle) * radiusY
        });

        var column = index % 3;
        var row = Math.floor(index / 3);
        var rows = Math.ceil(nodes.length / 3);
        layouts[2].push({
          x: width * (.2 + column * .3) + (seeded(index + 31) - .5) * width * .055,
          y: height * (.13 + (row / Math.max(1,rows - 1)) * .45) + (seeded(index + 51) - .5) * 9
        });

        var cluster = index % 4;
        var centers = [
          { x: .25, y: .2 }, { x: .75, y: .2 },
          { x: .25, y: .49 }, { x: .75, y: .49 }
        ];
        var clusterAngle = seeded(index + 80) * Math.PI * 2;
        var clusterRadius = Math.sqrt(seeded(index + 100)) * Math.min(width,height) * .105;
        layouts[3].push({
          x: width * centers[cluster].x + Math.cos(clusterAngle) * clusterRadius,
          y: height * centers[cluster].y + Math.sin(clusterAngle) * clusterRadius
        });
      });

      nodes.forEach(function (node, index) {
        if (!node.x && !node.y) {
          node.x = layouts[0][index].x;
          node.y = layouts[0][index].y;
        }
      });
    }

    function resize() {
      var box = field.getBoundingClientRect();
      width = Math.max(1,box.width);
      height = Math.max(1,box.height);
      ratio = Math.min(window.devicePixelRatio || 1,1.5);
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
      context.setTransform(ratio,0,0,ratio,0,0);
      updatePalette();
      makeLayouts();
      if (reduce.matches || isStatic) {
        nodes.forEach(function (node,index) {
          var desired = desiredPosition(index,stageValue);
          node.x = desired.x;
          node.y = desired.y;
        });
      }
      draw(performance.now());
    }

    function mix(a,b,amount) {
      return a + (b - a) * amount;
    }

    function desiredPosition(index,value) {
      var lower = Math.max(0,Math.min(3,Math.floor(value)));
      var upper = Math.max(0,Math.min(3,Math.ceil(value)));
      var amount = value - lower;
      return {
        x: mix(layouts[lower][index].x,layouts[upper][index].x,amount),
        y: mix(layouts[lower][index].y,layouts[upper][index].y,amount)
      };
    }

    function rgba(hex,alpha) {
      var clean = hex.replace("#","");
      if (clean.length === 3) clean = clean.split("").map(function (value) { return value + value; }).join("");
      var number = parseInt(clean,16);
      return "rgba(" + ((number >> 16) & 255) + "," + ((number >> 8) & 255) + "," + (number & 255) + "," + alpha + ")";
    }

    function drawGuides(value) {
      var attractorStrength = Math.max(0,1 - Math.abs(value - 1));
      if (attractorStrength > .01) {
        context.save();
        context.strokeStyle = rgba(palette.accent,.16 * attractorStrength);
        context.lineWidth = 1;
        [0.095,0.16,0.225].forEach(function (radius) {
          context.beginPath();
          context.ellipse(width * .5,height * .34,width * radius,height * radius * .82,0,0,Math.PI * 2);
          context.stroke();
        });
        context.restore();
      }

      var traceStrength = Math.max(0,1 - Math.abs(value - 2));
      if (traceStrength > .01) {
        context.save();
        context.lineWidth = .8;
        for (var row = 0; row < 18; row += 1) {
          var a = nodes[row * 3];
          var b = nodes[row * 3 + 1];
          var c = nodes[row * 3 + 2];
          if (!a || !b || !c) continue;
          context.strokeStyle = rgba(row % 6 === 0 ? palette.accent : palette.ink,(row % 6 === 0 ? .32 : .105) * traceStrength);
          context.beginPath();
          context.moveTo(a.x,a.y);
          context.bezierCurveTo(mix(a.x,b.x,.55),a.y,mix(a.x,b.x,.45),b.y,b.x,b.y);
          context.bezierCurveTo(mix(b.x,c.x,.55),b.y,mix(b.x,c.x,.45),c.y,c.x,c.y);
          context.stroke();
        }
        context.restore();
      }

      var clusterStrength = Math.max(0,value - 2);
      if (clusterStrength > .01) {
        context.save();
        context.strokeStyle = rgba(palette.accent,.12 * clusterStrength);
        context.lineWidth = 1;
        [[.25,.2],[.75,.2],[.25,.49],[.75,.49]].forEach(function (center) {
          context.beginPath();
          context.arc(width * center[0],height * center[1],Math.min(width,height) * .125,0,Math.PI * 2);
          context.stroke();
        });
        context.restore();
      }
    }

    function drawConnections(value) {
      context.save();
      context.lineWidth = .65;
      var limit = Math.max(38,Math.min(width,height) * .13);
      var edges = 0;
      for (var i = 0; i < nodes.length; i += 1) {
        for (var j = i + 1; j < nodes.length; j += 1) {
          if (edges > 76 || (i + j) % 5 !== 0) continue;
          if (value > 2.45 && i % 4 !== j % 4) continue;
          var dx = nodes[i].x - nodes[j].x;
          var dy = nodes[i].y - nodes[j].y;
          var distance = Math.sqrt(dx * dx + dy * dy);
          if (distance > limit) continue;
          var alpha = (1 - distance / limit) * (value < .7 ? .12 : .18);
          context.strokeStyle = rgba(nodes[i].accent || nodes[j].accent ? palette.accent : palette.ink,alpha);
          context.beginPath();
          context.moveTo(nodes[i].x,nodes[i].y);
          context.lineTo(nodes[j].x,nodes[j].y);
          context.stroke();
          edges += 1;
        }
      }
      context.restore();
    }

    function draw(time) {
      if (!width || !height) return;
      context.clearRect(0,0,width,height);
      var animate = !reduce.matches && !isStatic;
      var ease = animate ? .085 : 1;
      stageValue += (targetStage - stageValue) * ease;

      nodes.forEach(function (node,index) {
        var desired = desiredPosition(index,stageValue);
        var driftX = animate ? Math.sin(time * .00028 + node.phase) * 2.3 : 0;
        var driftY = animate ? Math.cos(time * .00024 + node.phase * 1.3) * 2 : 0;
        node.x += (desired.x + driftX - node.x) * ease;
        node.y += (desired.y + driftY - node.y) * ease;

        if (pointer.active && finePointer.matches) {
          var dx = node.x - pointer.x;
          var dy = node.y - pointer.y;
          var distance = Math.sqrt(dx * dx + dy * dy) || 1;
          var reach = 92;
          if (distance < reach) {
            var force = (1 - distance / reach) * 4.5;
            node.x += dx / distance * force;
            node.y += dy / distance * force;
          }
        }
      });

      drawGuides(stageValue);
      if (stageValue < 1.65 || stageValue > 2.15) drawConnections(stageValue);

      nodes.forEach(function (node,index) {
        var isAccent = node.accent || (stageValue > 2.5 && index % 4 === currentStage % 4);
        context.fillStyle = rgba(isAccent ? palette.accent : palette.ink,isAccent ? .92 : .58);
        context.beginPath();
        context.arc(node.x,node.y,node.size,0,Math.PI * 2);
        context.fill();

        if (index % 8 === 0) {
          context.strokeStyle = rgba(isAccent ? palette.accent : palette.ink,isAccent ? .4 : .2);
          context.lineWidth = .7;
          context.beginPath();
          context.moveTo(node.x + node.size + 3,node.y);
          context.lineTo(node.x + node.size + 3 + node.messageLength,node.y);
          context.stroke();
        }
      });
    }

    function setStage(stage) {
      stage = Math.max(0,Math.min(3,stage));
      if (stage === currentStage) return;
      currentStage = stage;
      observatory.setAttribute("data-stage",String(stage));
      if (indexLabel) indexLabel.textContent = "0" + (stage + 1);
      panels.forEach(function (panel) {
        panel.classList.toggle("is-current",Number(panel.getAttribute("data-observatory-panel")) === stage);
      });
    }

    function calculateStage() {
      scrollFrame = 0;
      var readingLine = window.scrollY + window.innerHeight * .48;
      var centers = steps.map(function (step) {
        var box = step.getBoundingClientRect();
        return window.scrollY + box.top + box.height * .5;
      });

      if (readingLine <= centers[0]) {
        targetStage = 0;
      } else if (readingLine < centers[1]) {
        targetStage = (readingLine - centers[0]) / Math.max(1,centers[1] - centers[0]);
      } else if (readingLine < centers[2]) {
        targetStage = 1 + (readingLine - centers[1]) / Math.max(1,centers[2] - centers[1]);
      } else {
        var storyBox = story.getBoundingClientRect();
        var storyEnd = window.scrollY + storyBox.bottom - window.innerHeight * .24;
        targetStage = 2 + Math.max(0,Math.min(1,(readingLine - centers[2]) / Math.max(1,storyEnd - centers[2])));
      }

      setStage(Math.round(targetStage));
      if (reduce.matches || isStatic || !active) {
        stageValue = targetStage;
        nodes.forEach(function (node,index) {
          var desired = desiredPosition(index,stageValue);
          node.x = desired.x;
          node.y = desired.y;
        });
        draw(performance.now());
      }
    }

    function requestStage() {
      if (!scrollFrame) scrollFrame = requestAnimationFrame(calculateStage);
    }

    function loop(time) {
      frame = 0;
      draw(time);
      if (active && !reduce.matches && !isStatic) frame = requestAnimationFrame(loop);
    }

    function start() {
      active = true;
      if (!frame && !reduce.matches && !isStatic) frame = requestAnimationFrame(loop);
      else draw(performance.now());
    }

    function stop() {
      active = false;
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
    }

    field.addEventListener("pointermove",function (event) {
      if (!finePointer.matches || reduce.matches) return;
      var box = field.getBoundingClientRect();
      pointer.x = event.clientX - box.left;
      pointer.y = event.clientY - box.top;
      pointer.active = true;
    },{ passive: true });
    field.addEventListener("pointerleave",function () { pointer.active = false; });

    window.addEventListener("scroll",requestStage,{ passive: true });
    window.addEventListener("resize",function () {
      resize();
      calculateStage();
    });

    if (window.ResizeObserver) {
      new ResizeObserver(resize).observe(field);
    }

    if (window.IntersectionObserver) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) start();
          else stop();
        });
      },{ rootMargin: "20% 0px 20% 0px" }).observe(story);
    }

    if (reduce.addEventListener) {
      reduce.addEventListener("change",function () {
        if (reduce.matches) stop();
        else start();
        calculateStage();
      });
    }

    new MutationObserver(function () {
      updatePalette();
      draw(performance.now());
    }).observe(document.documentElement,{ attributes: true, attributeFilter: ["data-theme"] });

    setStage(0);
    resize();
    calculateStage();
    start();
  }

  function setupTranscriptPreviews() {
    document.querySelectorAll("[data-transcript-preview]").forEach(function (preview) {
      var triggers = Array.from(preview.querySelectorAll("[data-transcript-trigger]"));
      var panels = Array.from(preview.querySelectorAll("[data-transcript-panel]"));
      if (!triggers.length || !panels.length) return;

      function setStage(index,focusTrigger) {
        index = Math.max(0,Math.min(triggers.length - 1,index));
        preview.setAttribute("data-stage",String(index));

        triggers.forEach(function (trigger,triggerIndex) {
          var current = triggerIndex === index;
          trigger.classList.toggle("is-current",current);
          trigger.setAttribute("aria-selected",current ? "true" : "false");
          trigger.setAttribute("tabindex",current ? "0" : "-1");
          if (current && focusTrigger) trigger.focus();
        });

        panels.forEach(function (panel,panelIndex) {
          var current = panelIndex === index;
          panel.classList.toggle("is-current",current);
          panel.hidden = !current;
          if (current) panel.removeAttribute("inert");
          else panel.setAttribute("inert","");
        });
      }

      triggers.forEach(function (trigger,index) {
        trigger.addEventListener("click",function () {
          setStage(index,false);
        });

        trigger.addEventListener("keydown",function (event) {
          var next = index;
          if (event.key === "ArrowRight") next = (index + 1) % triggers.length;
          else if (event.key === "ArrowLeft") next = (index - 1 + triggers.length) % triggers.length;
          else if (event.key === "Home") next = 0;
          else if (event.key === "End") next = triggers.length - 1;
          else return;
          event.preventDefault();
          setStage(next,true);
        });
      });

      setStage(Number(preview.getAttribute("data-stage")) || 0,false);
    });
  }

  setupTranscriptPreviews();

  var root = document.documentElement;
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var staticMode = root.classList.contains("static");
  var revealItems = Array.from(document.querySelectorAll("[data-reveal]"));
  var revealObserver = null;
  var parallaxFrame = 0;
  var hero = document.querySelector(".candidate-hero");
  var method = document.querySelector(".candidate-method-bridge");
  var villageCreation = document.querySelector(".candidate-village-creation");
  var readingProgress = document.querySelector(".candidate-reading-progress span");
  var themeToggle = document.querySelector("[data-theme-toggle]");

  if (themeToggle) {
    themeToggle.addEventListener("click",function () {
      var freeze = document.createElement("style");
      freeze.textContent = "*,*::before,*::after{transition:none!important}";
      document.head.appendChild(freeze);
      void document.documentElement.offsetHeight;
      requestAnimationFrame(function () { freeze.remove(); });
    },true);
  }

  function revealEverything() {
    revealItems.forEach(function (item) {
      item.classList.add("is-revealed");
    });
  }

  function revealVisibleItems() {
    revealItems.forEach(function (item) {
      var box = item.getBoundingClientRect();
      if (box.bottom > 0 && box.top < window.innerHeight * .92) {
        item.classList.add("is-revealed");
        if (revealObserver) revealObserver.unobserve(item);
      }
    });
  }

  function revealHashTarget() {
    if (!window.location.hash) return;
    var id = decodeURIComponent(window.location.hash.slice(1));
    var target = document.getElementById(id);
    if (!target) return;
    if (target.hasAttribute("data-reveal")) target.classList.add("is-revealed");
    target.querySelectorAll("[data-reveal]").forEach(function (item) {
      item.classList.add("is-revealed");
      if (revealObserver) revealObserver.unobserve(item);
    });
  }

  function updateParallax() {
    parallaxFrame = 0;
    if (readingProgress) {
      var distance = document.documentElement.scrollHeight - window.innerHeight;
      var progress = distance > 0 ? Math.max(0,Math.min(1,window.scrollY / distance)) : 0;
      readingProgress.style.transform = "scaleX(" + progress.toFixed(4) + ")";
    }
    if (reducedMotion.matches || staticMode) return;

    if (hero) {
      var heroShift = Math.max(0,Math.min(34,window.scrollY * .055));
      hero.style.setProperty("--hero-parallax",heroShift.toFixed(2) + "px");
    }

    if (method) {
      var methodBox = method.getBoundingClientRect();
      if (methodBox.bottom > 0 && methodBox.top < window.innerHeight) {
        var methodCenter = methodBox.top + methodBox.height / 2;
        var methodShift = Math.max(-24,Math.min(24,(window.innerHeight / 2 - methodCenter) * .028));
        method.style.setProperty("--method-parallax",methodShift.toFixed(2) + "px");
      }
    }

    if (villageCreation) {
      var creationBox = villageCreation.getBoundingClientRect();
      if (creationBox.bottom > 0 && creationBox.top < window.innerHeight) {
        var creationCenter = creationBox.top + creationBox.height / 2;
        var creationShift = Math.max(-16,Math.min(16,(window.innerHeight / 2 - creationCenter) * .035));
        villageCreation.style.setProperty("--creation-parallax",creationShift.toFixed(2) + "px");
      }
    }
  }

  function requestParallax() {
    if (!parallaxFrame) parallaxFrame = requestAnimationFrame(updateParallax);
  }

  function startMotion() {
    window.addEventListener("scroll",requestParallax,{ passive: true });
    window.addEventListener("resize",requestParallax);
    updateParallax();

    if (staticMode || reducedMotion.matches || window.matchMedia("(max-width: 900px)").matches) {
      revealEverything();
      return;
    }

    root.classList.add("motion-ready");
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        root.classList.add("motion-started");
      });
    });

    revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-revealed");
        revealObserver.unobserve(entry.target);
      });
    },{ rootMargin: "0px 0px -12% 0px", threshold: .12 });

    revealItems.forEach(function (item) {
      revealObserver.observe(item);
    });

    requestAnimationFrame(revealVisibleItems);
    requestAnimationFrame(revealHashTarget);
    window.addEventListener("load",function () {
      requestAnimationFrame(revealVisibleItems);
      requestAnimationFrame(revealHashTarget);
    },{ once: true });
    window.addEventListener("hashchange",function () {
      requestAnimationFrame(revealVisibleItems);
      requestAnimationFrame(revealHashTarget);
    });

  }

  function stopMotion() {
    if (revealObserver) revealObserver.disconnect();
    root.classList.remove("motion-ready","motion-started");
    revealEverything();
    if (hero) hero.style.setProperty("--hero-parallax","0px");
    if (method) method.style.setProperty("--method-parallax","0px");
    if (villageCreation) villageCreation.style.setProperty("--creation-parallax","0px");
  }

  if (reducedMotion.addEventListener) {
    reducedMotion.addEventListener("change",function (event) {
      if (event.matches) stopMotion();
    });
  }

  startMotion();
})();
