from pathlib import Path

from student_memory import (
    add_learning_record,
    create_or_update_student_profile,
    get_knowledge_mastery,
    get_learning_records,
    get_student_profile,
    init_db,
)


TEST_DB_PATH = str(Path(__file__).with_name("student_learning_test.db"))


def main():
    student_id = "S001"

    test_db = Path(TEST_DB_PATH)
    if test_db.exists():
        test_db.unlink()

    init_db(TEST_DB_PATH)

    create_or_update_student_profile(
        student_id=student_id,
        grade="大二",
        major="智能科学与技术",
        course="多媒体信息处理",
        level="基础较弱",
        goal="期末复习",
        learning_style="喜欢通俗解释和例子",
        db_path=TEST_DB_PATH,
    )

    add_learning_record(
        student_id=student_id,
        knowledge_point="LZW算法",
        question_type="选择题",
        correct=False,
        answer_time=30,
        difficulty="简单",
        db_path=TEST_DB_PATH,
    )

    add_learning_record(
        student_id=student_id,
        knowledge_point="LZW算法",
        question_type="填空题",
        correct=False,
        answer_time=45,
        difficulty="简单",
        db_path=TEST_DB_PATH,
    )

    add_learning_record(
        student_id=student_id,
        knowledge_point="LZW算法",
        question_type="简答题",
        correct=True,
        answer_time=80,
        difficulty="中等",
        db_path=TEST_DB_PATH,
    )

    profile = get_student_profile(student_id, db_path=TEST_DB_PATH)
    print("\n当前学生画像：")
    print(profile)

    mastery = get_knowledge_mastery(student_id, db_path=TEST_DB_PATH)
    print("\n知识点掌握情况：")
    for item in mastery:
        print(item)

    records = get_learning_records(student_id, db_path=TEST_DB_PATH)
    print("\n做题记录：")
    for record in records:
        print(record)


if __name__ == "__main__":
    main()
