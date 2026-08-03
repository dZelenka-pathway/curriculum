# Pathway Christian Prep Academy - Canvas Styling

This repository contains standardized HTML templates and CSS styling for Pathway Christian Prep Academy's Canvas LMS pages.

## 📁 Files

- **`pathway-canvas-stylesheet.css`** - Main stylesheet with Pathway branding (navy #001f3e and gold #ebbd6b)
- **`template1.html`** - Clean HTML template for Canvas pages
- **`curved-header.html`** - Classes: pw-lesson-header, pw-lesson-div

Purge file
- Go to: https://www.jsdelivr.com/tools/purge
- Enter your URL: https://cdn.jsdelivr.net/gh/dZelenka-pathway/curriculum@main/css/pathway-canvas-stylesheet.css
- Click "Purge cache"
- Wait 5-10 minutes, then refresh your Canvas page

## 🎨 Using in Canvas

### Imported CSS Globally (Admins)

This has been added to Canvas **Admin → Themes → Global CSS**:

```css
@import url('https://cdn.jsdelivr.net/gh/dZelenka-pathway/curriculum@main/css/pathway-canvas-stylesheet.css');
```

## 📝 Using the Template

1. Copy the HTML from `template1.html`
2. Replace bracketed placeholders `[Main Title]`, `[Section 1]`, etc. with your content
3. Paste into Canvas page (HTML editor mode)
4. Prompt LLM with "Code in html inline text." It will sometimes ignore that prompt. If so, try again.
5. Alternate prompt: "Code inline text the content into this template (do not include quiz, <body> content only).  If there's content gap in the html structure add content."

### Template Structure:

```html
<div class="pw-canvas">
    <div class="pw-header">
        <h1>[Main Title]</h1>
        <p class="pw-subtitle">[Subtitle]</p>
        <p class="pw-bright"><strong>FLEx Phase: [if available]</strong></p>
    </div>
    
    <div class="pw-0">
        <h2>[Section 1]</h2>
        <p>[Content...]</p>
    </div>
    
    <div class="pw-1">
        <h2>[Section 2]</h2>
        <p>[Content...]</p>
    </div>

    <div class="pw-footer">
        &copy; Pathway Christian Preparatory Academy &mdash; [footer title]
    </div>
</div>
```

## 🤖 Using with AI Assistants (ChatGPT, Claude, Sparky, etc.)

When asking an AI to create Canvas content with Pathway styling, provide this prompt:

```
Use the Pathway Christian Prep Academy Canvas template from:
https://github.com/dZelenka-pathway/curriculum/tree/main/css

Template: https://raw.githubusercontent.com/dZelenka-pathway/curriculum/main/css/template1.html
Stylesheet: https://raw.githubusercontent.com/dZelenka-pathway/curriculum/main/css/pathway-canvas-stylesheet.css

Create content using the .pw-canvas structure with:
- .pw-header for title section
- .pw-0, .pw-1, .pw-2, .pw-3 for alternating content sections
- .pw-footer for copyright footer

```

## 🔄 Updating Styles

When you update `pathway-canvas-stylesheet.css`:

1. Commit changes to GitHub
2. jsDelivr CDN will cache for up to 24 hours
3. To force immediate update, use versioned URL:
   ```
   https://cdn.jsdelivr.net/gh/dZelenka-pathway/curriculum@COMMIT-HASH/css/pathway-canvas-stylesheet.css
   ```
4. Or purge cache at: https://www.jsdelivr.com/tools/purge

## 📋 Quick Start Example

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/dZelenka-pathway/curriculum@main/css/pathway-canvas-stylesheet.css">

<div class="pw-canvas">
    <div class="pw-header">
        <h1>Algebra 1 - Unit 3</h1>
        <p class="pw-subtitle">Linear Equations and Inequalities</p>
        <p class="pw-bright"><strong>FLEx Phase: Foundation</strong></p>
    </div>
    
    <div class="pw-0">
        <h2>Learning Objectives</h2>
        <ul>
            <li>Solve one-step and two-step equations</li>
            <li>Graph linear inequalities on a number line</li>
            <li>Apply equations to real-world problems</li>
        </ul>
    </div>
    
    <div class="pw-1">
        <h2>Key Vocabulary</h2>
        <p><strong>Equation:</strong> A mathematical statement that two expressions are equal.</p>
        <p><strong>Inequality:</strong> A mathematical statement comparing two expressions using &lt;, &gt;, ≤, or ≥.</p>
    </div>

    <div class="pw-footer">
        &copy; Pathway Christian Preparatory Academy &mdash; Algebra 1
    </div>
</div>
```
## Color Palette

| Swatch | Hex Code | Description / Usage |
| :---: | :--- | :--- |
| <span style="display:inline-block; width:22px; height:22px; background:#001f3e; border:1px solid #ccc; border-radius:4px; vertical-align:middle;"></span> | `#001f3e` | **Primary Dark Navy** — Main headers, borders, footer, callout text |
| <span style="display:inline-block; width:22px; height:22px; background:#003d66; border:1px solid #ccc; border-radius:4px; vertical-align:middle;"></span> | `#003d66` | **Deep Blue** — Header background gradient stop |
| <span style="display:inline-block; width:22px; height:22px; background:#ebbd6b; border:1px solid #ccc; border-radius:4px; vertical-align:middle;"></span> | `#ebbd6b` | **Pathway Gold** — Subtitles, accent borders, buttons, callout background |
| <span style="display:inline-block; width:22px; height:22px; background:#222222; border:1px solid #ccc; border-radius:4px; vertical-align:middle;"></span> | `#222` (`#222222`) | **Charcoal** — Default body text |
| <span style="display:inline-block; width:22px; height:22px; background:#555555; border:1px solid #ccc; border-radius:4px; vertical-align:middle;"></span> | `#555` (`#555555`) | **Medium Gray** — Blockquote body text |
| <span style="display:inline-block; width:22px; height:22px; background:#e0e0e0; border:1px solid #ccc; border-radius:4px; vertical-align:middle;"></span> | `#e0e0e0` | **Light Slate** — Header metadata text |
| <span style="display:inline-block; width:22px; height:22px; background:#dddddd; border:1px solid #ccc; border-radius:4px; vertical-align:middle;"></span> | `#ddd` (`#dddddd`) | **Border Gray** — Table grid lines |
| <span style="display:inline-block; width:22px; height:22px; background:#f7f8fa; border:1px solid #ccc; border-radius:4px; vertical-align:middle;"></span> | `#f7f8fa` | **Off-White** — Alternating section backgrounds, table rows, reflection box |
| <span style="display:inline-block; width:22px; height:22px; background:#ffffff; border:1px solid #ccc; border-radius:4px; vertical-align:middle;"></span> | `#fff` (`#ffffff`) | **Pure White** — Cards, headers text, container background |

**Repository:** https://github.com/dZelenka-pathway/curriculum  
**Maintained by:** Pathway Christian Prep Academy
