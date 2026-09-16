---
name: smoothui-magicui-library
description: Curated high-end UI library recipes and modern SaaS design patterns from SmoothUI (smoothui.dev), Magic UI (magicui.design), Aceternity UI, Motion Primitives, and Origin UI. Use when building or upgrading web applications, dashboards, landing pages, and interactive components with smooth micro-interactions, border beams, cursor spotlights, dynamic islands, number tickers, and high-agency tactile feedback.
---

# 🎨 SmoothUI & Magic UI SaaS Design System

A master reference of curated UI library patterns, micro-interactions, and component recipes designed to make interfaces look like a multi-million-dollar SaaS product (Linear, Raycast, Vercel) rather than generic AI slop.

---

## 🏛️ The 5 Goldmine Component Libraries

1. **SmoothUI (`smoothui.dev`)**:
   - 130+ animated React/Tailwind/GSAP components.
   - Core specialties: Shader reveal transitions, dynamic islands, expandable bento cards, animated avatar groups, magnetic cursor elements.
2. **Magic UI (`magicui.design`)**:
   - 50+ animated landing page & dashboard primitives.
   - Core specialties: Animated Border Beam, Cursor Spotlight Cards, Number Tickers, Marquee Tickers, Particle & Radial Grids.
3. **Aceternity UI (`ui.aceternity.com`)**:
   - High-contrast futuristic interactions.
   - Core specialties: 3D Pin Cards, Floating Docks, Background Gradient Beams, Lamp effect heroes.
4. **Motion Primitives (`motion-primitives.com`)**:
   - Apple-grade fluid gestures and physics.
   - Core specialties: Spring dialogs, smooth popovers, morphing menus, drag-to-dismiss panels.
5. **Origin UI (`originui.com`)**:
   - Clean, functional UI inputs and data displays.
   - Core specialties: 100+ input fields, status chips, multi-action selects, tabular data grids.

---

## 💎 Core SaaS Design Patterns (Copy-Paste Recipes)

### 1. Magic UI: Cursor Spotlight Card
Cards subtly illuminate when the mouse hovers over or moves across them, revealing hairline borders:

```css
.spotlight-card {
  position: relative;
  background: #0c0e12;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.spotlight-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(
    600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
    rgba(255, 255, 255, 0.05),
    transparent 40%
  );
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 1;
}

.spotlight-card:hover::before {
  opacity: 1;
}
```

```javascript
document.querySelectorAll('.spotlight-card').forEach(card => {
  card.addEventListener('mousemove', e => {
    const rect = card.getBoundingClientRect();
    card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
    card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
  });
});
```

---

### 2. Magic UI: Animated Border Beam
An elegant, razor-thin light beam travelling along the perimeter of an active badge or hero card:

```css
@keyframes border-beam {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.border-beam-container {
  position: relative;
  border-radius: 100px;
  padding: 1px;
  overflow: hidden;
  display: inline-flex;
}

.border-beam-container::before {
  content: '';
  position: absolute;
  top: -50%; left: -50%; width: 200%; height: 200%;
  background: conic-gradient(from 0deg, transparent 0 340deg, #3b82f6 360deg);
  animation: border-beam 4s linear infinite;
  pointer-events: none;
}

.border-beam-content {
  position: relative;
  background: #060709;
  border-radius: 99px;
  z-index: 1;
  padding: 3px 8px;
}
```

---

### 3. SmoothUI: Dynamic Island & Pulsing Status Capsule
A compact status pill with a breathing micro-dot and hairline outline:

```css
@keyframes pulse-ring {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 245, 155, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(0, 245, 155, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 245, 155, 0); }
}

.status-capsule {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 100px;
  padding: 3px 8px;
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  color: #fffce1;
}

.status-dot-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00f59b;
  animation: pulse-ring 2s infinite cubic-bezier(0.45, 0, 0.55, 1);
}
```

---

### 4. Magic UI: Shimmer Button Sweep
A clean, premium shimmer sweep on primary CTA buttons on hover:

```css
@keyframes shimmer-sweep {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

.btn-shimmer {
  position: relative;
  overflow: hidden;
  background: #2f80ed;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-shimmer::after {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.25), transparent);
  transform: translateX(-100%);
  pointer-events: none;
}

.btn-shimmer:hover::after {
  animation: shimmer-sweep 1s ease-in-out;
}
```

---

### 5. Magic UI: Number Ticker & Data Flash Indicator
Subtle visual indication when numbers update in a streaming or polling terminal:

```css
@keyframes flash-green {
  0% { background-color: rgba(0, 245, 155, 0.25); color: #00f59b; }
  100% { background-color: transparent; }
}

@keyframes flash-red {
  0% { background-color: rgba(255, 59, 86, 0.25); color: #ff3b56; }
  100% { background-color: transparent; }
}

.data-flash-up {
  animation: flash-green 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.data-flash-down {
  animation: flash-red 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}
```

---

## 🚫 Anti-Slop Enforcement Guidelines
When adopting these libraries:
- **Never use gaudy 3D drop shadows or blurry glow filters.** Use hairline 1px borders with opacity gradients.
- **Never use generic purple-to-pink gradient backgrounds.** Stick to deep charcoal (`#060709`, `#0c0e12`) with intentional accent colors (electric green, cyber cyan, amber, crisp white).
- **Keep animations subtle (<0.3s duration).** Fast and snappy, not floaty or distracting.
