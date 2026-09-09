# GSAP® Design System & Frontend Taste Specification
> **Theme:** Animated Chalkboard in a Design Studio  
> **Philosophy:** A near-black stage where warm cream typography, thin outlined ghost pill buttons, and 5-discipline color taxonomy highlights create a typographic showcase rather than a generic marketing site.

---

## 1. Core Color Tokens (Strict Taxonomy)

Color functions as **taxonomy and data signaling**, never as arbitrary decoration.

| Design Token | Hex Code | Purpose & Semantic Role |
| :--- | :--- | :--- |
| `--color-just-black` | `#0e100f` | Main canvas background (*near-black matte chalkboard wall*) |
| `--color-off-black` | `#141514` / `#191919` | Elevated surfaces, nested card backgrounds, data panels |
| `--color-surface-cream` | `#fffce1` | Primary text, heading typography, ghost pill button borders |
| `--color-surface-50` | `#7c7c6f` | Secondary text, subtle descriptions, axis labels |
| `--color-surface-25` | `#42433d` / `#282829` | Hairline borders, structural grid dividers (1px solid) |
| `--color-shockingly-green` | `#0ae448` | Brandmark, core alpha, active CTAs, winning PnL |
| `--gradient-shockingly-green` | `linear-gradient(114.41deg, #0ae448 20.74%, #abff84 65.5%)` | 1.5px gradient stroke for primary active trading mode |

### 5-Discipline Highlight Taxonomy
* 🌸 **Scroll / Journal Annotations (`#fec5fb`)**: Trade history, timestamps, log tags.
* 🍊 **SVG / Alerts & Shorts (`#ff8709`)**: Bearish signals, liquidation zones, circuit breaker alerts.
* 🔮 **Text / LLM Debates & Copilot (`#9d95ff`)**: AI Senior Quant Officer, Bull vs Bear debate, narrative summaries.
* 💧 **UI / Longs & Visual Signals (`#00bae2`)**: Bullish signals, institutional flows, order flow imbalance.
* 🍃 **Core GSAP & Alpha (`#0ae448` / `#dfffd1`)**: Verified confluences, take-profit levels, positive PnL.

---

## 2. Typography & Layout Standards

* **Font Families**:
  * Display / Headlines: `'Inter Tight', -apple-system, BlinkMacSystemFont, sans-serif`
  * Body / UI: `'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif`
  * Monospace Data: `'Geist Mono', 'JetBrains Mono', 'Fira Code', monospace`
* **Letter Spacing**: Aggressive negative tracking (`-0.02em` to `-0.03em`) on titles and headers for a carved, typographic presence.
* **Signature Brackets**: Section headings and navigation tabs are wrapped with GSAP signature curly-brackets:
  * `{ Terminal }`
  * `{ Market Intelligence }`
  * `{ Trade Journal }`
  * `{ Paperclip Firm }`

---

## 3. Interactive Components & Micro-Interactions

1. **Ghost Pill Buttons**:
   * Outlined pills with `border-radius: 100px`.
   * Transparent background, `1px solid #fffce1` or `1px solid #42433d`.
   * Strictly **zero heavy solid background fills** on secondary actions.
2. **Showcase Cards**:
   * Corner radius: `8px` (`--radius-cards`).
   * Border: Hairline `1px solid #282829`.
   * Strictly **zero heavy blurry drop-shadows**; depth is achieved via tonal surface steps (`#141514` on top of `#0e100f`).
3. **Micro-Motion & Easing**:
   * Transition curves: `cubic-bezier(0.16, 1, 0.3, 1)` (150ms–250ms).
   * Active pulse on live daemons and WebSocket streaming ticks.

---

## 4. Anti-Slop Guardrails (Banned Patterns)

❌ **Banned**: Generic purple-to-blue gradient cards.  
❌ **Banned**: Oversized pill buttons filled with solid neon colors.  
❌ **Banned**: Blurry `box-shadow: 0 10px 30px rgba(...)` on dark surfaces.  
❌ **Banned**: Unformatted vertical line-wrapping on button text.  
❌ **Banned**: Placeholder strings or unstyled browser default form controls.  
