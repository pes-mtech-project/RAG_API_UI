import unittest

from api.app.config import rag_config
from api.app.services.elasticsearch_service import build_rag_filters
from api.app.services import sector_news_service


class RagFiltersTest(unittest.TestCase):
    def test_build_rag_filters_structure(self):
        filters = build_rag_filters()
        self.assertIsInstance(filters, list)

        # When filters are available, validate their structure
        if filters:
            usable_clause = next((f for f in filters if "term" in f), {})
            terms_clause = next((f for f in filters if "terms" in f), {})
            range_clause = next((f for f in filters if "range" in f), {})

            self.assertEqual(
                usable_clause.get("term", {}).get(rag_config.usable_for_rag_field), True
            )
            self.assertEqual(
                terms_clause.get("terms", {}).get(rag_config.doc_type_field),
                rag_config.allowed_doc_types_for_rag,
            )
            self.assertIn(
                rag_config.quality_score_field, range_clause.get("range", {})
            )
            self.assertGreaterEqual(
                range_clause.get("range", {})
                .get(rag_config.quality_score_field, {})
                .get("gte", 0),
                rag_config.min_quality_score_for_rag,
            )

    def test_bm25_query_includes_rag_filters(self):
        body = sector_news_service._bm25_query(
            "structured_context", ["bank"], size=5, indices="news_finbert_embeddings"
        )
        filters = body.get("query", {}).get("bool", {}).get("filter")
        self.assertIsInstance(filters, list)
        if filters:
            filter_terms = [f for f in filters if "term" in f]
            self.assertTrue(
                any(
                    clause.get("term", {}).get(rag_config.usable_for_rag_field) is True
                    for clause in filter_terms
                )
            )


if __name__ == "__main__":
    unittest.main()
