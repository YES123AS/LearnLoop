from trusted_course_generator import (
    generate_trusted_answer,
    generate_trusted_resource,
    generate_trusted_quiz,
)


student_profile = {
    "grade": "大二",
    "major": "智能科学与技术",
    "course": "多媒体信息处理",
    "level": "基础较弱",
    "goal": "期末复习",
    "weak_points": ["LZW算法", "JPEG压缩"],
    "learning_style": "喜欢通俗解释和例子",
}


def test_answer():
    result = generate_trusted_answer(
        question="JPEG压缩编码的基本过程是什么？",
        student_profile=student_profile,
        top_k=6,
    )

    print("\n===== 可信问答 =====")
    print(result["answer"])
    print("\n来源：")
    for source in result["sources"]:
        print(source)
    print("\n检索检查：", result["retrieval_check"])
    print("\n依据性检查：", result["grounding_check"])


def test_resource():
    result = generate_trusted_resource(
        topic="LZW算法",
        output_file="trusted_lzw_resource.md",
        student_profile=student_profile,
        resource_type="复习资料",
        top_k=8,
    )

    print("\n===== 可信资料 =====")
    print("保存路径：", result["output_file"])
    print("检索检查：", result["retrieval_check"])
    print("依据性检查：", result["grounding_check"])


def test_quiz():
    result = generate_trusted_quiz(
        topic="LZW算法",
        student_profile=student_profile,
        question_types=["选择题", "填空题", "简答题"],
        count=5,
        difficulty="简单",
        top_k=8,
    )

    print("\n===== 可信题目 =====")
    print(result["quiz"])


if __name__ == "__main__":
    test_answer()
    test_resource()
    test_quiz()
