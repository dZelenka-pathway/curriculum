# README.md for Algebra 1 Canvas Import

# Algebra 1 Pathway Canvas Common Cartridge Import

This package generates a **Common Cartridge (.imscc)** file containing 161 CK-12 Algebra 1 assignments ready to import into Canvas.

## What's Included

- **161 unique assignments** spanning chapters 1–13
- Each assignment has:
  - Unique folder structure
  - Unique HTML file with lesson instructions
  - Unique `assignment_settings.xml` configuration
  - Placeholder external tool URL (to be replaced with actual CK-12 links)
- Complete `imsmanifest.xml` for Canvas compatibility
- Course settings files required by Canvas

## How to Use

### Step 1: Generate the Import File

Run the Python script:

```bash
python generate_canvas_import.py
```

This creates: `algebra1_pathway_canvas_import.imscc` (~250 KB)

### Step 2: Import into Canvas

1. Open your Canvas course
2. Navigate to **Content** → **Import Course Content**
3. Select **Common Cartridge** as the import type
4. Upload `algebra1_pathway_canvas_import.imscc`
5. Click **Import**
6. Wait for the import to complete (Canvas will create all 161 assignments)

### Step 3: Relink CK-12 URLs (⚠️ CRITICAL)

After import, each assignment has a **placeholder URL** that must be replaced with the actual CK-12 link.

**⚠️ IMPORTANT: Follow this process carefully to avoid data loss.**

For each assignment:

1. **Open the assignment** in Canvas
2. Click **Edit**
3. Scroll to the **External Tool URL** field
4. **Copy the CK-12 link** from your CK-12 class (the LTI launch URL)
5. **Paste it into the field**
6. **Reload the page** (F5 or Cmd+R)
7. **Paste the URL again** into the same field
8. Click **Save**

### ⚠️ Why the Reload Step Matters

If you do NOT reload the page before pasting the final URL:
- Canvas will overwrite the HTML content
- The assignment title will be lost
- The lesson instructions will be destroyed
- You'll lose most of the work done by this script

**The reload ensures Canvas properly registers the change without corrupting the assignment structure.**

## File Structure

```
algebra1_pathway_canvas_import.imscc (zip file)
├── imsmanifest.xml                    (manifest file)
├── course_settings/
│   ├── canvas_export.txt
│   ├── module_meta.xml
│   └── assignment_groups.xml
├── 1-1-definition-of-variable/
│   ├── 1-1-definition-of-variable.html
│   └── assignment_settings.xml
├── 1-2-expressions-with-one-or-more-variables/
│   ├── 1-2-expressions-with-one-or-more-variables.html
│   └── assignment_settings.xml
├── ... (159 more assignment folders)
```

## Assignment List

All 161 assignments are organized by chapter:

- **Chapter 1:** Equations and Functions (1.1–1.17)
- **Chapter 2:** Real Numbers (2.1–2.11)
- **Chapter 3:** Equations of Lines (3.1–3.15)
- **Chapter 4:** Graphs of Equations and Functions (4.1–4.11)
- **Chapter 5:** Writing Linear Equations (5.1–5.7)
- **Chapter 6:** Linear Inequalities (6.1–6.12)
- **Chapter 7:** Solving Systems of Equations and Inequalities (7.1–7.11)
- **Chapter 8:** Exponential Functions (8.1–8.12)
- **Chapter 9:** Polynomials (9.1–9.14)
- **Chapter 10:** Quadratic Equations and Quadratic Functions (10.1–10.12)
- **Chapter 11:** Algebra and Geometry Connections (11.1–11.12)
- **Chapter 12:** Rational Equations and Functions (12.1–12.13)
- **Chapter 13:** Probability and Statistics (13.1–13.14)

## Troubleshooting

### Assignment titles or content are missing after import

This typically happens if you didn't follow the reload step when relinking CK-12 URLs. Unfortunately, this cannot be undone. You'll need to:
- Delete the affected assignment
- Re-import the `.imscc` file
- Carefully follow the relink process again

### The import fails or hangs

- Check that your `.imscc` file is not corrupted
- Try importing into a test course first
- Contact Canvas support if the issue persists

### I need to update assignments for next year

Simply re-run the Python script to generate a fresh `.imscc` file and import it into a new Canvas course. The process is identical.

## Notes

- Each assignment is worth **100 points** by default (configurable in `assignment_settings.xml`)
- All assignments are set to **external_tool** submission type (CK-12 LTI)
- Assignments are **published** by default
- No due dates are set (you can add them in Canvas after import)

## Support

If you encounter issues:
1. Verify the `.imscc` file was generated correctly (check file size ~250 KB)
2. Test import in a Canvas sandbox/test course first
3. Review the Canvas Common Cartridge documentation
4. Contact your Canvas administrator

---

**Generated for:** Pathway Christian Prep Academy  
**Curriculum:** CK-12 Algebra 1 Concepts  
**Last Updated:** 2026

