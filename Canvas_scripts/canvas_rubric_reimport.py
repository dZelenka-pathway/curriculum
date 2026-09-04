#!/usr/bin/env python3
"""
canvas_rubric_reimport.py

Fully reimports a rubric from a Canvas-format CSV, preserving which
assignments it was attached to.

Per course:
  1. Find every rubric titled RUBRIC_TITLE (there may be more than one after
     earlier duplicate-creating runs -- all of them are handled).
  2. Record every assignment currently linked to any of them, along with its
     use_for_grading / hide_* display settings.
  3. Back up the full rubric definitions, their associations, and ALL existing
     rubric assessments to a JSON file.
  4. Unlink: delete each grading rubric_association found.
  5. Delete the rubric(s).
  6. Re-import the rubric fresh from RUBRIC_CSV.
  7. Re-attach it to every assignment recorded in step 2, with
     "Use this rubric for assignment grading" set.

*** WHAT THIS DOES AND DOESN'T TOUCH ***
Deleting a rubric deletes its rubric assessments -- the criterion-level clicks
and comments entered through the rubric grid. Submission scores in the
gradebook live on the submission record and are NOT affected, recomputed, or
cleared, even where the rubric was used for grading.

So the loss is student-visible feedback detail, not grades. The reimported
rubric has new criterion ids, so old assessments cannot be remapped onto it by
this script or by hand; they are archived to the backup JSON for reference.
The script reports the count and proceeds. Pass --strict-assessments if you
would rather it stop and make you confirm.

One thing to expect afterwards: on assignments that already have scores,
SpeedGrader will show the fresh rubric with an empty grid next to the existing
grade. If a grader then fills in that grid on a use_for_grading association,
the rubric total overwrites the current score.

Run modes:
  python canvas_rubric_reimport.py                        # dry run, writes nothing
  python canvas_rubric_reimport.py --apply                # execute
  python canvas_rubric_reimport.py --courses 771          # override COURSE_IDS
  python canvas_rubric_reimport.py --include-keyword Exam # also attach to keyword matches
  python canvas_rubric_reimport.py --apply --strict-assessments   # stop if assessments exist
  python canvas_rubric_reimport.py --restore FILE --apply # recreate the OLD rubric + links

Always --apply against ONE test course first and check it in the Canvas UI
before running the full COURSE_IDS list.
"""

import argparse
import copy
import csv
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

# Prefer an env var so the token stays out of the file:
#   Windows:  set CANVAS_API_TOKEN=.....
#   mac/linux: export CANVAS_API_TOKEN="....."
API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "token goes here")

COURSE_IDS = [
    772,
]
# 771, 772, 802, 801, 803, 804, 805, 806, 807, 808, 809, 810, 797, 800,

# Canvas-format rubric CSV to import.
RUBRIC_CSV = "Flint_exam_Rubric5PointMath.csv"

# Title of the rubric to tear down. None = use the "Rubric Name" column
# from the CSV, which is also what the new rubric gets titled.
RUBRIC_TITLE = None

# Title for the reimported rubric. None = same as RUBRIC_TITLE, which is
# the point of a reimport (same title, fresh contents).
NEW_TITLE = None

# Applied to every re-created association. This is the Canvas checkbox
# "Use this rubric for assignment grading."
USE_FOR_GRADING = True

# If True, carry each assignment's previous hide_score_total / hide_points /
# hide_outcome_results forward instead of using the defaults below.
PRESERVE_DISPLAY_SETTINGS = True
HIDE_SCORE_TOTAL = False
HIDE_POINTS = False
HIDE_OUTCOME_RESULTS = False

BACKUP_DIR = "canvas_rubric_backups"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
}


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


def canvas_delete(path):
    """DELETE that treats 404 as 'already gone', which is the outcome we want."""
    resp = requests.delete(CANVAS_URL + path, headers=HEADERS)
    if resp.status_code == 404:
        return {"already_removed": True}
    _check(resp)
    try:
        return resp.json()
    except ValueError:
        return {}


# --------------------------------------------------------------------------
# CSV PARSING
# --------------------------------------------------------------------------
#
# Canvas rubric CSV layout (one row per criterion):
#
#   Rubric Name, Criteria Name, Criteria Description, Criteria Enable Range,
#   [Rating Name, Rating Description, Rating Points] x N
#
# Mapping into the Canvas API shape:
#   Criteria Name        -> criterion["description"]
#   Criteria Description -> criterion["long_description"]
#   Rating Name          -> rating["description"]
#   Rating Description   -> rating["long_description"]
#   criterion["points"]  -> max of that criterion's rating points

FIXED_COLS = 4


def _truthy(val):
    return str(val).strip().lower() in ("true", "yes", "y", "1")


def parse_rubric_csv(path):
    """Returns (rubric_title, criteria_list)."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if len(rows) < 2:
        raise RuntimeError(f"{path}: expected a header row plus at least one criterion row.")

    header = rows[0]
    if header[:2] != ["Rubric Name", "Criteria Name"]:
        raise RuntimeError(
            f"{path}: unexpected header. Expected a Canvas rubric export starting with "
            f"'Rubric Name,Criteria Name,...'. Got: {header[:4]}"
        )

    titles = set()
    criteria = []

    for lineno, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) < FIXED_COLS:
            raise RuntimeError(f"{path} line {lineno}: only {len(row)} columns.")

        titles.add(row[0].strip())

        ratings = []
        for i in range(FIXED_COLS, len(row), 3):
            chunk = row[i:i + 3]
            if len(chunk) < 3:
                break
            name, desc, points = (c.strip() for c in chunk)
            if not name and not desc and not points:
                continue
            if not points:
                raise RuntimeError(f"{path} line {lineno}: rating '{name}' has no point value.")
            try:
                pts = float(points)
            except ValueError:
                raise RuntimeError(
                    f"{path} line {lineno}: rating '{name}' has non-numeric points '{points}'."
                )
            ratings.append({
                "description": name,
                "long_description": desc,
                "points": pts,
            })

        if not ratings:
            raise RuntimeError(f"{path} line {lineno}: criterion '{row[1]}' has no ratings.")

        ratings.sort(key=lambda r: r["points"], reverse=True)

        criteria.append({
            "description": row[1].strip(),
            "long_description": row[2].strip(),
            "criterion_use_range": _truthy(row[3]),
            "points": max(r["points"] for r in ratings),
            "ratings": ratings,
        })

    if len(titles) > 1:
        raise RuntimeError(
            f"{path}: multiple rubric names found ({sorted(titles)}). "
            f"This script imports one rubric at a time."
        )

    return titles.pop(), criteria


def describe_criteria(criteria):
    total = sum(c["points"] for c in criteria)
    lines = [f"  Criteria: {len(criteria)}, total points: {total:g}"]
    for c in criteria:
        rat = ", ".join(f"{r['description']} ({r['points']:g})" for r in c["ratings"])
        lines.append(f"    - {c['description']} [{c['points']:g} pts]: {rat}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CANVAS RUBRIC HELPERS
# --------------------------------------------------------------------------

def _normalize_rubric(rubric):
    """Some Canvas instances return the criteria list under 'data' instead of
    'criteria'. Normalize so the rest of the script can always use
    'criteria'."""
    if isinstance(rubric, dict) and "criteria" not in rubric and "data" in rubric:
        rubric = dict(rubric)
        rubric["criteria"] = rubric["data"]
    return rubric


def find_rubrics_by_title(course_id, title):
    """ALL rubrics with this exact title -- duplicates from earlier runs get
    cleaned up too."""
    rubrics = canvas_get_paginated(f"/api/v1/courses/{course_id}/rubrics")
    return [r for r in rubrics if (r.get("title") or "").strip() == title]


def get_rubric_detail(course_id, rubric_id, fallback=None):
    """Full rubric with criteria plus, where the instance supports it,
    embedded associations and assessments.

    Instances differ in what they return when include[] is passed on a
    course-context rubric, so this tries the rich call, falls back to a plain
    GET, normalizes 'data'->'criteria', and finally falls back to the summary
    object from the list endpoint.
    """
    detail = {}
    try:
        detail = canvas_get(
            f"/api/v1/courses/{course_id}/rubrics/{rubric_id}",
            params={"include[]": ["associations", "assessments"], "style": "full"},
        )
        detail = _normalize_rubric(detail)
    except Exception as e:
        print(f"    (include=associations,assessments fetch failed: {e})")

    if "criteria" not in detail:
        carried = {k: detail.get(k) for k in ("associations", "assessments")
                   if isinstance(detail, dict) and detail.get(k) is not None}
        try:
            plain = _normalize_rubric(canvas_get(f"/api/v1/courses/{course_id}/rubrics/{rubric_id}"))
        except Exception as e:
            plain = {}
            print(f"    (plain rubric fetch failed: {e})")
        if "criteria" in plain:
            plain.update(carried)
            detail = plain

    if "criteria" not in detail:
        fb = _normalize_rubric(fallback) if fallback else None
        if fb and "criteria" in fb:
            print("    (falling back to list-endpoint rubric data; no 'associations' "
                  "available -> relying on the rubric delete to clear links)")
            detail = dict(fb)
        else:
            raise RuntimeError(
                f"Could not find 'criteria' or 'data' in any rubric response for "
                f"id={rubric_id}. Keys returned: {list(detail.keys())}"
            )
    return detail


def rubric_assessment_count(detail):
    """How many rubric assessments exist. Falls back to the summary counter
    some instances expose when the assessments list wasn't returned."""
    assessments = detail.get("assessments")
    if isinstance(assessments, list):
        return len(assessments)
    for key in ("assessments_count", "rubric_assessments_count"):
        val = detail.get(key)
        if isinstance(val, int):
            return val
    return None  # unknown


def grading_associations(detail):
    """Assignment-context grading associations embedded on the rubric."""
    out = []
    for assoc in detail.get("associations", []) or []:
        if assoc.get("association_type") == "Assignment":
            out.append(assoc)
    return out


def delete_rubric(course_id, rubric_id):
    """Canvas removes the rubric's remaining associations as part of this."""
    return canvas_delete(f"/api/v1/courses/{course_id}/rubrics/{rubric_id}")


def delete_association(course_id, association_id):
    return canvas_delete(f"/api/v1/courses/{course_id}/rubric_associations/{association_id}")


# --------------------------------------------------------------------------
# ASSIGNMENT HELPERS
# --------------------------------------------------------------------------

def get_all_assignments(course_id):
    return canvas_get_paginated(f"/api/v1/courses/{course_id}/assignments")


def current_rubric_id(assignment):
    return (assignment.get("rubric_settings") or {}).get("id")


def snapshot_assignment(assignment):
    """Everything needed to rebuild this assignment's association later."""
    rs = assignment.get("rubric_settings") or {}
    return {
        "id": assignment["id"],
        "name": assignment.get("name"),
        "previous_rubric_id": rs.get("id"),
        "previous_rubric_title": rs.get("title"),
        "use_for_grading": bool(assignment.get("use_rubric_for_grading",
                                               rs.get("use_for_grading", False))),
        "hide_score_total": bool(rs.get("hide_score_total", False)),
        "hide_points": bool(rs.get("hide_points", False)),
        "hide_outcome_results": bool(rs.get("hide_outcome_results", False)),
    }


def association_params_for(snap, rubric_id, assignment_id):
    if PRESERVE_DISPLAY_SETTINGS and snap:
        hide_total = snap["hide_score_total"]
        hide_pts = snap["hide_points"]
        hide_outcome = snap["hide_outcome_results"]
    else:
        hide_total, hide_pts, hide_outcome = (HIDE_SCORE_TOTAL, HIDE_POINTS,
                                              HIDE_OUTCOME_RESULTS)
    return [
        ("rubric_association[rubric_id]", rubric_id),
        ("rubric_association[association_id]", assignment_id),
        ("rubric_association[association_type]", "Assignment"),
        ("rubric_association[purpose]", "grading"),
        # "Use this rubric for assignment grading"
        ("rubric_association[use_for_grading]", str(bool(USE_FOR_GRADING)).lower()),
        ("rubric_association[hide_score_total]", str(hide_total).lower()),
        ("rubric_association[hide_points]", str(hide_pts).lower()),
        ("rubric_association[hide_outcome_results]", str(hide_outcome).lower()),
    ]


def associate_rubric_to_assignment(course_id, rubric_id, assignment_id, snap=None):
    return canvas_post(f"/api/v1/courses/{course_id}/rubric_associations",
                       association_params_for(snap, rubric_id, assignment_id))


# --------------------------------------------------------------------------
# RUBRIC CREATION
# --------------------------------------------------------------------------

def build_rubric_create_params(title, criteria, course_id,
                               free_form_criterion_comments=False):
    params = [
        ("rubric[title]", title),
        ("rubric[free_form_criterion_comments]",
         str(bool(free_form_criterion_comments)).lower()),
        # Bookmark to the course so it appears in the course rubric list
        # without being tied to an assignment yet.
        ("rubric_association[association_type]", "Course"),
        ("rubric_association[association_id]", course_id),
        ("rubric_association[purpose]", "bookmark"),
    ]
    for i, crit in enumerate(criteria):
        prefix = f"rubric[criteria][{i}]"
        params.append((f"{prefix}[description]", crit.get("description", "") or ""))
        if crit.get("long_description"):
            params.append((f"{prefix}[long_description]", crit["long_description"]))
        params.append((f"{prefix}[points]", crit.get("points", 0)))
        if crit.get("criterion_use_range"):
            params.append((f"{prefix}[criterion_use_range]", "true"))
        for j, rating in enumerate(crit.get("ratings", []) or []):
            rprefix = f"{prefix}[ratings][{j}]"
            params.append((f"{rprefix}[description]", rating.get("description", "") or ""))
            if rating.get("long_description"):
                params.append((f"{rprefix}[long_description]", rating["long_description"]))
            params.append((f"{rprefix}[points]", rating.get("points", 0)))
    return params


def create_rubric(course_id, title, criteria, free_form=False):
    params = build_rubric_create_params(title, criteria, course_id, free_form)
    result = canvas_post(f"/api/v1/courses/{course_id}/rubrics", params)
    rubric = _normalize_rubric(result.get("rubric", result))
    return rubric["id"], rubric


# --------------------------------------------------------------------------
# BACKUP / RESTORE
# --------------------------------------------------------------------------

def backup_path(course_id, title):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", title)
    return os.path.join(BACKUP_DIR, f"reimport_course{course_id}_{safe}_{ts}.json")


def write_backup(path, payload):
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  Backup written: {path}")


def restore_from_backup(path, apply_changes):
    """Recreate the pre-reimport rubric definition under a '(restored)' title
    and relink the same assignments to it.

    Rubric ASSESSMENTS cannot be restored through the API. They are archived
    in the backup JSON for reference only.
    """
    with open(path) as f:
        payload = json.load(f)

    course_id = payload["course_id"]
    old_rubrics = payload["old_rubrics"]
    targets = payload["linked_assignments"]

    if not old_rubrics:
        print(f"{path}: no old rubric definitions recorded; nothing to restore.")
        return

    source = old_rubrics[0]["rubric"]
    restore_title = (source.get("title") or payload["rubric_title"]) + " (restored)"

    print(f"\n=== RESTORE: course {course_id} from {path} ===")
    print(f"  Recreate '{restore_title}' from the backed-up definition and "
          f"relink {len(targets)} assignment(s).")
    if len(old_rubrics) > 1:
        print(f"  NOTE: {len(old_rubrics)} rubrics were deleted; restoring the first "
              f"(id={old_rubrics[0]['rubric_id']}) only.")
    archived = sum(len(r.get("assessments") or []) for r in old_rubrics)
    if archived:
        print(f"  NOTE: {archived} archived assessment(s) in this file CANNOT be "
              f"restored via the API. They remain in the JSON for reference.")

    if not apply_changes:
        print("  (dry run - pass --apply together with --restore to execute)")
        return

    new_id, _ = create_rubric(
        course_id, restore_title,
        copy.deepcopy(source["criteria"]),
        source.get("free_form_criterion_comments", False),
    )
    print(f"  Created restored rubric id={new_id}")

    for snap in targets:
        try:
            associate_rubric_to_assignment(course_id, new_id, snap["id"], snap)
            print(f"    Linked [{snap['id']}] '{snap['name']}'")
        except Exception as e:
            print(f"    FAILED on [{snap['id']}] '{snap['name']}': {e}")


# --------------------------------------------------------------------------
# MAIN WORKFLOW
# --------------------------------------------------------------------------

def strip_ids(criteria):
    """Fresh criteria for creation -- Canvas assigns new ids."""
    out = copy.deepcopy(criteria)
    for crit in out:
        crit.pop("id", None)
        for rating in crit.get("ratings", []) or []:
            rating.pop("id", None)
    return out


def process_course(course_id, old_title, new_title, criteria, args):
    print(f"\n=== Course {course_id} ===")

    # ---- 0. locate the rubric(s) --------------------------------------
    summaries = find_rubrics_by_title(course_id, old_title)
    if not summaries:
        print(f"  No rubric titled '{old_title}' in this course.")
        if not args.create_if_missing:
            print("  Nothing to reimport. Pass --create-if-missing to import it anyway.")
            return
        print("  --create-if-missing set: importing fresh.")
    else:
        print(f"  Found {len(summaries)} rubric(s) titled '{old_title}': "
              f"{[s['id'] for s in summaries]}")

    details = []
    for s in summaries:
        d = get_rubric_detail(course_id, s["id"], fallback=s)
        details.append(d)
        n_assess = rubric_assessment_count(d)
        n_assoc = len(grading_associations(d))
        shown = "unknown" if n_assess is None else n_assess
        print(f"    id={s['id']}: {len(d.get('criteria') or [])} criteria, "
              f"{n_assoc} assignment association(s) returned, "
              f"{shown} assessment(s)")

    rubric_ids = {str(s["id"]) for s in summaries}

    # ---- 1. work out which assignments are linked ---------------------
    assignments = get_all_assignments(course_id)
    by_id = {a["id"]: a for a in assignments}

    linked = {}
    for a in assignments:
        if str(current_rubric_id(a)) in rubric_ids:
            linked[a["id"]] = snapshot_assignment(a)

    # Also pick up anything the rubric's own association list names but whose
    # assignment record doesn't reflect (stale rubric_settings).
    for d in details:
        for assoc in grading_associations(d):
            aid = assoc.get("association_id")
            if aid and aid not in linked:
                a = by_id.get(aid)
                if a:
                    snap = snapshot_assignment(a)
                    snap["found_via"] = "rubric_association"
                    linked[aid] = snap

    # Optional widening: assignments matching a title keyword.
    if args.include_keyword:
        kw = args.include_keyword.lower()
        added = 0
        for a in assignments:
            if kw in (a.get("name") or "").lower() and a["id"] not in linked:
                snap = snapshot_assignment(a)
                snap["found_via"] = f"keyword:{args.include_keyword}"
                linked[a["id"]] = snap
                added += 1
        if added:
            print(f"  --include-keyword '{args.include_keyword}' added {added} "
                  f"assignment(s) that weren't previously linked.")

    targets = list(linked.values())
    print(f"  Assignments to re-attach after reimport: {len(targets)}")
    for snap in targets:
        via = f", via {snap['found_via']}" if snap.get("found_via") else ""
        print(f"    - [{snap['id']}] {snap['name']} "
              f"(was rubric={snap['previous_rubric_id']}, "
              f"use_for_grading={snap['use_for_grading']}{via})")

    # ---- assessment safety gate ---------------------------------------
    known = [rubric_assessment_count(d) for d in details]
    total_assess = sum(n for n in known if isinstance(n, int))
    unknown = any(n is None for n in known)

    if args.strict_assessments and not args.force and (total_assess or (unknown and summaries)):
        shown = total_assess if total_assess else "an unknown number of"
        print(f"\n  STOP (--strict-assessments): {shown} rubric assessment(s) on this "
              f"rubric. Re-run with --force to proceed.")
        return
    if total_assess:
        print(f"\n  NOTE: {total_assess} rubric assessment(s) will be archived to the "
              f"backup JSON and then lost. Gradebook scores are unaffected -- what goes "
              f"away is the criterion-level clicks and comments students see as feedback.")
    elif unknown and summaries:
        print("\n  NOTE: this instance did not report assessment counts, so any existing "
              "criterion-level clicks and comments cannot be archived before deletion. "
              "Gradebook scores are unaffected.")

    # ---- backup --------------------------------------------------------
    payload = {
        "course_id": course_id,
        "rubric_title": old_title,
        "new_title": new_title,
        "csv": args.csv,
        "use_for_grading": USE_FOR_GRADING,
        "old_rubrics": [
            {
                "rubric_id": d.get("id"),
                "rubric": d,
                "associations": grading_associations(d),
                "assessments": d.get("assessments") or [],
            }
            for d in details
        ],
        "linked_assignments": targets,
        "new_criteria": criteria,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if not args.apply:
        print("\n  DRY RUN - no changes made. Re-run with --apply to execute.")
        print(f"  Plan: unlink {sum(len(grading_associations(d)) for d in details)} "
              f"association(s), delete {len(summaries)} rubric(s), "
              f"create '{new_title}' from {args.csv}, "
              f"attach to {len(targets)} assignment(s) with "
              f"use_for_grading={str(USE_FOR_GRADING).lower()}.")
        return

    bpath = backup_path(course_id, old_title)
    write_backup(bpath, payload)

    # ---- 2. unlink -----------------------------------------------------
    unlinked = 0
    for d in details:
        for assoc in grading_associations(d):
            aid = assoc.get("id")
            if not aid:
                continue
            try:
                result = delete_association(course_id, aid)
                if result.get("already_removed"):
                    print(f"    Association {aid} already gone.")
                else:
                    print(f"    Unlinked association {aid} "
                          f"(assignment {assoc.get('association_id')}).")
                unlinked += 1
            except Exception as e:
                print(f"    Could not delete association {aid}: {e}")
    if not unlinked and details:
        print("    No association ids available to delete explicitly; "
              "the rubric delete below clears remaining links.")

    # ---- 3. delete the rubric(s) ---------------------------------------
    deleted = []
    for s in summaries:
        try:
            delete_rubric(course_id, s["id"])
            print(f"    Deleted rubric id={s['id']}.")
            deleted.append(s["id"])
        except Exception as e:
            print(f"    FAILED to delete rubric id={s['id']}: {e}")
            print(f"    (If this rubric lives in an account context rather than the "
                  f"course, delete it from the account rubric list instead.)")

    if summaries and not deleted:
        print("  Aborting before reimport: nothing was deleted, so creating the new "
              "rubric now would leave a duplicate title.")
        payload["aborted"] = "no rubrics deleted"
        write_backup(bpath, payload)
        return

    # Confirm the title is clear so we don't stack duplicates.
    leftover = find_rubrics_by_title(course_id, new_title)
    if leftover:
        print(f"  WARNING: {len(leftover)} rubric(s) titled '{new_title}' still present "
              f"({[r['id'] for r in leftover]}). Creating anyway would duplicate the "
              f"title -- aborting. Remove them in the UI and re-run.")
        payload["aborted"] = f"title still occupied by {[r['id'] for r in leftover]}"
        write_backup(bpath, payload)
        return

    # ---- 4. reimport ---------------------------------------------------
    new_id, new_rubric = create_rubric(course_id, new_title, strip_ids(criteria))
    print(f"    Created rubric id={new_id}, title='{new_title}', "
          f"{len(new_rubric.get('criteria') or [])} criteria, "
          f"{new_rubric.get('points_possible')} points possible.")
    payload["new_rubric_id"] = new_id

    # ---- 5. re-attach --------------------------------------------------
    failures = []
    for snap in targets:
        try:
            associate_rubric_to_assignment(course_id, new_id, snap["id"], snap)
            print(f"    Attached [{snap['id']}] '{snap['name']}' -> rubric {new_id} "
                  f"(use_for_grading={str(USE_FOR_GRADING).lower()})")
        except Exception as e:
            print(f"    FAILED on [{snap['id']}] '{snap['name']}': {e}")
            failures.append({"id": snap["id"], "name": snap["name"], "error": str(e)})

    payload["failures"] = failures
    write_backup(bpath, payload)

    if failures:
        print(f"\n  {len(failures)} of {len(targets)} assignment(s) failed to attach. "
              f"The new rubric (id={new_id}) exists; the backup JSON lists exactly "
              f"which assignments still need linking.")
    else:
        print(f"  All {len(targets)} assignment(s) attached successfully.")
    print(f"  Done with course {course_id}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Actually perform changes (default is dry run).")
    ap.add_argument("--strict-assessments", action="store_true",
                    help="Refuse to run on a rubric that has existing assessments "
                         "(criterion clicks/comments) unless --force is also given. "
                         "Off by default: gradebook scores are not affected by the "
                         "delete, so the reimport proceeds and just reports the loss.")
    ap.add_argument("--force", action="store_true",
                    help="Override --strict-assessments.")
    ap.add_argument("--csv", default=RUBRIC_CSV, help="Path to the rubric CSV.")
    ap.add_argument("--courses", nargs="+", type=int, default=None,
                    help="Course ids to process, overriding COURSE_IDS.")
    ap.add_argument("--title", default=None,
                    help="Title of the rubric to reimport (default: the CSV's Rubric Name).")
    ap.add_argument("--include-keyword", default=None, metavar="WORD",
                    help="Also attach the new rubric to assignments whose title contains "
                         "WORD, even if they weren't previously linked (e.g. Exam).")
    ap.add_argument("--create-if-missing", action="store_true",
                    help="If no rubric with that title exists, import it anyway "
                         "(useful with --include-keyword).")
    ap.add_argument("--restore", metavar="BACKUP_JSON",
                    help="Recreate the pre-reimport rubric and links from a backup file.")
    args = ap.parse_args()

    if not API_TOKEN or API_TOKEN == "PASTE_TOKEN_HERE" or API_TOKEN.startswith("["):
        sys.exit("Set CANVAS_API_TOKEN in your environment (or edit API_TOKEN) before running.")

    if args.restore:
        restore_from_backup(args.restore, args.apply)
        return

    try:
        csv_title, criteria = parse_rubric_csv(args.csv)
    except Exception as e:
        sys.exit(f"Could not parse {args.csv}: {e}")

    old_title = args.title or RUBRIC_TITLE or csv_title
    new_title = NEW_TITLE or old_title

    print(f"Reimport target: '{old_title}'")
    print(f"New rubric title: '{new_title}'  (from {args.csv})")
    print(describe_criteria(criteria))

    if not args.apply:
        print("\n*** DRY RUN MODE (no changes will be made). Pass --apply to execute. ***")
    else:
        print("\n*** APPLY MODE - this deletes rubrics and their assessments. ***")

    for course_id in (args.courses if args.courses else COURSE_IDS):
        try:
            process_course(course_id, old_title, new_title, criteria, args)
        except Exception as e:
            print(f"  ERROR in course {course_id}: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
