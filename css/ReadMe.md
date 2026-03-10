# Pathway Christian Prep Academy - Canvas Styling

This repository contains standardized HTML templates and CSS styling for Pathway Christian Prep Academy's Canvas LMS pages.

## 📁 Files

- **`pathway-canvas-stylesheet.css`** - Main stylesheet with Pathway branding (navy #001f3e and gold #ebbd6b)
- **`template1.html`** - Clean HTML template for Canvas pages
- **`curved-header.html`** - *(Not yet deployed)*

## 🎨 Using in Canvas

### Method 1: Import CSS Globally (Recommended for Admins)

Add this to your Canvas **Admin → Themes → Global CSS**:

```css
@import url('https://cdn.jsdelivr.net/gh/dZelenka-pathway/curriculum@main/css/pathway-canvas-stylesheet.css');
```

This applies Pathway styling across all Canvas pages automatically.

### Method 2: Link CSS on Individual Pages

Add this to the top of any Canvas page (HTML editor mode):

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/dZelenka-pathway/curriculum@main/css/pathway-canvas-stylesheet.css">

<!-- Your content here -->
```

### Method 3: Embed CSS Inline (No external dependencies)

Copy the contents of `pathway-canvas-stylesheet.css` and wrap in `<style>` tags at the top of your page:

```html
<style>
/* Paste CSS contents here */
</style>

<!-- Your content here -->
```

## 📝 Using the Template

1. Copy the HTML from `template1.html`
2. Replace bracketed placeholders `[Main Title]`, `[Section 1]`, etc. with your content
3. Paste into Canvas page (HTML editor mode)

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

Include the CSS link at the top:
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/dZelenka-pathway/curriculum@main/css/pathway-canvas-stylesheet.css">
```

## 🎨 Available CSS Classes

| Class | Purpose | Styling |
|-------|---------|---------|
| `.pw-canvas` | Main container | Full width, Arial font |
| `.pw-header` | Page header | Navy background, white text, rounded top |
| `.pw-subtitle` | Subtitle text | 18px, white |
| `.pw-bright` | Accent text (FLEx Phase) | Gold color (#ebbd6b) |
| `.pw-0` | Content section | Gold left border, light gray background |
| `.pw-1` | Content section | Navy left border, white background |
| `.pw-2` | Content section | Gold left border, white background |
| `.pw-3` | Content section | Navy left border, light gray background |
| `.pw-footer` | Page footer | Navy background, white text, rounded bottom |

**Tip:** Alternate `.pw-0`, `.pw-1`, `.pw-2`, `.pw-3` for visual variety in longer pages.

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

## 📞 Support

For questions or issues, contact the Pathway curriculum team.

---

**Repository:** https://github.com/dZelenka-pathway/curriculum  
**Maintained by:** Pathway Christian Prep Academy
