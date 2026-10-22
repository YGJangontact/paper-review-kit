// check_deck.js — paste the whole file into the browser pane's javascript tool
// (mcp__Claude_Browser__javascript_tool) on a deck served over http://localhost.
// Returns a JSON report; "problems" empty means the deck passed.
(async () => {
  const problems = [];
  const warn = [];
  if (!window.Deck) return { problems: ['window.Deck missing — runtime script not loaded or crashed'], warn };
  await document.fonts.ready;
  // A hidden/background tab doesn't advance CSS transitions; disable them while measuring.
  const noAnim = document.createElement('style');
  noAnim.textContent = '*,*::before,*::after{transition:none!important;animation-duration:0s!important}';
  document.head.appendChild(noAnim);
  const slides = Deck.slides;
  const ids = new Set();
  const per = [];
  const startIndex = Deck.index, startStep = Deck.step;

  for (let i = 0; i < slides.length; i++) {
    const s = slides[i];
    if (!s.id) warn.push(`slide ${i + 1}: no id`);
    else if (ids.has(s.id)) problems.push(`slide ${i + 1}: duplicate id "${s.id}"`);
    ids.add(s.id);

    Deck.go(i, -1); // all steps shown
    await new Promise(r => setTimeout(r, 60));
    const sr = s.getBoundingClientRect();
    const k = sr.width / 1920; // stage scale
    const issues = [];

    for (const el of s.querySelectorAll('*')) {
      if (el.closest('aside.notes, .demo-stage, svg, .katex')) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      const out = Math.max(sr.left - r.left, r.right - sr.right, sr.top - r.top, r.bottom - sr.bottom) / k;
      if (out > 2) issues.push(`<${el.tagName.toLowerCase()}${el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : ''}> spills ${Math.round(out)}px outside the slide`);
      if (/(hidden|clip|auto|scroll)/.test(cs.overflow + cs.overflowY) && el.scrollHeight > el.clientHeight + 2 && el.tagName !== 'HTML')
        issues.push(`<${el.tagName.toLowerCase()}> content is clipped (${el.scrollHeight - el.clientHeight}px hidden)`);
      const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (hasText && parseFloat(cs.fontSize) < 22) issues.push(`text "${el.textContent.trim().slice(0, 30)}" is ${cs.fontSize} (< 22px)`);
    }
    // slide-level vertical overflow (flex column pushing content down)
    if (s.scrollHeight > 1080 + 2) issues.push(`slide content is ${s.scrollHeight - 1080}px taller than 1080`);
    const nSteps = s.querySelectorAll('.step').length;
    const demoCount = Deck.demos.filter(d => d.slide === s).length;
    const hasNotes = !!s.querySelector('aside.notes');
    if (issues.length) problems.push(...issues.map(m => `slide ${i + 1} (${s.id}): ${m}`));
    per.push({ n: i + 1, id: s.id, steps: nSteps, demos: demoCount, notes: hasNotes });
  }

  // keyboard walk: → from the start must reach the last slide with every step
  Deck.go(0, 0);
  let guard = 0;
  while (!(Deck.index === slides.length - 1 && Deck.step === slides[slides.length - 1].querySelectorAll('.step').length) && guard < 1000) {
    document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    guard++;
  }
  if (guard >= 1000) problems.push('keyboard walk with → never reached the last slide');

  // demos: mounted without errors, inputs present on demo slides
  document.querySelectorAll('[data-demo-error]').forEach(el => problems.push(`demo ${el.id || el.className}: ${el.getAttribute('data-demo-error')}`));
  Deck.errors.forEach(e => problems.push(`runtime error: ${e}`));
  const demoEls = document.querySelectorAll('.demo');
  demoEls.forEach(el => { if (!Deck.demos.some(d => d.el === el)) warn.push(`.demo#${el.id} has no Deck.demo(...) registration`); });

  // external resources must be version-pinned
  document.querySelectorAll('script[src], link[rel=stylesheet][href]').forEach(n => {
    const u = n.src || n.href;
    if (/cdn\.jsdelivr\.net\/npm\/|unpkg\.com\//.test(u) && !/@\d+\.\d+/.test(u)) problems.push(`unpinned CDN url: ${u}`);
  });

  Deck.go(startIndex, startStep);
  noAnim.remove();
  return {
    pass: problems.length === 0,
    slides: slides.length,
    stepsTotal: per.reduce((a, p) => a + p.steps, 0),
    demos: Deck.demos.length,
    slidesWithoutNotes: per.filter(p => !p.notes).map(p => p.n),
    problems,
    warn,
    perSlide: per
  };
})()
