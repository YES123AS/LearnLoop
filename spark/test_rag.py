# test_rag.py

from knowledge_base.rag_answer import rag_answer


student_profile = {
    "grade": "大二",
    "major": "智能科学与技术",
    "course": "多媒体信息处理",
    "level": "基础较弱",
    "goal": "期末复习",
    "weak_points": ["LZW算法", "JPEG压缩"],
    "learning_style": "喜欢通俗解释和例子"
}

result = rag_answer(
    question="JPEG压缩编码的基本过程是什么？",
    student_profile=student_profile,
    top_k=5
)

print("模型回答：")
print(result["answer"])

print("\n引用资料：")
for source in result["sources"]:
    print(source["file_name"], source["score"])