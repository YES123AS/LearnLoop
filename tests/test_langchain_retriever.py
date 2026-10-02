import unittest

from spark.knowledge_base.retriever import (
    LangChainKnowledgeRetriever,
    documents_to_results,
)


class FakeLegacyRetriever:
    def retrieve(self, query, top_k=5):
        return [
            {
                "id": 1,
                "file_name": "课程资料.pptx",
                "content": f"与 {query} 相关的内容",
                "score": 0.91,
            }
        ][:top_k]


class LangChainRetrieverTests(unittest.TestCase):
    def test_legacy_vector_results_are_exposed_as_documents(self):
        retriever = LangChainKnowledgeRetriever(
            legacy_retriever=FakeLegacyRetriever(),
            top_k=1,
        )

        documents = retriever.invoke("LZW")

        self.assertEqual(documents[0].page_content, "与 LZW 相关的内容")
        self.assertEqual(documents[0].metadata["score"], 0.91)
        self.assertEqual(documents_to_results(documents)[0]["file_name"], "课程资料.pptx")


if __name__ == "__main__":
    unittest.main()
