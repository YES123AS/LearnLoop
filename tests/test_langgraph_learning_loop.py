import unittest
import uuid

from langgraph.checkpoint.memory import MemorySaver

from spark.langgraph_learning_loop import (
    LearningLoopServices,
    build_learning_loop_graph,
    multi_agent_learning_loop,
)


class FakeServices:
    def __init__(self):
        self.calls = {
            "plan": 0,
            "resource": 0,
            "quiz": 0,
            "evaluate": 0,
        }

    def prepare(self, state):
        return {
            "topic": "LZW算法",
            "days": 3,
            "question_count": 1,
            "difficulty": "简单",
            "question_types": ["选择题"],
            "resource_file": "unused.md",
        }

    @staticmethod
    def _audited(name, result):
        return {
            "step": {
                "step_name": name,
                "agent_name": f"{name} Agent",
                "status": "success",
                "result": result,
                "error": None,
                "started_at": "2026-10-02 10:00:00",
                "finished_at": "2026-10-02 10:00:01",
            },
            "audit": {"passed": True, "score": 1.0},
            "audit_history": [{"passed": True, "score": 1.0}],
            "retry_count": 0,
        }

    def plan(self, state):
        self.calls["plan"] += 1
        return self._audited("规划", "三天学习计划")

    def resource(self, state):
        self.calls["resource"] += 1
        return self._audited("资料", {"resource": "课程资料"})

    def quiz(self, state):
        self.calls["quiz"] += 1
        return self._audited(
            "题目",
            {
                "questions": [
                    {
                        "id": 1,
                        "type": "选择题",
                        "knowledge_point": "LZW词典构建",
                        "question": "测试题",
                        "answer": "A",
                    }
                ]
            },
        )

    def evaluate(self, state):
        self.calls["evaluate"] += 1
        return [
            {
                "question_id": "1",
                "knowledge_point": "LZW词典构建",
                "question_type": "选择题",
                "correct": state["submitted_answers"]["1"] == "A",
            }
        ]

    def analyze(self, state):
        return {
            "step_name": "分析",
            "agent_name": "分析 Agent",
            "status": "success",
            "result": {"weak_points": [], "mastered_points": ["LZW词典构建"]},
            "error": None,
        }

    def recommend(self, state):
        return {
            "step_name": "推荐",
            "agent_name": "推荐 Agent",
            "status": "success",
            "result": "进入编码练习",
            "error": None,
        }

    def remedial(self, state):
        return {
            "step_name": "补救",
            "agent_name": "补救 Agent",
            "status": "success",
            "result": "巩固路径",
            "error": None,
        }

    @staticmethod
    def summarize(state, result):
        return f"状态：{result['status']}"

    @staticmethod
    def parse_quiz(result):
        return result if isinstance(result, dict) else {}

    @staticmethod
    def timeline_item(**kwargs):
        return {
            "order": kwargs["order"],
            "step_name": kwargs["step"]["step_name"],
            "status": "success",
        }

    def as_services(self):
        return LearningLoopServices(
            prepare=self.prepare,
            plan=self.plan,
            resource=self.resource,
            quiz=self.quiz,
            evaluate=self.evaluate,
            analyze=self.analyze,
            recommend=self.recommend,
            remedial=self.remedial,
            summarize=self.summarize,
            parse_quiz=self.parse_quiz,
            timeline_item=self.timeline_item,
        )


class LangGraphLearningLoopTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeServices()
        self.graph = build_learning_loop_graph(
            services=self.fake.as_services(),
            checkpointer=MemorySaver(),
        )
        self.profile = {"course": "多媒体信息处理", "weak_points": []}

    def test_workflow_interrupts_and_resumes_without_regeneration(self):
        workflow_id = f"test-{uuid.uuid4()}"
        waiting = multi_agent_learning_loop(
            "帮我学习LZW算法",
            self.profile,
            extra_data={"workflow_id": workflow_id},
            graph=self.graph,
        )

        self.assertEqual(waiting["status"], "waiting_for_answers")
        self.assertEqual(waiting["orchestrator"], "langgraph")
        self.assertEqual(len(waiting["quiz"]["questions"]), 1)
        self.assertEqual(self.fake.calls["plan"], 1)

        completed = multi_agent_learning_loop(
            "帮我学习LZW算法",
            self.profile,
            extra_data={
                "workflow_id": workflow_id,
                "submitted_answers": {"1": "A"},
            },
            graph=self.graph,
        )

        self.assertEqual(completed["status"], "closed_loop_completed")
        self.assertTrue(completed["answer_records"][0]["correct"])
        self.assertEqual(self.fake.calls["plan"], 1)
        self.assertEqual(self.fake.calls["resource"], 1)
        self.assertEqual(self.fake.calls["quiz"], 1)
        self.assertEqual(self.fake.calls["evaluate"], 1)

    def test_answers_can_be_supplied_on_first_run(self):
        completed = multi_agent_learning_loop(
            "帮我学习LZW算法",
            self.profile,
            extra_data={
                "workflow_id": f"test-{uuid.uuid4()}",
                "submitted_answers": {"1": "B"},
            },
            graph=self.graph,
        )

        self.assertEqual(completed["status"], "closed_loop_completed")
        self.assertFalse(completed["answer_records"][0]["correct"])
        self.assertEqual(self.fake.calls["evaluate"], 1)


if __name__ == "__main__":
    unittest.main()
