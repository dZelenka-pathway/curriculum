import requests

CANVAS_URL = "https://pathwaychristian.instructure.com"
API_TOKEN = "[token goes here]"  

COURSE_IDS = [771, 772, 802, 801, 803, 804, 805,
    806, 807, 808, 809, 810, 797, 800]

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

for course_id in COURSE_IDS:
    print(f"\n--- Processing Course {course_id} ---")

    # Step 1: list rubrics in the course (include[] is NOT supported here — just get IDs)
    list_url = f"{CANVAS_URL}/api/v1/courses/{course_id}/rubrics"
    list_resp = requests.get(list_url, headers=headers, params={"per_page": 100})

    if list_resp.status_code != 200:
        print(f"Failed to fetch rubrics for Course {course_id}: HTTP {list_resp.status_code}")
        continue

    rubrics = list_resp.json()
    print(f"Found {len(rubrics)} rubric(s)")

    for rubric in rubrics:
        rubric_id = rubric["id"]
        rubric_title = rubric.get("title")

        # Step 2: fetch the single rubric WITH associations (this include DOES work here)
        detail_url = f"{CANVAS_URL}/api/v1/courses/{course_id}/rubrics/{rubric_id}"
        detail_resp = requests.get(
            detail_url, headers=headers, params={"include[]": "associations"}
        )

        if detail_resp.status_code != 200:
            print(f"  Failed to fetch rubric {rubric_id} ({rubric_title}): "
                  f"HTTP {detail_resp.status_code}")
            continue

        detail = detail_resp.json()
        associations = detail.get("associations") or []

        for assoc in associations:
            if assoc.get("association_type") != "Assignment":
                continue

            assignment_id = assoc.get("association_id")

            if assoc.get("use_for_grading"):
                print(f"  = Rubric '{rubric_title}' / Assignment {assignment_id} "
                      f"already set to use for grading")
                continue

            assoc_id = assoc["id"]
            update_url = f"{CANVAS_URL}/api/v1/courses/{course_id}/rubric_associations/{assoc_id}"
            payload = {
                "rubric_association": {
                    "rubric_id": assoc["rubric_id"],
                    "association_id": assoc["association_id"],
                    "association_type": assoc["association_type"],
                    "use_for_grading": True,
                    "purpose": "grading",
                }
            }

            res = requests.put(update_url, headers=headers, json=payload)
            if res.status_code == 200:
                print(f"  ✓ Updated Rubric Association {assoc_id} "
                      f"(Rubric '{rubric_title}' / Assignment {assignment_id})")
            else:
                print(f"  ✗ Failed Association {assoc_id}: HTTP {res.status_code} - {res.text}")
