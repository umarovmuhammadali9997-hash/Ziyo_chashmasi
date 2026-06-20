import json
import os

TESTS_DIR = os.path.join(os.path.dirname(__file__), "tests")


def list_tests(subject_key):
    """Fan bo'yicha testlar ro'yxati. Har biri: {id, title, file, answers}"""
    path = os.path.join(TESTS_DIR, subject_key, "index.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_test(subject_key, test_id):
    for t in list_tests(subject_key):
        if t["id"] == test_id:
            return t
    return None


def test_pdf_path(subject_key, test):
    return os.path.join(TESTS_DIR, subject_key, test["file"])
