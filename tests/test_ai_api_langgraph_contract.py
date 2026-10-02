import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from spark.ai_api import app


class LearningLoopApiContractTests(unittest.TestCase):
    def test_endpoint_preserves_langgraph_workflow_id(self):
        expected = {
            "workflow_id": "workflow-123",
            "status": "waiting_for_answers",
            "orchestrator": "langgraph",
            "quiz": {"questions": []},
        }
        with patch("spark.ai_api.multi_agent_learning_loop", return_value=expected) as run:
            response = TestClient(app).post(
                "/ai/multi_agent_learning_loop",
                json={
                    "user_input": "制定学习闭环",
                    "student_profile": {"course": "多媒体信息处理"},
                    "extra_data": {"workflow_id": "workflow-123"},
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], expected)
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["extra_data"]["workflow_id"], "workflow-123")


if __name__ == "__main__":
    unittest.main()
