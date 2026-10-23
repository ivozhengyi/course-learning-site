#!/usr/bin/env python3
"""Audit an exported course inventory. Does not establish semantic correctness."""
import argparse
import json
from collections import Counter
from pathlib import Path


def audit(data):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())

    def records(key):
        rows = data.get(key)
        if not isinstance(rows, list):
            errors.append(f"{key}: expected array")
            return [], {}
        result = {}
        valid = []
        for row in rows:
            if not isinstance(row, dict) or not nonempty(row.get("id")):
                errors.append(f"{key}: record missing string id")
                continue
            rid = row["id"]
            require(rid not in result, f"{key}: duplicate id {rid}")
            result[rid] = row
            valid.append(row)
        return valid, result

    if not isinstance(data, dict):
        return {"ok": False, "errors": ["root: expected object"]}
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(nonempty(data.get("course")), "course is required")
    materials = data.get("materials", {})
    if not isinstance(materials, dict):
        materials = {}
    for kind in ("slides", "papers"):
        require(materials.get(kind) in ("provided", "none"),
                f"materials.{kind}: explicitly confirm provided or none")
    require(nonempty(materials.get("scope_basis")), "materials.scope_basis is required")
    sources, source_map = records("sources")
    chapters, chapter_map = records("chapters")
    topics, topic_map = records("topics")
    lessons, _ = records("lessons")
    questions, _ = records("questions")
    require(bool(chapters), "no chapters")
    require(bool(topics), "no topics")
    require(bool(lessons), "no lessons")
    require(bool(questions), "no questions")
    for source in sources:
        sid = source["id"]
        require(source.get("kind") in ("slides", "paper", "sample", "notes", "textbook", "syllabus", "official"),
                f"source {sid}: invalid kind")
        require(nonempty(source.get("locator")), f"source {sid}: missing file or URL locator")
        if "pages" in source:
            require(type(source["pages"]) is int and source["pages"] > 0,
                    f"source {sid}: pages must be positive integer")
    if materials.get("slides") == "provided":
        require(any(s.get("kind") in ("slides", "notes") for s in sources), "provided slides/notes missing source")
    if materials.get("papers") == "provided":
        require(any(s.get("kind") in ("paper", "sample") for s in sources), "provided papers missing source")
    if materials.get("papers") == "none":
        require(not any(s.get("kind") in ("paper", "sample") for s in sources), "paper sources conflict with materials.papers=none")

    def citations(row, label, mandatory=False, paper=False):
        refs = row.get("citations", [])
        if not isinstance(refs, list):
            errors.append(f"{label}: citations must be array")
            return
        require(not mandatory or bool(refs), f"{label}: missing source citations")
        has_paper = False
        for ref in refs:
            source = source_map.get(ref.get("source")) if isinstance(ref, dict) else None
            if source is None:
                errors.append(f"{label}: unknown source citation")
                continue
            has_paper |= source.get("kind") in ("paper", "sample")
            if "pages" in source:
                page = ref.get("page")
                require(type(page) is int and type(source["pages"]) is int and 1 <= page <= source["pages"],
                        f"{label}: page outside source {source['id']}")
            else:
                require(nonempty(ref.get("section")), f"{label}: non-paged source requires section")
        require(not paper or has_paper, f"{label}: paper claim lacks paper/sample citation")

    def string_list(value, label):
        if not isinstance(value, list) or not all(nonempty(v) for v in value):
            errors.append(f"{label}: expected array of strings")
            return []
        require(len(value) == len(set(value)), f"{label}: duplicate references")
        return value

    graph = {}
    for topic in topics:
        tid = topic["id"]
        require(topic.get("chapter") in chapter_map, f"topic {tid}: unknown chapter")
        require(type(topic.get("core")) is bool, f"topic {tid}: core must be boolean")
        require(nonempty(topic.get("title")), f"topic {tid}: missing title")
        prereqs = string_list(topic.get("prerequisites", []), f"topic {tid} prerequisites")
        graph[tid] = prereqs
        for pre in prereqs:
            require(pre in topic_map, f"topic {tid}: unknown prerequisite {pre}")
        citations(topic, f"topic {tid}", mandatory=True)
    active, done = set(), set()

    def visit(tid):
        if tid in active:
            errors.append(f"prerequisite cycle at {tid}")
            return
        if tid in done or tid not in graph:
            return
        active.add(tid)
        for pre in graph[tid]:
            visit(pre)
        active.remove(tid)
        done.add(tid)

    for tid in graph:
        visit(tid)
    lesson_coverage = set()
    question_coverage = set()
    counts = Counter()
    families = {"learn": set(), "review": set()}

    def linkage(row, label):
        mode = row.get("mode")
        require(mode in ("learn", "review"), f"{label}: invalid mode")
        tids = string_list(row.get("topics"), f"{label} topics")
        require(bool(tids), f"{label}: missing topics")
        for tid in tids:
            require(tid in topic_map, f"{label}: unknown topic {tid}")
        return mode, tids

    def choice(row, label):
        options = row.get("options")
        feedback = row.get("option_feedback")
        if not isinstance(options, list) or len(options) < 2 or not all(nonempty(v) for v in options):
            errors.append(f"{label}: requires at least two nonempty options")
            return
        require(len(set(options)) == len(options), f"{label}: duplicate options")
        require(isinstance(feedback, list) and len(feedback) == len(options) and all(nonempty(v) for v in feedback),
                f"{label}: every option requires feedback")
        answer = row.get("answer")
        require(type(answer) is int and 0 <= answer < len(options), f"{label}: answer must be zero-based option index")

    for lesson in lessons:
        label = f"lesson {lesson['id']}"
        mode, tids = linkage(lesson, label)
        require(nonempty(lesson.get("body")), f"{label}: missing actual teaching body")
        lesson_coverage.update((mode, tid) for tid in tids)
        if mode == "learn":
            require(nonempty(lesson.get("example")), f"{label}: missing concrete example")
            check = lesson.get("classroom_check")
            if not isinstance(check, dict):
                errors.append(f"{label}: missing classroom check")
            else:
                require(nonempty(check.get("prompt")), f"{label}: classroom check missing prompt")
                choice(check, label + " classroom check")
        if mode == "review":
            for field in ("recall_prompt", "conditions"):
                require(nonempty(lesson.get(field)), f"{label}: missing {field}")
    for q in questions:
        label = f"question {q['id']}"
        mode, tids = linkage(q, label)
        require(nonempty(q.get("family")), f"{label}: missing family")
        if mode in families and nonempty(q.get("family")):
            families[mode].add(q["family"])
        require(q.get("chapter") in chapter_map, f"{label}: unknown chapter")
        for tid in tids:
            if tid in topic_map:
                require(topic_map[tid].get("chapter") == q.get("chapter") or q.get("cross_chapter") is True,
                        f"{label}: topic chapter mismatch; mark cross_chapter if intentional")
        require(q.get("difficulty") in ("foundation", "standard", "challenge"), f"{label}: invalid difficulty")
        require(q.get("tier") in ("core", "optional"), f"{label}: invalid tier")
        for field in ("prompt", "explanation", "kind"):
            require(nonempty(q.get(field)), f"{label}: missing {field}")
        require(q.get("grading") in ("auto", "self"), f"{label}: invalid grading")
        answer = q.get("answer")
        has_answer = answer is not None and (not isinstance(answer, (str, list, dict)) or bool(answer))
        if isinstance(answer, str):
            has_answer = bool(answer.strip())
        require(has_answer, f"{label}: missing reference answer")
        if q.get("grading") == "self":
            require(nonempty(q.get("rubric")), f"{label}: self-graded question missing rubric")
        if q.get("kind") == "choice":
            choice(q, label)
        basis = q.get("basis")
        require(basis in ("course", "paper", "general"), f"{label}: invalid basis")
        citations(q, label, mandatory=basis in ("course", "paper"), paper=basis == "paper")
        if basis == "paper":
            require(materials.get("papers") == "provided", f"{label}: paper claim without provided papers")
        counts[(mode, q.get("chapter"))] += 1
        if q.get("tier") == "core":
            question_coverage.update((mode, tid) for tid in tids)
    for topic in topics:
        if topic.get("core") is True:
            for mode in ("learn", "review"):
                require((mode, topic["id"]) in lesson_coverage, f"core topic {topic['id']}: missing {mode} lesson")
                require((mode, topic["id"]) in question_coverage, f"core topic {topic['id']}: missing {mode} core question")
    for chapter in chapters:
        require(nonempty(chapter.get("priority_reason")), f"chapter {chapter['id']}: missing priority reason")
    learn = sum(v for (mode, _), v in counts.items() if mode == "learn")
    review = sum(v for (mode, _), v in counts.items() if mode == "review")
    require(review > learn or nonempty(data.get("review_count_exception")), "review question count must exceed learn count, or document user-approved exception")
    return {"ok": not errors, "errors": errors,
            "counts": {"chapters": len(chapters), "topics": len(topics), "lessons": len(lessons),
                       "learn_questions": learn, "review_questions": review,
                       "learn_families": len(families['learn']), "review_families": len(families['review']),
                       "by_chapter": {cid: {m: counts[(m, cid)] for m in ("learn", "review")} for cid in chapter_map}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.inventory.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
