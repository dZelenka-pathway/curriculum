import json
import re
import requests

CANVAS_URL = "https://pathwaychristian.instructure.com"
API_TOKEN = "[token goes here]"

COURSE_IDS = [
    797
]
#771, 772, 802, 801, 803, 804, 805, 806, 807, 808, 809, 810, 797, 800,


RUBRIC_TITLE = "Notebook Check"  # must match EXACTLY what's in Canvas right now

FIND_TEXT = "Generally accurate."
REPLACE_TEXT = "Generally accurate. Shows clear understanding."
CASE_SENSITIVE = True

DRY_RUN = False                     # Phase 1 only — backs up and reports, no changes
CONFIRM_DESTRUCTIVE_PHASE = True  # must ALSO be True (with DRY_RUN False) to run Phase 2

BACKUP_FILE = "rubric_full_backup.json"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}


def find_replace(text, find, replace, case_sensitive):
    if not text:
        return text, 0
    if case_sensitive:
        return text.replace(find, replace), text.count(find)
    pattern = re.compile(re.escape(find), re.IGNORECASE)
    new_text, count = pattern.subn(replace, text)
    return new_text, count


def build_criteria_payload(criteria_data):
    total_matches = 0
    criteria_payload = {}
    for idx, criterion in enumerate(criteria_data or [], start=1):
        crit_desc, c1 = find_replace(criterion.get("description"), FIND_TEXT, REPLACE_TEXT, CASE_SENSITIVE)
        crit_long, c2 = find_replace(criterion.get("long_description"), FIND_TEXT, REPLACE_TEXT, CASE_SENSITIVE)
        total_matches += c1 + c2

        ratings_payload = {}
        for r_idx, rating in enumerate(criterion.get("ratings") or [], start=1):
            r_desc, c3 = find_replace(rating.get("description"), FIND_TEXT, REPLACE_TEXT, CASE_SENSITIVE)
            r_long, c4 = find_replace(rating.get("long_description"), FIND_TEXT, REPLACE_TEXT, CASE_SENSITIVE)
            total_matches += c3 + c4
            ratings_payload[str(r_idx)] = {
                "id": rating.get("id"),
                "description": r_desc,
                "long_description": r_long or "",
                "points": rating.get("points"),
            }

        criteria_payload[str(idx)] = {
            "id": criterion.get("id"),
            "description": crit_desc,
            "long_description": crit_long or "",
            "points": criterion.get("points"),
            "criterion_use_range": criterion.get("criterion_use_range", False),
            "ratings": ratings_payload,
        }
    return criteria_payload, total_matches


def get_rubric_for_course(course_id):
    """Find the rubric matching RUBRIC_TITLE in this course, with full detail + associations."""
    list_resp = requests.get(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/rubrics",
        headers=headers, params={"per_page": 100},
    )
    if list_resp.status_code != 200:
        print(f"  Failed to list rubrics: HTTP {list_resp.status_code}")
        return None

    for summary in list_resp.json():
        if summary.get("title") != RUBRIC_TITLE:
            continue
        detail_resp = requests.get(
            f"{CANVAS_URL}/api/v1/courses/{course_id}/rubrics/{summary['id']}",
            headers=headers, params={"include[]": "associations"},
        )
        if detail_resp.status_code != 200:
            print(f"  Failed to fetch rubric detail: HTTP {detail_resp.status_code}")
            return None
        return detail_resp.json()
    print(f"  No rubric titled '{RUBRIC_TITLE}' found")
    return None


def backup_graded_submissions(course_id, assignment_id):
    resp = requests.get(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions",
        headers=headers, params={"per_page": 100, "include[]": "rubric_assessment"},
    )
    if resp.status_code != 200:
        print(f"    Failed to fetch submissions for assignment {assignment_id}: HTTP {resp.status_code}")
        return []

    graded = []
    for s in resp.json():
        ra = s.get("rubric_assessment")
        if ra:
            graded.append({
                "user_id": s["user_id"],
                "submission_id": s["id"],
                "rubric_assessment": ra,
            })
    return graded


def create_association_and_get_id(course_id, rubric_id, assignment_id, use_for_grading,
                                    purpose, hide_score_total, hide_points, hide_outcome_results):
    """POST a new rubric_association and resolve its id, whatever shape Canvas returns it in."""
    resp = requests.post(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/rubric_associations",
        headers=headers,
        json={"rubric_association": {
            "rubric_id": rubric_id,
            "association_id": assignment_id,
            "association_type": "Assignment",
            "use_for_grading": use_for_grading,
            "purpose": purpose,
            "hide_score_total": hide_score_total,
            "hide_points": hide_points,
            "hide_outcome_results": hide_outcome_results,
        }},
    )

    if resp.status_code not in (200, 201):
        print(f"  ✗ Failed to relink assignment {assignment_id}: HTTP {resp.status_code} - {resp.text}")
        return None

    body = resp.json()
    candidate_id = None
    if isinstance(body, dict):
        if "id" in body:
            candidate_id = body["id"]
        elif "rubric_association" in body and isinstance(body["rubric_association"], dict):
            candidate_id = body["rubric_association"].get("id")

    if candidate_id:
        print(f"  ✓ Relinked assignment {assignment_id} (association id {candidate_id})")
        return candidate_id

    print(f"  ⚠ Unexpected response shape for assignment {assignment_id}, re-fetching to confirm link...")
    print(f"    Raw response: {resp.text}")

    detail = requests.get(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/rubrics/{rubric_id}",
        headers=headers, params={"include[]": "associations"},
    ).json()

    for assoc in detail.get("associations", []):
        if assoc.get("association_type") == "Assignment" and assoc.get("association_id") == assignment_id:
            print(f"  ✓ Confirmed via re-fetch: assignment {assignment_id} linked (association id {assoc['id']})")
            return assoc["id"]

    print(f"  ✗ Could not confirm assignment {assignment_id} is linked — CHECK MANUALLY")
    return None


def verify_rubric_survived(course_id, rubric_id, expected_title):
    """Post-edit sanity check: confirm the rubric is still listed with the right title."""
    list_resp = requests.get(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/rubrics",
        headers=headers, params={"per_page": 100},
    )
    if list_resp.status_code != 200:
        print(f"  ⚠ Could not verify rubric list: HTTP {list_resp.status_code}")
        return False

    for r in list_resp.json():
        if r["id"] == rubric_id:
            if r.get("title") == expected_title:
                print(f"  ✓ Verified: rubric {rubric_id} still listed as '{expected_title}'")
                return True
            print(f"  ⚠ Rubric {rubric_id} found but title is now '{r.get('title')}' (expected '{expected_title}')")
            return False

    print(f"  ✗ Rubric {rubric_id} no longer appears in the course rubric list at all")
    return False


# ---------------- PHASE 1: BACKUP + REPORT ----------------
full_backup = []

for course_id in COURSE_IDS:
    print(f"\n--- Course {course_id} ---")
    rubric = get_rubric_for_course(course_id)
    if not rubric:
        continue

    print(f"  Found rubric '{rubric['title']}' (id={rubric['id']}), "
          f"points_possible={rubric.get('points_possible')}")

    criteria_payload, match_count = build_criteria_payload(rubric.get("data"))
    print(f"  {match_count} text match(es) found for replacement")

    assoc_list = [a for a in rubric.get("associations", []) if a.get("association_type") == "Assignment"]
    print(f"  {len(assoc_list)} assignment association(s)")

    entry = {
        "course_id": course_id,
        "rubric_id": rubric["id"],
        "rubric_title": rubric["title"],
        "free_form_criterion_comments": rubric.get("free_form_criterion_comments", False),
        "points_possible_before": rubric.get("points_possible"),
        "original_data": rubric.get("data"),
        "criteria_payload": criteria_payload,
        "match_count": match_count,
        "associations": [],
    }

    for assoc in assoc_list:
        assignment_id = assoc["association_id"]
        graded = backup_graded_submissions(course_id, assignment_id)
        if graded:
            print(f"    Assignment {assignment_id}: {len(graded)} graded submission(s) — will restore after edit")

        entry["associations"].append({
            "old_association_id": assoc["id"],
            "assignment_id": assignment_id,
            "use_for_grading": assoc.get("use_for_grading", True),
            "purpose": assoc.get("purpose", "grading"),
            "hide_score_total": assoc.get("hide_score_total", False),
            "hide_points": assoc.get("hide_points", False),
            "hide_outcome_results": assoc.get("hide_outcome_results", False),
            "graded_submissions": graded,
        })

    full_backup.append(entry)

with open(BACKUP_FILE, "w") as f:
    json.dump(full_backup, f, indent=2)
print(f"\nBackup written to {BACKUP_FILE}")

if DRY_RUN:
    print("\nDRY RUN — Phase 1 only. Review the backup file, then set DRY_RUN=False and "
          "CONFIRM_DESTRUCTIVE_PHASE=True to run Phase 2.")
    raise SystemExit

if not CONFIRM_DESTRUCTIVE_PHASE:
    print("\nDRY_RUN is False but CONFIRM_DESTRUCTIVE_PHASE is False — stopping before Phase 2 as a safety check.")
    raise SystemExit

# ---------------- PHASE 2: UNLINK -> EDIT -> VERIFY -> RELINK -> RESTORE ----------------
for entry in full_backup:
    course_id = entry["course_id"]
    rubric_id = entry["rubric_id"]

    if entry["match_count"] == 0:
        print(f"\nCourse {course_id}: no text changes needed, skipping")
        continue

    print(f"\n=== Course {course_id}: editing rubric '{entry['rubric_title']}' ===")

    for assoc in entry["associations"]:
        del_resp = requests.delete(
            f"{CANVAS_URL}/api/v1/courses/{course_id}/rubric_associations/{assoc['old_association_id']}",
            headers=headers,
        )
        print(f"  Unlinked assignment {assoc['assignment_id']}: HTTP {del_resp.status_code}")

    # Edit — title and free_form_criterion_comments are ALWAYS resent to prevent Canvas
    # from treating an omitted field as "clear it," which caused the earlier title-loss bug
    edit_resp = requests.put(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/rubrics/{rubric_id}",
        headers=headers,
        json={"rubric": {
            "title": entry["rubric_title"],
            "free_form_criterion_comments": entry["free_form_criterion_comments"],
            "criteria": entry["criteria_payload"],
        }},
    )
    print(f"  Edited rubric text: HTTP {edit_resp.status_code}")
    if edit_resp.status_code != 200:
        print(f"    {edit_resp.text}")
        print("  ABORTING relink for this course — fix manually, associations are currently deleted!")
        continue

    response_rubric = edit_resp.json().get("rubric", {})
    new_points_possible = response_rubric.get("points_possible")
    returned_rubric_id = response_rubric.get("id")

    if returned_rubric_id != rubric_id:
        print(f"  ⚠ WARNING: edit returned a DIFFERENT rubric id ({returned_rubric_id} vs {rubric_id}) — "
              f"Canvas may have created a new version. Using the returned id for relinking.")
        rubric_id = returned_rubric_id

    if new_points_possible != entry["points_possible_before"]:
        print(f"  ⚠ points_possible changed: {entry['points_possible_before']} -> {new_points_possible} "
              f"(verify this was intentional)")
    else:
        print(f"  points_possible unchanged ({new_points_possible}) ✓")

    # Verify the rubric is still visibly listed with the right title before relinking anything
    if not verify_rubric_survived(course_id, rubric_id, entry["rubric_title"]):
        print("  ABORTING relink for this course — rubric didn't survive the edit as expected, investigate first!")
        continue

    for assoc in entry["associations"]:
        new_assoc_id = create_association_and_get_id(
            course_id, rubric_id, assoc["assignment_id"],
            assoc["use_for_grading"], assoc["purpose"],
            assoc["hide_score_total"], assoc["hide_points"], assoc["hide_outcome_results"],
        )
        if new_assoc_id is None:
            print(f"  Skipping grade restore for assignment {assoc['assignment_id']} — not linked")
            continue

        for graded in assoc["graded_submissions"]:
            restore_payload = {"rubric_assessment": {
                "user_id": graded["user_id"],
                "assessment_type": "grading",
            }}
            for criterion_id, data in graded["rubric_assessment"].items():
                restore_payload["rubric_assessment"][f"criterion_{criterion_id}"] = {
                    "points": data.get("points"),
                    "comments": data.get("comments", ""),
                }

            restore_resp = requests.post(
                f"{CANVAS_URL}/api/v1/courses/{course_id}/rubric_associations/{new_assoc_id}/rubric_assessments",
                headers=headers,
                json=restore_payload,
            )
            if restore_resp.status_code in (200, 201):
                print(f"      ✓ Restored grade for user {graded['user_id']}")
            else:
                print(f"      ✗ Failed to restore grade for user {graded['user_id']}: "
                      f"HTTP {restore_resp.status_code} - {restore_resp.text}")

print("\nDone. Spot-check SpeedGrader on at least one previously-graded assignment per course.")