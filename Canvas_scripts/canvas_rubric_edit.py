#!/usr/bin/env python3
"""
canvas_rubric_edit.py

Canvas doesn't let you edit rubric criteria text in place once a rubric has
been used for grading. This script:

  1. Finds a rubric by exact title in each given course.
  2. Finds every assignment currently linked to that rubric (for grading).
  3. Backs up the full rubric + assignment-link data to a JSON file.
  4. Recreates the rubric under a new title with the text replaced.
  5. Re-links every assignment that was linked to the old rubric, to the new
     one, using the same association settings (use_for_grading,
     hide_score_total, hide_outcome_results, purpose).
  6. Optionally removes the old rubric's grading association from each
     assignment (so the assignment doesn't end up pointing at two rubrics).

Run modes:
  python canvas_rubric_edit.py                  # dry run (default) - prints plan, writes no changes
  python canvas_rubric_edit.py --apply          # actually performs the changes
  python canvas_rubric_edit.py --restore FILE   # re-creates rubric+links from a backup JSON (rollback/debug)

Always run with --apply on ONE test course first and check the result in the
Canvas UI before running against the full COURSE_IDS list.
"""

import argparse
import copy
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone

import requests

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

CANVAS_URL = "https://pathwaychristian.instructure.com"
API_TOKEN = "token goes here"

COURSE_IDS = [
    771, 772, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 797, 800,

]
# 771, 772, 802, 801, 803, 804, 805, 806, 807, 808, 809, 810, 797, 800,

RUBRIC_TITLE = "Exam (Flint) 1"   # must match EXACTLY what's currently in Canvas for each course
NEW_TITLE = "Exam (Flint) "    # what the recreated rubric should be titled (clean, no "(1)" suffixes). Must have a new title

FIND_TEXT = "Completes practice test problems."
REPLACE_TEXT = "Completed practice test."
CASE_SENSITIVE = True

# If True, after linking the new rubric to an assignment, delete the old
# rubric's grading association on that assignment so the assignment only
# points at the new rubric going forward.
DELETE_OLD_ASSOCIATIONS = True

BACKUP_DIR = "canvas_rubric_backups"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
}

TEXT_FIELDS = ("description", "long_description")


# --------------------------------------------------------------------------
# LOW-LEVEL HTTP HELPERS
# --------------------------------------------------------------------------

def _check(resp):
    if not resp.ok:
        raise RuntimeError(
            f"Canvas API error {resp.status_code} for {resp.request.method} "
            f"{resp.request.url}\nBody: {resp.text[:1000]}"
        )
    return resp


def canvas_get_paginated(path, params=None):
    """GET with Canvas Link-header pagination. Returns list of all items."""
    url = CANVAS_URL + path
    params = dict(params or {})
    params.setdefault("per_page", 100)
    items = []
    while url:
        resp = _check(requests.get(url, headers=HEADERS, params=params))
        data = resp.json()
        if isinstance(data, list):
            items.extend(data)
        else:
            items.append(data)
        # follow "next" link if present
        url = None
        params = None
        link = resp.headers.get("Link", "")
        for part in link.split(","):
            part = part.strip()
            m = re.match(r"<([^>]+)>;\s*rel=\"next\"", part)
            if m:
                url = m.group(1)
                break
    return items


def canvas_get(path, params=None):
    resp = _check(requests.get(CANVAS_URL + path, headers=HEADERS, params=params or {}))
    return resp.json()


def canvas_post(path, data):
    resp = _check(requests.post(CANVAS_URL + path, headers=HEADERS, data=data))
    return resp.json()


def canvas_delete(path, params=None):
    resp = _check(requests.delete(CANVAS_URL + path, headers=HEADERS, params=params or {}))
    try:
        return resp.json()
    except ValueError:
        return {}


# --------------------------------------------------------------------------
# CANVAS-SPECIFIC HELPERS
# --------------------------------------------------------------------------

def find_rubric_by_title(course_id, title):
    rubrics = canvas_get_paginated(f"/api/v1/courses/{course_id}/rubrics")
    matches = [r for r in rubrics if r.get("title") == title]
    if not matches:
        return None
    if len(matches) > 1:
        print(f"  WARNING: {len(matches)} rubrics titled '{title}' in course {course_id}; using the first (id={matches[0]['id']}).")
    return matches[0]


def _normalize_rubric(rubric):
    """Some Canvas instances/API versions return the criteria list under
    'data' instead of 'criteria'. Normalize so the rest of the script can
    always use 'criteria'."""
    if isinstance(rubric, dict) and "criteria" not in rubric and "data" in rubric:
        rubric = dict(rubric)
        rubric["criteria"] = rubric["data"]
    return rubric


def get_rubric_detail(course_id, rubric_id, fallback=None):
    """Full rubric with criteria, and (if supported) embedded associations.

    Some Canvas instances return a different/stripped shape when
    include[]=associations is passed on a course-context rubric, and some
    return the criteria list under 'data' instead of 'criteria'. Be
    defensive: try with the include, fall back to a plain GET, normalize
    'data'->'criteria', and finally fall back to the summary object from
    the list endpoint if nothing else has it.
    """
    detail = {}
    try:
        detail = canvas_get(
            f"/api/v1/courses/{course_id}/rubrics/{rubric_id}",
            params={"include[]": "associations"},
        )
        detail = _normalize_rubric(detail)
    except Exception as e:
        print(f"  (include=associations fetch failed: {e})")

    if "criteria" not in detail:
        associations = detail.get("associations") if isinstance(detail, dict) else None
        try:
            plain = canvas_get(f"/api/v1/courses/{course_id}/rubrics/{rubric_id}")
            plain = _normalize_rubric(plain)
        except Exception as e:
            plain = {}
            print(f"  (plain rubric fetch failed: {e})")
        if "criteria" in plain:
            if associations is not None:
                plain["associations"] = associations
            detail = plain

    if "criteria" not in detail:
        fallback = _normalize_rubric(fallback) if fallback else fallback
        if fallback and "criteria" in fallback:
            print("  (falling back to list-endpoint rubric data; no 'associations' available "
                  "-> old association auto-delete will be skipped)")
            detail = dict(fallback)
        else:
            raise RuntimeError(
                f"Could not find 'criteria' or 'data' in any rubric response for id={rubric_id}. "
                f"Keys returned: {list(detail.keys())}"
            )

    return detail


def get_all_assignments(course_id):
    return canvas_get_paginated(f"/api/v1/courses/{course_id}/assignments")


def find_assignments_for_rubric(assignments, rubric_id):
    """Assignments whose current rubric_settings.id matches rubric_id."""
    out = []
    for a in assignments:
        rs = a.get("rubric_settings")
        if rs and str(rs.get("id")) == str(rubric_id):
            out.append(a)
    return out


def build_association_settings(assignment):
    """Pull the grading-relevant association settings off an assignment."""
    rs = assignment.get("rubric_settings", {}) or {}
    return {
        "use_for_grading": bool(assignment.get("use_rubric_for_grading", rs.get("use_for_grading", False))),
        "hide_score_total": bool(rs.get("hide_score_total", False)),
        "hide_points": bool(rs.get("hide_points", False)),
        "hide_outcome_results": bool(rs.get("hide_outcome_results", False)),
    }


# --------------------------------------------------------------------------
# TEXT REPLACEMENT
# --------------------------------------------------------------------------

def replace_text(value):
    if not isinstance(value, str):
        return value
    if CASE_SENSITIVE:
        return value.replace(FIND_TEXT, REPLACE_TEXT)
    else:
        return re.sub(re.escape(FIND_TEXT), REPLACE_TEXT, value, flags=re.IGNORECASE)


def transform_criteria(criteria):
    """Deep-copy criteria list, apply text replacement, strip old IDs so
    Canvas assigns fresh ones on the new rubric."""
    new_criteria = copy.deepcopy(criteria)
    for crit in new_criteria:
        crit.pop("id", None)
        for field in TEXT_FIELDS:
            if field in crit and crit[field] is not None:
                crit[field] = replace_text(crit[field])
        for rating in crit.get("ratings", []) or []:
            rating.pop("id", None)
            for field in TEXT_FIELDS:
                if field in rating and rating[field] is not None:
                    rating[field] = replace_text(rating[field])
    return new_criteria


def count_replacements(criteria):
    n = 0
    needle = FIND_TEXT if CASE_SENSITIVE else FIND_TEXT.lower()
    for crit in criteria:
        for field in TEXT_FIELDS:
            v = crit.get(field)
            if isinstance(v, str):
                hay = v if CASE_SENSITIVE else v.lower()
                n += hay.count(needle)
        for rating in crit.get("ratings", []) or []:
            for field in TEXT_FIELDS:
                v = rating.get(field)
                if isinstance(v, str):
                    hay = v if CASE_SENSITIVE else v.lower()
                    n += hay.count(needle)
    return n


# --------------------------------------------------------------------------
# PARAM BUILDING (Canvas wants bracketed form keys, not JSON, for this endpoint)
# --------------------------------------------------------------------------

def build_rubric_create_params(title, free_form_criterion_comments, criteria,
                                association_type=None, association_id=None,
                                purpose=None, use_for_grading=None,
                                hide_score_total=None):
    params = [
        ("rubric[title]", title),
        ("rubric[free_form_criterion_comments]", str(bool(free_form_criterion_comments)).lower()),
    ]
    for i, crit in enumerate(criteria):
        prefix = f"rubric[criteria][{i}]"
        params.append((f"{prefix}[description]", crit.get("description", "") or ""))
        if crit.get("long_description"):
            params.append((f"{prefix}[long_description]", crit["long_description"]))
        params.append((f"{prefix}[points]", crit.get("points", 0)))
        if "criterion_use_range" in crit:
            params.append((f"{prefix}[criterion_use_range]", str(bool(crit["criterion_use_range"])).lower()))
        for j, rating in enumerate(crit.get("ratings", []) or []):
            rprefix = f"{prefix}[ratings][{j}]"
            params.append((f"{rprefix}[description]", rating.get("description", "") or ""))
            if rating.get("long_description"):
                params.append((f"{rprefix}[long_description]", rating["long_description"]))
            params.append((f"{rprefix}[points]", rating.get("points", 0)))

    if association_type:
        params.append(("rubric_association[association_type]", association_type))
        params.append(("rubric_association[association_id]", association_id))
        params.append(("rubric_association[purpose]", purpose or "bookmark"))
        if use_for_grading is not None:
            params.append(("rubric_association[use_for_grading]", str(bool(use_for_grading)).lower()))
        if hide_score_total is not None:
            params.append(("rubric_association[hide_score_total]", str(bool(hide_score_total)).lower()))

    return params


def create_rubric(course_id, title, free_form_criterion_comments, criteria):
    """Create the new rubric, bookmarked to the course (not attached to any
    assignment yet). Returns the new rubric's id."""
    params = build_rubric_create_params(
        title, free_form_criterion_comments, criteria,
        association_type="Course",
        association_id=course_id,
        purpose="bookmark",
    )
    result = canvas_post(f"/api/v1/courses/{course_id}/rubrics", params)
    rubric = result.get("rubric", result)
    return rubric["id"], rubric


def associate_rubric_to_assignment(course_id, rubric_id, assignment_id, settings):
    params = [
        ("rubric_association[rubric_id]", rubric_id),
        ("rubric_association[association_id]", assignment_id),
        ("rubric_association[association_type]", "Assignment"),
        ("rubric_association[purpose]", "grading"),
        ("rubric_association[use_for_grading]", str(settings["use_for_grading"]).lower()),
        ("rubric_association[hide_score_total]", str(settings["hide_score_total"]).lower()),
        ("rubric_association[hide_points]", str(settings["hide_points"]).lower()),
        ("rubric_association[hide_outcome_results]", str(settings["hide_outcome_results"]).lower()),
    ]
    return canvas_post(f"/api/v1/courses/{course_id}/rubric_associations", params)


def delete_association(course_id, association_id):
    try:
        resp = requests.delete(
            f"{CANVAS_URL}/api/v1/courses/{course_id}/rubric_associations/{association_id}",
            headers=HEADERS,
        )
        if resp.status_code == 404:
            # Canvas only allows one grading association per assignment, so
            # creating the new association often auto-removes the old one.
            # That's the outcome we wanted anyway - not an error.
            return {"already_removed": True}
        _check(resp)
        try:
            return resp.json()
        except ValueError:
            return {}
    except RuntimeError:
        raise


def find_old_grading_association_id(old_rubric_detail, assignment_id):
    """Look inside the embedded 'associations' list (if Canvas returned one)
    for the grading association tied to this assignment."""
    for assoc in old_rubric_detail.get("associations", []) or []:
        if (assoc.get("association_type") == "Assignment"
                and str(assoc.get("association_id")) == str(assignment_id)
                and assoc.get("purpose") == "grading"):
            return assoc.get("id")
    return None


# --------------------------------------------------------------------------
# BACKUP / RESTORE
# --------------------------------------------------------------------------

def backup_path(course_id, rubric_title):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_title = re.sub(r"[^A-Za-z0-9_-]+", "_", rubric_title)
    return os.path.join(BACKUP_DIR, f"course{course_id}_{safe_title}_{ts}.json")


def write_backup(path, payload):
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  Backup written: {path}")


def restore_from_backup(path, apply_changes):
    """Recreate a rubric (with its ORIGINAL, pre-edit criteria) from a backup
    file and re-link it to the same assignments. Use this to undo a bad run."""
    with open(path) as f:
        payload = json.load(f)

    course_id = payload["course_id"]
    old_rubric = payload["old_rubric"]
    assignments = payload["linked_assignments"]
    restore_title = old_rubric["title"] + " (restored)"

    print(f"\n=== RESTORE: course {course_id}, rubric '{old_rubric['title']}' ===")
    print(f"  Will recreate original rubric as '{restore_title}' and relink "
          f"{len(assignments)} assignment(s).")

    if not apply_changes:
        print("  (dry run - pass --apply together with --restore to execute)")
        return

    new_id, _ = create_rubric(
        course_id, restore_title,
        old_rubric.get("free_form_criterion_comments", False),
        copy.deepcopy(old_rubric["criteria"]),
    )
    print(f"  Created restored rubric id={new_id}")

    for a in assignments:
        settings = build_association_settings(a)
        associate_rubric_to_assignment(course_id, new_id, a["id"], settings)
        print(f"    Linked assignment {a['id']} ('{a['name']}')")


# --------------------------------------------------------------------------
# MAIN WORKFLOW
# --------------------------------------------------------------------------

def process_course(course_id, apply_changes, reuse_rubric_id=None):
    print(f"\n=== Course {course_id} ===")

    rubric_summary = find_rubric_by_title(course_id, RUBRIC_TITLE)
    if not rubric_summary:
        print(f"  Rubric '{RUBRIC_TITLE}' not found in this course. Skipping.")
        return

    print(f"  DEBUG rubric_summary keys: {list(rubric_summary.keys())}")
    old_rubric = get_rubric_detail(course_id, rubric_summary["id"], fallback=rubric_summary)
    print(f"  DEBUG old_rubric keys: {list(old_rubric.keys())}")
    old_id = old_rubric["id"]
    print(f"  Found rubric id={old_id}, title='{old_rubric['title']}'")

    assignments = get_all_assignments(course_id)
    linked = find_assignments_for_rubric(assignments, old_id)
    print(f"  Linked assignments: {len(linked)}")
    for a in linked:
        print(f"    - [{a['id']}] {a['name']}")

    n_hits = count_replacements(old_rubric["criteria"])
    print(f"  Occurrences of FIND_TEXT in this rubric's criteria: {n_hits}")
    if n_hits == 0:
        print("  Nothing to replace - skipping this course.")
        return

    # backup before touching anything
    payload = {
        "course_id": course_id,
        "old_rubric": old_rubric,
        "linked_assignments": linked,
        "find_text": FIND_TEXT,
        "replace_text": REPLACE_TEXT,
        "case_sensitive": CASE_SENSITIVE,
        "new_title": NEW_TITLE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    bpath = backup_path(course_id, RUBRIC_TITLE)
    write_backup(bpath, payload)

    new_criteria = transform_criteria(old_rubric["criteria"])

    if not apply_changes:
        print("  DRY RUN - no changes made. Re-run with --apply to execute.")
        print(f"  Plan: create rubric '{NEW_TITLE}', then link "
              f"{len(linked)} assignment(s) to it"
              + (", then remove old associations." if DELETE_OLD_ASSOCIATIONS else "."))
        return

    if reuse_rubric_id:
        new_id = reuse_rubric_id
        print(f"  Reusing existing rubric id={new_id} (skipping creation).")
    else:
        new_id, _ = create_rubric(
            course_id, NEW_TITLE,
            old_rubric.get("free_form_criterion_comments", False),
            new_criteria,
        )
        print(f"  Created new rubric id={new_id}, title='{NEW_TITLE}'")

    # re-fetch assignments so we can skip any that are already linked to new_id
    # (relevant when resuming a partially-completed run)
    current_assignments = {a["id"]: a for a in get_all_assignments(course_id)}

    failures = []
    for a in linked:
        try:
            current = current_assignments.get(a["id"], a)
            current_rubric_id = (current.get("rubric_settings") or {}).get("id")
            if str(current_rubric_id) == str(new_id):
                print(f"    [{a['id']}] '{a['name']}' already linked to rubric {new_id} - skipping.")
                continue

            settings = build_association_settings(a)
            associate_rubric_to_assignment(course_id, new_id, a["id"], settings)
            print(f"    Linked assignment [{a['id']}] '{a['name']}' -> new rubric "
                  f"(use_for_grading={settings['use_for_grading']})")

            if DELETE_OLD_ASSOCIATIONS:
                old_assoc_id = find_old_grading_association_id(old_rubric, a["id"])
                if old_assoc_id:
                    result = delete_association(course_id, old_assoc_id)
                    if result.get("already_removed"):
                        print(f"      Old association {old_assoc_id} was already gone "
                              f"(Canvas auto-removed it when the new one was created).")
                    else:
                        print(f"      Removed old association {old_assoc_id} from this assignment.")
                else:
                    print("      Could not determine old association id "
                          "(Canvas did not return 'associations' on the rubric) - "
                          "leaving old link in place. Check the assignment in the UI.")
        except Exception as e:
            print(f"    FAILED on assignment [{a['id']}] '{a['name']}': {e}")
            failures.append((a["id"], a["name"], str(e)))

    if failures:
        print(f"\n  {len(failures)} of {len(linked)} assignment(s) failed to link - see above. "
              f"Fix and re-run; the new rubric (id={new_id}) already exists, "
              f"so you may want to adjust the script to reuse it rather than creating another.")
    else:
        print(f"  All {len(linked)} assignment(s) linked successfully.")

    payload["new_rubric_id"] = new_id
    write_backup(bpath, payload)  # rewrite with new_rubric_id recorded
    print(f"  Done with course {course_id}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually perform changes (default is dry run).")
    ap.add_argument("--restore", metavar="BACKUP_JSON", help="Restore/rollback from a backup file instead of running the normal edit flow.")
    ap.add_argument("--reuse-rubric-id", type=int, default=None,
                     help="Skip creating a new rubric and instead link assignments to this "
                          "already-created rubric id (for resuming a partially-completed run). "
                          "Only meaningful with a single course id in COURSE_IDS.")
    args = ap.parse_args()

    if API_TOKEN.startswith("["):
        sys.exit("Set API_TOKEN before running.")

    if args.restore:
        restore_from_backup(args.restore, args.apply)
        return

    if not args.apply:
        print("*** DRY RUN MODE (no changes will be made). Pass --apply to execute. ***")

    for course_id in COURSE_IDS:
        try:
            process_course(course_id, args.apply, reuse_rubric_id=args.reuse_rubric_id)
        except Exception as e:
            print(f"  ERROR in course {course_id}: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
