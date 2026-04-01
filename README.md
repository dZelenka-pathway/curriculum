# Curriculum
2026 Curriculum Development

---

## Step 1 - Course Initation

Use the following prompt to build a new Course Blueprint and Course Unit Map:
```
Write a Course Blueprint and Course Unit Map for [course] (code in HTML templates) and discussion prompts (doc). All of our math practice will use CK-12 which includes online activities per topic. Rather than breaking it up into 18-week structure with 9-lesson FLEx cycles. We will use the CK-12 Unit Structure. Everything else will be the same. 

CK-12 practices are scored only on completion (100% or 0). They are adaptive learning. There will be 2 activities per quarter which will be considered extra credit.

Each week should have a discussion: math tied to Biblical using the 6 kingdom domains. Provide 3 per week alternatives. Due each Friday. Prompt should be no more than 500 characters. Write prompts that encourage math creativity, so students can't just copy and paste from an LLM. Examples: https://www.youcubed.org/tasks. When possible, correlate with the math standards covered that week. ~15% of discussion-based tasks should be simple math puzzles and riddles, which may require group discussion effort to solve.

Each week should have a notebook due on Friday.

Each unit will have a unit exam in Flint. There will be Practice and Exam mode.

---

Quarterly PBL Project-based learning projects, develop these based on discomath.com activities: https://discomath.com/activities/list/8. If there is no good fit, suggest a quarter PBL math investigation.

---

General Rubric: 
Excellent - A - 5.0
Proficient - B - 4.4
Developing - C - 3.9
Needs Improvement - D - 3.5
Insufficient - F - 3.0

This method allows conversion to a grade. When using multiple criteria, an average can be built based on that second value, using the Canvas rubric tool. Rubrics are attached as Rubric5PointMath.csv.

---

Below is an example of a Math Unit Exam Prompt, just as an example of what we will build later.
Build a 40-minute [course] Third Quarter exam. Follow these guidelines:

EXAM STRUCTURE:
Students will have Two Modes:
A) Practice Mode - Work through problems for learning (unlimited attempts)
B) Official Exam - Your graded assessment (tell me when ready)
Cover topics from all content randomly
Limit each problem to 5 minutes max
Use simple integer solutions when possible. Angles in degrees.
Create diagrams as needed for visual problems
Focus on conceptual understanding over exact calculations
VISUAL PROBLEMS:
For questions that can be visualized or algebra used, first say "Sketch them out in your notebook."
If you create diagrams, ensure the entire visualization fits within the graph bounds
Students can request diagrams at any time. Do not provide prompt options with solutions. Do not allow pasting of latex, markdown, or non-standard keyboard characters such as em dashes; consider it cheating. For math prompt them to use standard keyboard characters (sqrt(), ^ and _.) Provide them a warning, do not explain to the student how you know. Mark any problem where cheating occurred as fully incorrect.
Exam ASSESSMENT APPROACH:
Encourage and accept discussion-based answers that show understanding. Let students know there will be a oral component after the exam to discuss understanding and that the oral review may affect the grade.
Probe deeper knowledge rather than just computational skills
If student struggles >5 minutes, move to new topic
Keep responses low-verbose
Begin the 40-minute exam when student indicates official exam. Use different question bank. Export question banks into well structured json file with latex for math into one file differentiating between practice-mode and exam-mode problems.

GRADING:

Excellent: Deep understanding, clear explanations, correct applications
Proficient: Solid understanding, mostly clear explanations, minor errors
Developing: Partial understanding, needs clarity, some errors; less than 8 questions answered
Needs Improvement: Limited understanding, unclear explanations, frequent errors; less than 4 questions answered

---

For this output, create (1) 4-quarter blueprint (code in html); (2) course unit map (code in html), include CCS Math Standards chart in course unit map. No lessons or assessments.; produce (3) the weekly discussion prompts. Don't use the standard 18-week structure with 9-lessons. Just 18 weeks of content. Break up into CK-12-based units. Name weeks by semester: Semester 1 or 2: Week 1-18. 
Try to begin a new unit at the beginning of each semester and quarter (9 weeks). 

---
https://flexbooks.ck12.org/cbook/ck-12-algebra-i-concepts

Attached:  Course Authoring Document, CK-12 Curriculum overview page. Discover Math PBL Math Investigations, math-rubric-5-point.csv, template_course_unit_map.html, template_blueprint.html
```
Example of CK-12 Flexbook: [https://flexbooks.ck12.org/cbook/ck-12-algebra-i-concepts]

You may need to ask Flint to "code in html" after it produces these docs. Paste html documents to the Pages section in Canvas as html. Remove all html outside divs.


## Step 2 - Assessments and Standards Guide

After Step 1 in same chat, use css/template_assessment_standard_guide.html as a template:
```
Build and code in html the Assessments and Standards guide using this template:
```
Paste template after prompt. Upload to the Pages section in Canvas as html. Remove all html outside divs.

## Step 3 - Discussions

Edit each discussion for Semester A and Semester B. Filter the best of the three options for each week or modify to create your own.

# Step 4 - Repeat for all course units

Build each Unit pre-assessment QTI Quiz with introductory html. This may be converted at a later date to EG.

```
Unit Introduction	"Write a brief introductory lesson for [course] Unit [x]. Less than 5000 chars.  
---
Title: [unit title]
Subtitle: [create subtitle]
Sections:
What is ...[explain how jesus is the logos and how he forms our reasoning ability.]
Three Big Ideas...
Your Exploration Task...
Closing Reflection
---

Include a 10 question quiz in the following format. Not included in 5000 character count.

1. What is the capital of France?
a) London
b) Berlin
c) Paris*
d) Madrid

2. Match: Match countries with capitals
France = Paris
Italy = Rome

```
Paste a list of all sub-unit topics. Provide html template: css/template_unit_introduction.html. You will need to resubmit just unit introduction and ask it to "code in html." 



---

- Go to QTI packaging site and paste in quiz. 
- Export as QTI and import into course. 
- Edit new quiz and paste in html. 
- Add as module in correct unit.

[https://quiz-genius-flow.base44.app/]

Easy Generator 
```
1. What is the capital of France?
a) London
b) Berlin
c) Paris*
d) Madrid

2. Match: Match countries with capitals
France = Paris
Italy = Rome
```
Ordering does not seem to import properly.


