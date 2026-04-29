import os
import re
import zipfile
import uuid

# ── Assignment list ────────────────────────────────────────────────────────────
assignments = [
    "1.1 Definition of Variable",
    "1.2 Expressions with One or More Variables",
    "1.3 Algebra Expressions with Exponents",
    "1.4 Order of Operations",
    "1.5 Algebra Expressions with Fraction Bars",
    "1.6 Patterns and Expressions",
    "1.7 Words that Describe Patterns",
    "1.8 Checking Solutions to Equations",
    "1.9 Checking Solutions to Inequalities",
    "1.10 Domain and Range of a Function",
    "1.11 Applications of Functions",
    "1.12 Functions on a Cartesian Plane",
    "1.13 Graphs of Functions based on Rules",
    "1.14 Function Rules based on Graphs",
    "1.15 Algebraic Functions",
    "1.16 Problem-Solving Models",
    "1.17 Comparison of Problem-Solving Models",
    "2.1 Properties of Rational Numbers",
    "2.2 Additive Inverses and Absolute Values",
    "2.3 Addition of Rational Numbers",
    "2.4 Rational Numbers in Applications",
    "2.5 Multiplication of Rational Numbers",
    "2.6 Division of Rational Numbers",
    "2.7 Mixed Numbers in Applications",
    "2.8 Distributive Property",
    "2.9 Square Roots and Irrational Numbers",
    "2.10 Properties of Rational Numbers versus Irrational Numbers",
    "2.11 Guess and Check, Work Backward",
    "3.1 One-Step Equations and Inverse Operations",
    "3.2 One-Step Equations Transformed by Multiplication-Division",
    "3.3 Applications of One-Step Equations",
    "3.4 Two-Step Equations and Properties of Equality",
    "3.5 Multi-Step Equations with Like Terms",
    "3.6 Solving Real-World Problems with Two-Step Equations",
    "3.7 Multi-Step Equations",
    "3.8 Solving Real-World Problems Using Multi-Step Equations",
    "3.9 Equations with Variables on Both Sides",
    "3.10 Ratios",
    "3.11 Proportions",
    "3.12 Scale and Indirect Measurement Applications",
    "3.13 Conversion of Decimals, Fractions, and Percents",
    "3.14 Percent Equations",
    "3.15 Percent of Change",
    "4.1 Points in the Coordinate Plane",
    "4.2 Graphs in the Coordinate Plane",
    "4.3 Graphs of Linear Equations",
    "4.4 Horizontal and Vertical Line Graphs",
    "4.5 Intercepts and the Cover-Up Method",
    "4.6 Slope",
    "4.7 Rates of Change",
    "4.8 Graphs Using Slope-Intercept Form",
    "4.9 Graphs of Linear Models of Direct Variation",
    "4.10 Graphs of Linear Functions",
    "4.11 Problem Solving with Linear Graphs",
    "5.1 Determining the Equation of a Line",
    "5.2 Forms of Linear Equations",
    "5.3 Applications Using Linear Models",
    "5.4 Comparing Equations of Parallel and Perpendicular Lines",
    "5.5 Families of Lines",
    "5.6 Fitting Lines to Data",
    "5.7 Linear Interpolation and Extrapolation",
    "6.1 Inequality Expressions",
    "6.2 Linear Inequalities",
    "6.3 Multi-Step Inequalities",
    "6.4 Applications with Inequalities",
    "6.5 Compound Inequalities",
    "6.6 Solutions to Compound Inequalities",
    "6.7 Absolute Value",
    "6.8 Absolute Value Equations",
    "6.9 Graphs of Absolute Value Equations",
    "6.10 Absolute Value Inequalities",
    "6.11 Graphs of Inequalities in One Variable",
    "6.12 Linear Inequalities in Two Variables",
    "7.1 Graphs of Linear Systems",
    "7.2 Systems Using Substitution",
    "7.3 Mixture Problems",
    "7.4 Linear Systems with Addition or Subtraction",
    "7.5 Linear Systems with Multiplication",
    "7.6 Comparing Methods for Solving Linear Systems",
    "7.7 Consistent and Inconsistent Linear Systems",
    "7.8 Determining the Type of Linear System",
    "7.9 Applications of Linear Systems",
    "7.10 Systems of Linear Inequalities",
    "7.11 Linear Programming",
    "8.1 Exponential Properties Involving Products",
    "8.2 Exponential Terms Raised to an Exponent",
    "8.3 Exponential Properties Involving Quotients",
    "8.4 Exponent of a Quotient",
    "8.5 Negative Exponents",
    "8.6 Fractional Exponents",
    "8.7 Evaluating Exponential Expressions",
    "8.8 Scientific Notation",
    "8.9 Scientific Notation with a Calculator",
    "8.10 Geometric Sequences and Exponential Functions",
    "8.11 Graphs of Exponential Functions",
    "8.12 Applications of Exponential Functions",
    "9.1 Polynomials in Standard Form",
    "9.2 Addition and Subtraction of Polynomials",
    "9.3 Multiplication of Monomials by Polynomials",
    "9.4 Multiplication of Polynomials by Binomials",
    "9.5 Special Products of Polynomials",
    "9.6 Monomial Factors of Polynomials",
    "9.7 Zero Product Principle",
    "9.8 Factorization of Quadratic Expressions",
    "9.9 Factorization of Quadratic Expressions with Negative Coefficients",
    "9.10 Factorization using Difference of Squares",
    "9.11 Factorization using Perfect Square Trinomials",
    "9.12 Factoring Completely",
    "9.13 Factoring by Grouping",
    "9.14 Solving Problems by Factoring",
    "10.1 Quadratic Functions and Their Graphs",
    "10.2 Graphs of Quadratic Functions in Intercept Form",
    "10.3 Use Graphs to Solve Quadratic Equations",
    "10.4 Use Square Roots to Solve Quadratic Equations",
    "10.5 Square Root Applications",
    "10.6 Completing the Square",
    "10.7 Vertex Form of a Quadratic Equation",
    "10.8 Quadratic Formula",
    "10.9 Comparing Methods for Solving Quadratics",
    "10.10 Solutions Using the Discriminant",
    "10.11 Linear, Exponential, and Quadratic Models",
    "10.12 Applications of Function Models",
    "11.1 Graphs of Square Root Functions",
    "11.2 Shifts of Square Root Functions",
    "11.3 Raising a Product or Quotient to a Power",
    "11.4 Simplification of Radical Expressions",
    "11.5 Applications Using Radicals",
    "11.6 Radical Equations",
    "11.7 Equations with Radicals on Both Sides",
    "11.8 Pythagorean Theorem and its Converse",
    "11.9 Solving Equations Using the Pythagorean Theorem",
    "11.10 Applications Using the Pythagorean Theorem",
    "11.11 Distance Formula",
    "11.12 Midpoint Formula",
    "12.1 Inverse Variation Models",
    "12.2 Graphs of Rational Functions",
    "12.3 Horizontal and Vertical Asymptotes",
    "12.4 Inverse Variation Problems",
    "12.5 Division of Polynomials",
    "12.6 Determining Asymptotes by Division",
    "12.7 Excluded Values for Rational Expressions",
    "12.8 Multiplication of Rational Expressions",
    "12.9 Division of Rational Expressions",
    "12.10 Addition and Subtraction of Rational Expressions",
    "12.11 Applications of Adding and Subtracting Rational Expressions",
    "12.12 Rational Equations Using Proportions",
    "12.13 Applications Using Rational Equations",
    "13.1 Measurement of Probability",
    "13.2 Empirical Probability",
    "13.3 Permutations",
    "13.4 Probability and Permutations",
    "13.5 Combinations",
    "13.6 Probability and Combinations",
    "13.7 Mutually Exclusive Events",
    "13.8 Independence versus Dependence",
    "13.9 Measures of Central Tendency and Dispersion",
    "13.10 Measures of Spread-Dispersion",
    "13.11 Stem-and-Leaf Plots and Histograms",
    "13.12 Box-and-Whisker Plots",
    "13.13 Sampling methods",
    "13.14 Planning and Conducting Surveys",
]

# ── Helpers ────────────────────────────────────────────────────────────────────
def slugify(title):
    """Convert '1.1 Definition of Variable' → '1-1-definition-of-variable'"""
    s = title.lower()
    s = re.sub(r'[^a-z0-9\s-]', '', s)   # remove punctuation except hyphen
    s = re.sub(r'[\s]+', '-', s.strip())  # spaces → hyphens
    s = re.sub(r'-+', '-', s)             # collapse multiple hyphens
    return s

def make_identifier(slug):
    return "res_" + slug.replace("-", "_")

# ── Build file contents ────────────────────────────────────────────────────────
def html_content(title):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<title>Assignment: {title}</title>
</head>
<body>
<div class="pw-canvas">
  <div class="pw-lesson-header">
    <h1>Lesson Instructions</h1>
  </div>
  <div class="pw-lesson-div">
    <p>For this lesson, you will use a linked tool. To get started, click below.</p>
  </div>
</div>
</body>
</html>
"""

def assignment_settings_content(identifier, title, position):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<assignment identifier="{identifier}"
  xmlns="http://canvas.instructure.com/xsd/cccv1p0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd">
  <title>{title}</title>
  <due_at/>
  <lock_at/>
  <unlock_at/>
  <module_locked>false</module_locked>
  <workflow_state>published</workflow_state>
  <assignment_overrides></assignment_overrides>
  <allowed_extensions></allowed_extensions>
  <has_group_category>false</has_group_category>
  <points_possible>100.0</points_possible>
  <grading_type>percent</grading_type>
  <all_day>false</all_day>
  <submission_types>external_tool</submission_types>
  <position>{position}</position>
  <turnitin_enabled>false</turnitin_enabled>
  <vericite_enabled>false</vericite_enabled>
  <peer_review_count>0</peer_review_count>
  <peer_reviews>false</peer_reviews>
  <automatic_peer_reviews>false</automatic_peer_reviews>
  <anonymous_peer_reviews>false</anonymous_peer_reviews>
  <grade_group_students_individually>false</grade_group_students_individually>
  <freeze_on_copy>false</freeze_on_copy>
  <omit_from_final_grade>false</omit_from_final_grade>
  <hide_in_gradebook>false</hide_in_gradebook>
  <intra_group_peer_reviews>false</intra_group_peer_reviews>
  <only_visible_to_overrides>false</only_visible_to_overrides>
  <post_to_sis>false</post_to_sis>
  <moderated_grading>false</moderated_grading>
  <grader_count>0</grader_count>
  <grader_comments_visible_to_graders>true</grader_comments_visible_to_graders>
  <anonymous_grading>false</anonymous_grading>
  <graders_anonymous_to_graders>false</graders_anonymous_to_graders>
  <grader_names_visible_to_final_grader>true</grader_names_visible_to_final_grader>
  <anonymous_instructor_annotations>false</anonymous_instructor_annotations>
  <external_tool_external_identifier>15</external_tool_external_identifier>
  <external_tool_url>https://flexbooks.ck12.org/auth/launch/lti/ltiApp/PLACEHOLDER</external_tool_url>
  <external_tool_data_json>""</external_tool_data_json>
  <external_tool_link_settings_json>{{"selection_width":"","selection_height":""}}</external_tool_link_settings_json>
  <external_tool_new_tab>true</external_tool_new_tab>
  <post_policy>
    <post_manually>false</post_manually>
  </post_policy>
</assignment>
"""

# ── Build manifest ─────────────────────────────────────────────────────────────
def build_manifest(entries):
    items_xml = ""
    resources_xml = ""
    for identifier, slug, title, folder, html_file, _ in entries:
        items_xml += f'        <item identifier="item_{identifier}" identifierref="{identifier}">\n'
        items_xml += f'          <title>{title}</title>\n'
        items_xml += f'        </item>\n'
        resources_xml += f'    <resource identifier="{identifier}" type="associatedcontent/imscc_xmlv1p1/learning-application-resource" href="{folder}/{html_file}">\n'
        resources_xml += f'      <file href="{folder}/{html_file}"/>\n'
        resources_xml += f'      <file href="{folder}/assignment_settings.xml"/>\n'
        resources_xml += f'    </resource>\n'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="g_ck12_pathway_rewrite"
  xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
  xmlns:lom="http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource"
  xmlns:lomimscc="http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1 http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imscp_v1p2_v1p0.xsd">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.1.0</schemaversion>
    <lomimscc:lom>
      <lomimscc:general>
        <lomimscc:title>
          <lomimscc:string>CK-12 Content Pathway Rewrite</lomimscc:string>
        </lomimscc:title>
      </lomimscc:general>
    </lomimscc:lom>
  </metadata>
  <organizations>
    <organization identifier="org_1" structure="rooted-hierarchy">
      <item identifier="LearningModules">
{items_xml}      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="g_course_settings" type="associatedcontent/imscc_xmlv1p1/learning-application-resource" href="course_settings/canvas_export.txt">
      <file href="course_settings/canvas_export.txt"/>
      <file href="course_settings/module_meta.xml"/>
      <file href="course_settings/assignment_groups.xml"/>
    </resource>
{resources_xml}  </resources>
</manifest>
"""

# ── Course settings stubs ──────────────────────────────────────────────────────
CANVAS_EXPORT_TXT = "This file is required by Canvas for Common Cartridge import.\n"
MODULE_META_XML = """<?xml version="1.0" encoding="UTF-8"?>
<modules xmlns="http://canvas.instructure.com/xsd/cccv1p0"></modules>
"""
ASSIGNMENT_GROUPS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<assignmentGroups xmlns="http://canvas.instructure.com/xsd/cccv1p0"></assignmentGroups>
"""

# ── Main ───────────────────────────────────────────────────────────────────────
entries = []
for i, title in enumerate(assignments, start=1):
    slug = slugify(title)
    identifier = make_identifier(slug)
    folder = slug
    html_file = slug + ".html"
    entries.append((identifier, slug, title, folder, html_file, i))

zip_path = "ck12_pathway_canvas_import.imscc"

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    # manifest
    zf.writestr("imsmanifest.xml", build_manifest(entries))
    # course settings
    zf.writestr("course_settings/canvas_export.txt", CANVAS_EXPORT_TXT)
    zf.writestr("course_settings/module_meta.xml", MODULE_META_XML)
    zf.writestr("course_settings/assignment_groups.xml", ASSIGNMENT_GROUPS_XML)
    # per-assignment files
    for identifier, slug, title, folder, html_file, position in entries:
        zf.writestr(f"{folder}/{html_file}", html_content(title))
        zf.writestr(f"{folder}/assignment_settings.xml",
                    assignment_settings_content(identifier, title, position))

print(f"✅ Created: {zip_path}")
print(f"   {len(entries)} assignments across chapters 1–13")
print(f"   Ready to import into Canvas (Content > Import Course Content > Common Cartridge)")
